
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

Antes de salvar, o consumidor valida os campos obrigatórios, números finitos,
umidade entre 0 e 100%, PM2.5 e velocidade não negativos, fluxo inteiro não
negativo e data ISO 8601 com fuso horário. Datas válidas são normalizadas em
UTC. Leituras inválidas exibem `[RECUSADA]` no terminal e não são gravadas;
o consumidor segue recebendo mensagens. As regras de integridade ficam em
`src/validacao_dados.py` e não são as faixas de cores do dashboard: uma
medição fora da faixa boa pode ser válida e deve continuar sendo analisada.
O histórico já salvo é preservado, sem revisão retroativa nesta etapa.

Para executar os testes de validação:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

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

### Dashboard local

Com a API em execução, abra http://127.0.0.1:8000/dashboard.
A página oferece filtro por sensor, médias, gráfico de temperatura e tabela
por minuto UTC, com até 1.000 grupos mais recentes. Os cartões usam médias
ponderadas pela quantidade de leituras de cada grupo (aproximadas, pois os
grupos já estão arredondados). Clique em **Atualizar consulta** após executar
o pipeline para consultar a nova exportação. A opção **Atualizar consulta
automaticamente a cada 10 segundos** repete as consultas enquanto a página
estiver aberta. Ela começa desligada e pode ser desmarcada a qualquer momento.

O filtro **Período** permite selecionar todo o histórico, últimos 15 minutos,
última hora ou últimas 24 horas. As janelas são relativas ao horário atual
do servidor e aplicadas às leituras antes de calcular médias e agrupamentos.
Dados antigos podem não aparecer nas janelas recentes; selecione todo o
histórico para consultá-los. A API aceita o parâmetro opcional `minutos`
entre 1 e 1440 em `/indicadores`.

A seção **Atualidade dos dados** mostra a última leitura exportada do sensor
selecionado (ou a mais recente entre todos), independentemente do filtro de
período. Até 60 segundos significa dados recentes; acima disso, dados sem
atualização. Ausência de leituras e horários futuros têm avisos específicos.
O horário é exibido em São Paulo, e a idade corresponde ao instante da
consulta. A rota `/atualizacao` aceita `sensor_id` opcional. Esse indicador
mede a atualidade do Parquet, não confirma a saúde dos serviços MQTT.

Os cartões exibem cores e rótulos Bom (verde), Ameno / atenção (amarelo)
e Ruim (vermelho). A seção abaixo dos cartões detalha os intervalos por
indicador. As faixas são ilustrativas do projeto, sem equivalência com
limites oficiais de saúde ou trânsito. Na velocidade, representam apenas
fluidez simulada. Os critérios ficam em `src/web/index.html`, em `criterios`.
Sem dados, os cartões permanecem neutros.

Para gerar novas leituras continuamente, mantenha Mosquitto, consumidor
e simulador ativos. Cada ciclo do simulador envia uma leitura de cada sensor
e aguarda três segundos. Em um terminal separado, execute o pipeline para
atualizar o Parquet e clique em **Atualizar consulta** no dashboard.

Para atualizar continuamente o Parquet, em vez do pipeline de execução única:

```powershell
.\.venv\Scripts\python.exe src\pipeline.py --intervalo 10
```

O comando executa um ciclo completo, espera dez segundos e repete, sem
sobrepor ciclos. Em caso de erro, interrompe e exibe a falha. Ctrl+C encerra
o processo. O simulador, o consumidor e a API devem continuar ativos em
terminais separados. No dashboard, marque a consulta automática para
acompanhar as novas exportações. Há atraso de coleta, processamento e
consulta: a atualização é periódica, não instantânea.

## Atualizar a análise local

Com leituras já salvas em `data/raw/leituras_urbanas.jsonl`, execute no PowerShell,
a partir da pasta do projeto:

```powershell
.\.venv\Scripts\python.exe src\pipeline.py
```

O comando exporta e valida o histórico em `data/processed/leituras_urbanas.parquet`
e exibe indicadores por sensor e minuto UTC. Cada execução atualiza a cópia
Parquet completa; o JSONL original é preservado. Se uma etapa falhar, o fluxo para.
Sem `--intervalo`, o comando executa uma vez. Ele não inicia a coleta MQTT.

Parquet é o formato de armazenamento por colunas usado na cópia analítica.
DuckDB é o banco analítico executado dentro do Python para ler os arquivos,
exportar Parquet e calcular indicadores com SQL. Neste projeto, suas tabelas
de trabalho ficam em memória; os arquivos JSONL e Parquet permanecem no disco.

## Status

Implementado: simulação de três sensores, MQTT local, histórico JSONL,
consultas SQL com DuckDB, exportação Parquet validada, indicadores por
minuto, pipeline manual, API FastAPI e dashboard local integrado.

Próximas etapas: integração com Google AI Studio e evolução da integração
e orquestração de dados.
