
# Smart City Data Platform

Plataforma de dados urbanos para simulação, integração,
processamento e análise de informações de cidades inteligentes.

## Objetivos

- Simular dados de mobilidade urbana e meio ambiente.
- Implementar comunicação com MQTT.
- Explorar streaming de eventos com Apache Kafka.
- Integrar bancos SQL e NoSQL.
- Processar dados com Apache Spark.
- Armazenar dados analíticos em Parquet.
- Consultar dados com DuckDB.
- Automatizar pipelines com Apache Airflow.
- Desenvolver um dashboard com Google AI Studio.

## Tecnologias

Python, MQTT, Mosquitto, Apache Kafka, MongoDB,
PostgreSQL, PostGIS, Apache Spark, Parquet, DuckDB,
Apache Airflow, FastAPI e Google AI Studio.

## Execução

O projeto será desenvolvido por etapas, com execução local
e dados simulados, sem necessidade de hardware físico.

### Preparar e iniciar

Requisitos: Python 3.10 ou superior e Docker Desktop em execução.
Na pasta do projeto, usando PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
docker compose up -d
```

Em um terminal, inicie o consumidor:

```powershell
.\.venv\Scripts\python.exe src\mqtt_consumer.py
```

Em outro terminal, inicie o simulador:

```powershell
.\.venv\Scripts\python.exe simulators\sensor_urbano.py
```

O simulador publica leituras de três pontos: URB-001 (Centro), URB-002
(Bairro residencial) e URB-003 (Avenida principal). O consumidor grava
as leituras em `data/raw/leituras_urbanas.jsonl`.

Para encerrar o dia, pressione Ctrl+C nos terminais do simulador, consumidor
e API. Depois execute `docker compose down`. Os arquivos de dados permanecem
no computador. Dados gerados, `.env` e `.venv` são ignorados pelo Git.

## API local

Depois de executar o pipeline, inicie a API na pasta do projeto:

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.api:app --host 127.0.0.1 --port 8000
```

Abra http://127.0.0.1:8000/docs para testar `GET /sensores` e
`GET /indicadores`. Os indicadores aceitam `sensor_id` opcional e `limite`
entre 1 e 1000. Horários em UTC. As consultas leem a última exportação
Parquet; execute o pipeline novamente para incluir novas leituras.
Para encerrar a API, pressione Ctrl+C no terminal.

## Atualizar a análise local

Com leituras já salvas em `data/raw/leituras_urbanas.jsonl`, execute no PowerShell,
a partir da pasta do projeto:

```powershell
.\.venv\Scripts\python.exe src\pipeline.py
```

O comando exporta e valida o histórico em `data/processed/leituras_urbanas.parquet`
e exibe indicadores por sensor e minuto UTC. Cada execução atualiza a cópia
Parquet completa; o JSONL original é preservado. Se uma etapa falhar, o fluxo para.
O comando executa uma vez; não agenda atualizações nem inicia a coleta MQTT.

Parquet é o formato de armazenamento por colunas usado na cópia analítica.
DuckDB é o banco analítico executado dentro do Python para ler os arquivos,
exportar Parquet e calcular indicadores com SQL. Neste projeto, suas tabelas
de trabalho ficam em memória; os arquivos JSONL e Parquet permanecem no disco.

## Status

Implementado: simulação de três sensores, MQTT local, histórico JSONL,
consultas SQL com DuckDB, exportação Parquet validada, indicadores por
minuto, pipeline manual e API FastAPI.

Próximas etapas: dashboard e evolução da integração e orquestração de dados.
