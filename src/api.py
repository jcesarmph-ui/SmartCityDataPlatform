"""API local de leitura do último histórico exportado em Parquet."""

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated

import duckdb
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

from src.indicadores_por_minuto import ARQUIVO_PARQUET, CONSULTA


app = FastAPI(title="Smart City Data Platform", version="0.1.0")
logger = logging.getLogger(__name__)


@app.get("/dashboard", include_in_schema=False)
def dashboard():
    return FileResponse(Path(__file__).resolve().parent / "web" / "index.html")


def consultar(sql, parametros=()):
    if not ARQUIVO_PARQUET.exists():
        raise HTTPException(503, "Execute o pipeline para gerar o Parquet primeiro.")
    try:
        with duckdb.connect(":memory:") as banco:
            banco.execute("SET TimeZone = 'UTC'")
            banco.read_parquet(str(ARQUIVO_PARQUET)).create_view("leituras")
            resultado = banco.execute(sql, parametros)
            colunas = [coluna[0] for coluna in resultado.description]
            return [dict(zip(colunas, linha)) for linha in resultado.fetchall()]
    except (duckdb.Error, OSError):
        logger.exception("Falha na consulta ao Parquet")
        raise HTTPException(503, "Não foi possível consultar o Parquet. Verifique o pipeline.")


@app.get("/")
def inicio():
    return {
        "projeto": "Smart City Data Platform",
        "documentacao": "/docs",
        "fonte": "Última exportação Parquet; execute o pipeline para atualizar.",
    }


@app.get("/sensores")
def sensores():
    return consultar("""
        SELECT sensor_id, COUNT(*) AS leituras
        FROM leituras GROUP BY sensor_id ORDER BY sensor_id
    """)


@app.get("/indicadores")
def indicadores(
    sensor_id: str | None = None,
    limite: int = Query(default=100, ge=1, le=1000),
    minutos: Annotated[int | None, Query(ge=1, le=1440)] = None,
):
    filtro = "WHERE sensor_id = ?" if sensor_id is not None else ""
    parametros = []
    periodo = ""
    if minutos is not None:
        agora = datetime.now(timezone.utc)
        periodo = "WHERE CAST(timestamp AS TIMESTAMPTZ) BETWEEN ? AND ?"
        parametros.extend([agora - timedelta(minutes=minutos), agora])
    if sensor_id is not None:
        parametros.append(sensor_id)
    parametros.append(limite)
    consulta_periodo = CONSULTA.replace("FROM leituras", "FROM fonte")
    sql = f"""
        WITH fonte AS (SELECT * FROM leituras {periodo}),
        indicadores AS ({consulta_periodo})
        SELECT * FROM indicadores {filtro}
        ORDER BY minuto_utc DESC, sensor_id LIMIT ?
    """
    return {"fuso_horario": "UTC", "periodo_minutos": minutos, "indicadores": consultar(sql, parametros)}


@app.get("/atualizacao")
def atualizacao(sensor_id: str | None = None):
    """Idade da última leitura exportada do sensor, independente do período exibido."""
    filtro = "WHERE sensor_id = ?" if sensor_id is not None else ""
    parametros = [sensor_id] if sensor_id is not None else []
    resultado = consultar(
        f"SELECT epoch(MAX(CAST(timestamp AS TIMESTAMPTZ))) AS ultima_leitura FROM leituras {filtro}",
        parametros,
    )
    agora = datetime.now(timezone.utc)
    instante = resultado[0]["ultima_leitura"]
    ultima = datetime.fromtimestamp(instante, timezone.utc) if instante is not None else None
    idade = (agora - ultima).total_seconds() if ultima is not None else None
    if idade is None:
        estado = "sem_dados"
    elif idade < -5:
        estado = "horario_futuro"
    elif idade <= 60:
        estado = "recente"
    else:
        estado = "sem_atualizacao"
    return {
        "ultima_leitura": ultima,
        "consultado_em": agora,
        "idade_segundos": max(0, int(idade)) if idade is not None and idade >= -5 else None,
        "estado": estado,
        "limite_recente_segundos": 60,
    }
