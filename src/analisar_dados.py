"""Exibe indicadores do histórico local de sensores urbanos."""

import json
import math
from pathlib import Path


ARQUIVO_DADOS = Path(__file__).resolve().parents[1] / "data" / "raw" / "leituras_urbanas.jsonl"
METRICAS = {
    "temperatura_c": ("Temperatura", "°C"),
    "umidade_percentual": ("Umidade", "%"),
    "pm25_ug_m3": ("PM2.5", "µg/m³"),
    "velocidade_media_kmh": ("Velocidade média", "km/h"),
    "veiculos_por_minuto": ("Fluxo de veículos", "veículos/min"),
}


def main():
    totais = {campo: 0.0 for campo in METRICAS}
    sensores = set()
    quantidade = 0
    invalidas = 0

    try:
        with ARQUIVO_DADOS.open(encoding="utf-8") as arquivo:
            for linha in arquivo:
                if not linha.strip():
                    continue
                try:
                    dados = json.loads(linha)
                    if not isinstance(dados, dict):
                        raise ValueError("A leitura deve ser um objeto JSON")
                    sensor = dados["sensor_id"]
                    if not isinstance(sensor, str) or not sensor.strip():
                        raise ValueError("Sensor inválido")
                    valores = [dados[campo] for campo in METRICAS]
                    if any(
                        isinstance(valor, bool)
                        or not isinstance(valor, (int, float))
                        or not math.isfinite(valor)
                        for valor in valores
                    ):
                        raise ValueError("Métrica inválida")
                except (json.JSONDecodeError, KeyError, ValueError):
                    invalidas += 1
                    continue

                for campo, valor in zip(METRICAS, valores):
                    totais[campo] += valor
                sensores.add(sensor)
                quantidade += 1
    except FileNotFoundError:
        print("Histórico não encontrado. Execute o consumidor e o simulador primeiro.")
        return
    except OSError as erro:
        print(f"Não foi possível ler o histórico: {erro}")
        return

    print("=== INDICADORES DA CIDADE SIMULADA ===")
    print(f"Leituras válidas: {quantidade}")
    print(f"Leituras inválidas ignoradas: {invalidas}")
    print(f"Sensores distintos: {len(sensores)}")
    if not quantidade:
        print("Ainda não há leituras válidas para calcular médias.")
        return

    print("\nMédias de todo o histórico:")
    for campo, (rotulo, unidade) in METRICAS.items():
        print(f"{rotulo}: {totais[campo] / quantidade:.2f} {unidade}")
    print("\nDados simulados; cada execução consulta o arquivo novamente.")


if __name__ == "__main__":
    main()
