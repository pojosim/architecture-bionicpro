from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.hooks.base import BaseHook
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from clickhouse_driver import Client

default_args = {
    'owner': 'bionic',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

def get_clickhouse_client():
    conn = BaseHook.get_connection('clickhouse_default')
    return Client(
        host=conn.host,
        port=conn.port,
        user=conn.login,
        password=conn.password,
        database=conn.schema
    )

def extract_crm_to_clickhouse():
    pg_hook = PostgresHook(postgres_conn_id='crm_postgres')
    df = pg_hook.get_pandas_df('SELECT * FROM customers')

    ch_client = get_clickhouse_client()
    ch_client.execute('TRUNCATE TABLE customers_olap')

    def esc(s):
        if isinstance(s, str):
            return s.replace("'", "''")
        return s

    for _, row in df.iterrows():
        # Экранируем строковые поля
        name = esc(row['name'])
        email = esc(row['email'])
        gender = esc(row['gender'])
        country = esc(row['country'])
        address = esc(row['address'])
        phone = esc(row['phone'])

        sql = f"""
            INSERT INTO customers_olap (id, name, email, age, gender, country, address, phone)
            VALUES ({row['id']}, '{name}', '{email}', {row['age']}, '{gender}', '{country}', '{address}', '{phone}')
        """
        ch_client.execute(sql)

def rebuild_aggregate_table():
    ch_client = get_clickhouse_client()

    ch_client.execute('TRUNCATE TABLE daily_user_metrics')

    sql = """
          INSERT INTO daily_user_metrics
          SELECT
              t.user_id,
              toDate(t.signal_time) as date,
            count() as total_signals,
            avg(toFloat32(t.signal_amplitude)) as avg_amplitude,
            avg(t.signal_frequency) as avg_frequency,
            avg(t.signal_duration) as avg_duration,
            c.name as customer_name,
            c.email as customer_email,
            c.country as customer_country
          FROM emg_sensor_data t
              LEFT JOIN customers_olap c ON t.user_id = c.id
          WHERE toDate(t.signal_time) >= today() - 30
          GROUP BY t.user_id, date, c.name, c.email, c.country \
          """
    ch_client.execute(sql)

with DAG(
        'bionic_crm_etl',
        default_args=default_args,
        description='ETL from CRM to ClickHouse and rebuild metrics',
        schedule_interval='0 * * * *',
        catchup=False,
) as dag:
    start = DummyOperator(task_id='start')
    extract = PythonOperator(
        task_id='extract_crm_to_clickhouse',
        python_callable=extract_crm_to_clickhouse
    )
    rebuild = PythonOperator(
        task_id='rebuild_aggregate_table',
        python_callable=rebuild_aggregate_table
    )
    end = DummyOperator(task_id='end')

    start >> extract >> rebuild >> end