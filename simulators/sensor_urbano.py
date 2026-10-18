import json
import random
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "smartcity/sensores/urbanos"
SENSORES = (
    {"sensor_id": "URB-001", "local": "Centro", "velocidade": (10, 35), "fluxo": (50, 100)},
    {"sensor_id": "URB-002", "local": "Bairro residencial", "velocidade": (20, 45), "fluxo": (5, 30)},
    {"sensor_id": "URB-003", "local": "Avenida principal", "velocidade": (35, 65), "fluxo": (30, 80)},
)


def gerar_dados(sensor=None):
    if sensor is None:
        sensor = SENSORES[0]
    return {
        "sensor_id": sensor["sensor_id"],
        "cidade": "Cidade Simulada",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "temperatura_c": round(random.uniform(18, 35), 2),
        "umidade_percentual": round(random.uniform(35, 90), 2),
        "pm25_ug_m3": round(random.uniform(5, 80), 2),
        "velocidade_media_kmh": round(random.uniform(*sensor["velocidade"]), 2),
        "veiculos_por_minuto": random.randint(*sensor["fluxo"]),
    }


def main():
    client = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="smartcity-simulador",
    )

    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()

    print("Simulador urbano iniciado.")
    print(f"Publicando em: {MQTT_TOPIC}")
    for sensor in SENSORES:
        print(f"{sensor['sensor_id']}: {sensor['local']}")
    print("Pressione Ctrl+C para encerrar.\n")

    try:
        while True:
            for sensor in SENSORES:
                dados = gerar_dados(sensor)
                mensagem = json.dumps(dados, ensure_ascii=False)

                resultado = client.publish(
                    MQTT_TOPIC,
                    mensagem,
                    qos=1,
                )
                resultado.wait_for_publish()

                if resultado.rc != mqtt.MQTT_ERR_SUCCESS:
                    print(f"Falha na publicação: {resultado.rc}")
                else:
                    print(f"[ENVIADO] {mensagem}")

            time.sleep(3)

    except KeyboardInterrupt:
        print("\nSimulação encerrada.")

    finally:
        client.disconnect()
        client.loop_stop()


if __name__ == "__main__":
    main()
