"""Cria uma cópia analítica do histórico e verifica sua integridade."""

from pathlib import Path
import sys
from uuid import uuid4

import duckdb


RAIZ = Path(__file__).resolve().parents[1]
ORIGEM = RAIZ / "data" / "raw" / "leituras_urbanas.jsonl"
DESTINO = RAIZ / "data" / "processed" / "leituras_urbanas.parquet"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    temporario = DESTINO.with_name(f".leituras_{uuid4().hex}.parquet")
    try:
        if not ORIGEM.exists() or ORIGEM.stat().st_size == 0:
            print("Histórico ausente ou vazio. Execute o consumidor e o simulador primeiro.")
            raise SystemExit(1)

        DESTINO.parent.mkdir(parents=True, exist_ok=True)
        with duckdb.connect(":memory:") as banco:
            # Materializa uma única leitura: a validação usa o mesmo conjunto exportado.
            banco.read_json(str(ORIGEM), format="newline_delimited").create("historico")
            quantidade = banco.sql("SELECT COUNT(*) FROM historico").fetchone()[0]
            if quantidade == 0:
                print("Histórico sem registros. Nenhum arquivo foi exportado.")
                raise SystemExit(1)
            banco.table("historico").write_parquet(str(temporario), compression="snappy")
            banco.read_parquet(str(temporario)).create_view("exportado")
            quantidade_exportada = banco.sql("SELECT COUNT(*) FROM exportado").fetchone()[0]
            diferencas = banco.sql("""
                SELECT COUNT(*) FROM (
                    (SELECT * FROM historico EXCEPT ALL SELECT * FROM exportado)
                    UNION ALL
                    (SELECT * FROM exportado EXCEPT ALL SELECT * FROM historico)
                )
            """).fetchone()[0]
            if quantidade != quantidade_exportada or diferencas:
                raise ValueError("A conferência dos registros exportados falhou.")

            print("=== AMOSTRA DO PARQUET ===")
            banco.sql("SELECT * FROM exportado LIMIT 5").show()

        # Só substitui a exportação anterior depois da validação e fechamento do banco.
        temporario.replace(DESTINO)
        print(f"Registros na origem: {quantidade}")
        print(f"Registros no Parquet: {quantidade_exportada}")
        print("Validação: todos os registros preservados, incluindo duplicatas.")
        print(f"Arquivo: {DESTINO}")
        print("Execute novamente para atualizar a cópia com todo o histórico disponível.")
    except (duckdb.Error, OSError, ValueError) as erro:
        print(f"Falha na exportação: {erro}")
        raise SystemExit(1)
    finally:
        if temporario.exists():
            temporario.unlink()


if __name__ == "__main__":
    main()
