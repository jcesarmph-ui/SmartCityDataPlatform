import json
from pathlib import Path

import paho.mqtt.client as mqtt

if __package__:
    from .validacao_dados import validar_leitura
else:
    from validacao_dados import validar_leitura

MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "smartcity/sensores/urbanos"
ARQUIVO_DADOS = Path(__file__).resolve().parents[1] / "data" / "raw" / "leituras_urbanas.jsonl"


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("Conectado ao broker MQTT.")
        client.subscribe(MQTT_TOPIC, qos=1)
        print(f"Inscrito no tópico: {MQTT_TOPIC}\n")
    else:
        print(f"Falha na conexão: {reason_code}")


def on_message(client, userdata, msg):
    try:
        dados = validar_leitura(json.loads(msg.payload.decode("utf-8")))

        print("\n--- NOVA LEITURA URBANA ---")
        print(f"Sensor: {dados['sensor_id']}")
        print(f"Temperatura: {dados['temperatura_c']} °C")
        print(f"Umidade: {dados['umidade_percentual']}%")
        print(f"PM2.5: {dados['pm25_ug_m3']} µg/m³")
        print(f"Velocidade média: {dados['velocidade_media_kmh']} km/h")
        print(f"Veículos/minuto: {dados['veiculos_por_minuto']}")
        print(f"Horário: {dados['timestamp']}")

        ARQUIVO_DADOS.parent.mkdir(parents=True, exist_ok=True)
        with ARQUIVO_DADOS.open("a", encoding="utf-8") as arquivo:
            arquivo.write(json.dumps(dados, ensure_ascii=False, allow_nan=False) + "\n")
        print(f"Leitura salva em: {ARQUIVO_DADOS}")

    except (UnicodeDecodeError, ValueError) as erro:
        print(f"[RECUSADA] Mensagem inválida: {erro}")
    except OSError as erro:
        print(f"Falha ao salvar leitura: {erro}")


def main():
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="smartcity-consumidor",
    )

    client.on_connect = on_connect
    client.on_message = on_message

    print("Aguardando mensagens MQTT...")

    try:
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        client.loop_forever()

    except KeyboardInterrupt:
        print("\nConsumidor encerrado.")

    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
