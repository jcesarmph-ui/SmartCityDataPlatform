
from datetime import datetime, timezone


def main():
    print("=" * 55)
    print("SMART CITY DATA PLATFORM")
    print("=" * 55)
    print("Status: ambiente inicial configurado")
    print("Projeto: plataforma de dados urbanos")
    print(f"Horário UTC: {datetime.now(timezone.utc).isoformat()}")
    print("Hardware físico: não necessário")
    print("=" * 55)


if __name__ == "__main__":
    main()
