"""Executa exportação e indicadores em sequência, uma vez por comando."""

from pathlib import Path
import subprocess
import sys


ETAPAS = (
    ("Atualizar e validar o Parquet", "exportar_parquet.py"),
    ("Calcular indicadores por minuto", "indicadores_por_minuto.py"),
)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    pasta = Path(__file__).resolve().parent
    try:
        for numero, (descricao, script) in enumerate(ETAPAS, start=1):
            print(f"\n[{numero}/{len(ETAPAS)}] {descricao}", flush=True)
            subprocess.run([sys.executable, str(pasta / script)], check=True)
    except subprocess.CalledProcessError:
        print("\nPipeline interrompido: corrija o erro mostrado acima e execute novamente.")
        raise SystemExit(1)
    except KeyboardInterrupt:
        print("\nPipeline interrompido pelo usuário.")
        raise SystemExit(130)
    print("\nPipeline concluído com sucesso.")


if __name__ == "__main__":
    main()
