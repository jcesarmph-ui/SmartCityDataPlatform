"""Consulta o histórico JSONL com SQL, sem modificar os dados originais."""

from pathlib import Path
import sys

import duckdb


ARQUIVO_DADOS = Path(__file__).resolve().parents[1] / "data" / "raw" / "leituras_urbanas.jsonl"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not ARQUIVO_DADOS.exists() or ARQUIVO_DADOS.stat().st_size == 0:
        print("Histórico ausente ou vazio. Execute o consumidor e o simulador primeiro.")
        return

    try:
        with duckdb.connect(":memory:") as banco:
            banco.read_json(str(ARQUIVO_DADOS), format="newline_delimited").create_view("leituras")

            print("=== RESUMO POR SENSOR ===")
            banco.sql("""
                SELECT
                    sensor_id,
                    COUNT(*) AS leituras,
                    ROUND(AVG(temperatura_c), 2) AS temperatura_media_c,
                    ROUND(AVG(umidade_percentual), 2) AS umidade_media_pct,
                    ROUND(AVG(pm25_ug_m3), 2) AS pm25_medio_ug_m3,
                    ROUND(AVG(velocidade_media_kmh), 2) AS velocidade_media_kmh,
                    ROUND(AVG(veiculos_por_minuto), 2) AS fluxo_medio_veiculos_min
                FROM leituras
                GROUP BY sensor_id
                ORDER BY sensor_id
            """).show()

            print("\n=== 5 LEITURAS MAIS RECENTES (HORÁRIO UTC) ===")
            banco.sql("""
                SELECT sensor_id, timestamp, temperatura_c,
                       pm25_ug_m3, velocidade_media_kmh
                FROM leituras
                ORDER BY CAST(timestamp AS TIMESTAMPTZ) DESC
                LIMIT 10
            """).show()
    except (duckdb.Error, OSError) as erro:
        print(f"Não foi possível consultar o histórico: {erro}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
