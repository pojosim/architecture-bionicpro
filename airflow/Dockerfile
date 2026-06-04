FROM apache/airflow:2.9.1-python3.9

RUN pip install --no-cache-dir \
    clickhouse-driver==0.2.6 \
    psycopg2-binary==2.9.9 \
    pandas==2.0.3

USER root
