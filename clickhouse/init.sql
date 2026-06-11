--данные от сенсоров
CREATE TABLE IF NOT EXISTS reports_db.emg_sensor_data (
                                               user_id UInt32,
                                               prosthesis_type String,
                                               muscle_group String,
                                               signal_frequency UInt32,
                                               signal_duration UInt32,
                                               signal_amplitude Decimal(5,2),
                                               signal_time DateTime
    ) ENGINE = MergeTree()
    ORDER BY (user_id, prosthesis_type, signal_time);

--копия клиентов
CREATE TABLE IF NOT EXISTS reports_db.customers_olap (
                                              id UInt32,
                                              name String,
                                              email String,
                                              age UInt8,
                                              gender String,
                                              country String,
                                              address String,
                                              phone String
    ) ENGINE = MergeTree()
    ORDER BY id;

--витрина отчёта
CREATE TABLE IF NOT EXISTS reports_db.daily_user_metrics (
                                                  user_id UInt32,
                                                  date Date,
                                                  total_signals UInt32,
                                                  avg_amplitude Decimal(10,2),
    avg_frequency Float32,
    avg_duration Float32,
    customer_name String,
    customer_email String,
    customer_country String
    ) ENGINE = MergeTree()
    ORDER BY (user_id, date);

INSERT INTO reports_db.emg_sensor_data
SELECT *
FROM file('olap.csv', 'CSV');