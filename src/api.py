"""API local de leitura do último histórico exportado em Parquet."""

import logging

import duckdb
from fastapi import FastAPI, HTTPException, Query

from src.indicadores_por_minuto import ARQUIVO_PARQUET, CONSULTA


app = FastAPI(title="Smart City Data Platform", version="0.1.0")
logger = logging.getLogger(__name__)


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
):
    filtro = "WHERE sensor_id = ?" if sensor_id is not None else ""
    parametros = [sensor_id, limite] if sensor_id is not None else [limite]
    sql = f"""
        WITH indicadores AS ({CONSULTA})
        SELECT * FROM indicadores {filtro}
        ORDER BY minuto_utc DESC, sensor_id LIMIT ?
    """
    return {"fuso_horario": "UTC", "indicadores": consultar(sql, parametros)}
