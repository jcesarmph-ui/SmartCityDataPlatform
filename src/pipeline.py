"""Executa exportação e indicadores uma vez ou em ciclos periódicos."""

import argparse
from pathlib import Path
import subprocess
import sys
import time


ETAPAS = (
    ("Atualizar e validar o Parquet", "exportar_parquet.py"),
    ("Calcular indicadores por minuto", "indicadores_por_minuto.py"),
)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intervalo", type=int, help="Segundos de espera entre ciclos (mínimo: 3).")
    args = parser.parse_args()
    if args.intervalo is not None and args.intervalo < 3:
        parser.error("--intervalo deve ser pelo menos 3 segundos")
    pasta = Path(__file__).resolve().parent
    try:
        while True:
            for numero, (descricao, script) in enumerate(ETAPAS, start=1):
                print(f"\n[{numero}/{len(ETAPAS)}] {descricao}", flush=True)
                subprocess.run([sys.executable, str(pasta / script)], check=True)
            print("\nPipeline concluído com sucesso.", flush=True)
            if args.intervalo is None:
                break
            print(f"Próximo ciclo após {args.intervalo}s de espera. Ctrl+C para encerrar.", flush=True)
            time.sleep(args.intervalo)
    except subprocess.CalledProcessError:
        print("\nPipeline interrompido: corrija o erro mostrado acima e execute novamente.")
        raise SystemExit(1)
    except KeyboardInterrupt:
        print("\nPipeline interrompido pelo usuário.")
        raise SystemExit(130)


if __name__ == "__main__":
    main()
