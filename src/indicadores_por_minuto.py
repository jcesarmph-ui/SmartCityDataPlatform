"""Consulta o Parquet e agrupa leituras por sensor e minuto UTC."""

from pathlib import Path
import sys

import duckdb


ARQUIVO_PARQUET = (
    Path(__file__).resolve().parents[1]
    / "data" / "processed" / "leituras_urbanas.parquet"
)

CONSULTA = """
    SELECT
        sensor_id,
        date_trunc('minute', CAST(timestamp AS TIMESTAMP)) AS minuto_utc,
        COUNT(*) AS leituras,
        ROUND(AVG(temperatura_c), 2) AS temperatura_media_c,
        ROUND(AVG(umidade_percentual), 2) AS umidade_media_pct,
        ROUND(AVG(pm25_ug_m3), 2) AS pm25_medio_ug_m3,
        ROUND(AVG(velocidade_media_kmh), 2) AS velocidade_media_kmh,
        ROUND(AVG(veiculos_por_minuto), 2) AS fluxo_medio_veiculos_min
    FROM leituras
    GROUP BY sensor_id, minuto_utc
    ORDER BY minuto_utc, sensor_id
"""


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        if not ARQUIVO_PARQUET.exists():
            print("Parquet não encontrado. Execute src/exportar_parquet.py primeiro.")
            return

        with duckdb.connect(":memory:") as banco:
            banco.execute("SET TimeZone = 'UTC'")
            banco.read_parquet(str(ARQUIVO_PARQUET)).create_view("leituras")
            banco.sql(CONSULTA).create("indicadores")
            total = banco.sql("SELECT COUNT(*) FROM leituras").fetchone()[0]
            grupos, agrupadas = banco.sql(
                "SELECT COUNT(*), COALESCE(SUM(leituras), 0) FROM indicadores"
            ).fetchone()
            if total != agrupadas:
                raise ValueError("A contagem agrupada diverge da origem.")

            print("=== INDICADORES POR SENSOR E MINUTO (UTC) ===")
            banco.sql("SELECT * FROM indicadores ORDER BY minuto_utc DESC, sensor_id").show(
                max_rows=20, max_width=220
            )
            print(f"Leituras no Parquet: {total}")
            print(f"Grupos de sensor/minuto: {grupos}")
            print(f"Leituras contabilizadas nos grupos: {agrupadas}")
            print("Fluxo é a média das estimativas de veículos/min, não a soma de veículos.")
            print("Minutos sem leituras não aparecem; minutos parciais usam as amostras disponíveis.")
            print("Para incluir novas leituras, execute a exportação Parquet novamente.")
    except (duckdb.Error, OSError, ValueError) as erro:
        print(f"Falha ao calcular indicadores: {erro}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
