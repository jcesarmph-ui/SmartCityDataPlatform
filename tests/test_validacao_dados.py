import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from simulators.sensor_urbano import SENSORES, gerar_dados
from src import mqtt_consumer
from src.validacao_dados import validar_leitura


class ValidacaoTest(unittest.TestCase):
    def test_simulador_compativel(self):
        for sensor in SENSORES:
            dados = gerar_dados(sensor)
            self.assertEqual(validar_leitura(dados), dados)

    def test_normaliza_horario_sem_alterar_original(self):
        dados = gerar_dados()
        dados["timestamp"] = "2026-10-20T12:00:00-03:00"
        self.assertEqual(validar_leitura(dados)["timestamp"], "2026-10-20T15:00:00+00:00")
        self.assertEqual(dados["timestamp"], "2026-10-20T12:00:00-03:00")

    def test_invalida_campos(self):
        casos = [
            ("sensor_id", ""), ("timestamp", "ontem"),
            ("timestamp", "2026-10-20T12:00:00"), ("timestamp", None),
            ("timestamp", "0001-01-01T00:00:00+01:00"),
            ("temperatura_c", float("nan")), ("temperatura_c", float("inf")),
            ("temperatura_c", 10**400), ("umidade_percentual", True),
            ("umidade_percentual", 101), ("umidade_percentual", -1),
            ("pm25_ug_m3", -1), ("velocidade_media_kmh", -1),
            ("veiculos_por_minuto", 1.5), ("veiculos_por_minuto", -1),
            ("cidade", []), ("temperatura_c", "25"),
        ]
        for campo, valor in casos:
            with self.subTest(campo=campo, valor=valor):
                with self.assertRaises(ValueError):
                    validar_leitura({**gerar_dados(), campo: valor})

    def test_campos_ausentes_e_formato(self):
        for dados in ([], None, "texto", {}):
            with self.assertRaises(ValueError):
                validar_leitura(dados)
        base = gerar_dados()
        for campo in ("sensor_id", "timestamp", "temperatura_c", "umidade_percentual",
                      "pm25_ug_m3", "velocidade_media_kmh", "veiculos_por_minuto"):
            with self.assertRaises(ValueError):
                validar_leitura({k: v for k, v in base.items() if k != campo})

    def test_limites_validos(self):
        for umidade in (0, 100):
            validar_leitura({**gerar_dados(), "umidade_percentual": umidade,
                             "temperatura_c": -10, "pm25_ug_m3": 0,
                             "velocidade_media_kmh": 0, "veiculos_por_minuto": 0})

    def test_consumidor_recusa_e_continua(self):
        destino = MagicMock()
        validos = gerar_dados()
        mensagens = [b"{", b"\xff", b"[]", json.dumps({**validos, "umidade_percentual": 110}).encode()]
        with patch.object(mqtt_consumer, "ARQUIVO_DADOS", destino), patch("builtins.print"):
            for payload in mensagens:
                mqtt_consumer.on_message(None, None, SimpleNamespace(payload=payload))
            destino.open.assert_not_called()
            mqtt_consumer.on_message(None, None, SimpleNamespace(payload=json.dumps(validos).encode()))
            destino.open.assert_called_once_with("a", encoding="utf-8")
            escrita = destino.open.return_value.__enter__.return_value.write.call_args.args[0]
            self.assertEqual(json.loads(escrita), validos)


if __name__ == "__main__":
    unittest.main()
