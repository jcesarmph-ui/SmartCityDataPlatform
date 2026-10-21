"""Regras de integridade das leituras, independentes das faixas visuais do painel."""

from datetime import datetime, timezone
import math


METRICAS = (
    "temperatura_c", "umidade_percentual", "pm25_ug_m3",
    "velocidade_media_kmh", "veiculos_por_minuto",
)


def validar_leitura(dados):
    """Valida sem alterar os dados. Retorna cópia com horário normalizado em UTC."""
    if not isinstance(dados, dict):
        raise ValueError("A leitura deve ser um objeto JSON.")
    for campo in ("sensor_id", "timestamp", *METRICAS):
        if campo not in dados:
            raise ValueError(f"Campo obrigatório ausente: {campo}.")
    if not isinstance(dados["sensor_id"], str) or not dados["sensor_id"].strip():
        raise ValueError("sensor_id deve ser um texto não vazio.")
    if "cidade" in dados and (not isinstance(dados["cidade"], str) or not dados["cidade"].strip()):
        raise ValueError("cidade deve ser um texto não vazio, quando informada.")
    for campo in METRICAS:
        valor = dados[campo]
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise ValueError(f"{campo} deve ser um número.")
        try:
            finito = math.isfinite(valor)
        except OverflowError:
            finito = False
        if not finito:
            raise ValueError(f"{campo} deve ser um número finito.")
    if not 0 <= dados["umidade_percentual"] <= 100:
        raise ValueError("umidade_percentual deve estar entre 0 e 100.")
    for campo in ("pm25_ug_m3", "velocidade_media_kmh", "veiculos_por_minuto"):
        if dados[campo] < 0:
            raise ValueError(f"{campo} não pode ser negativo.")
    if not isinstance(dados["veiculos_por_minuto"], int):
        raise ValueError("veiculos_por_minuto deve ser inteiro.")
    try:
        if not isinstance(dados["timestamp"], str):
            raise ValueError
        horario = datetime.fromisoformat(dados["timestamp"].replace("Z", "+00:00"))
        if horario.utcoffset() is None:
            raise ValueError
        normalizado = horario.astimezone(timezone.utc).isoformat()
    except (ValueError, OverflowError):
        raise ValueError("timestamp deve ser uma data ISO 8601 com fuso horário.") from None
    return {**dados, "timestamp": normalizado}
