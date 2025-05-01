import os
import json
import time
import decimal
import mysql.connector
from kafka import KafkaProducer
from dotenv import load_dotenv

# loading environment variables
load_dotenv()

# SQL and Kafka configurations
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT"))
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")

# SQL database connections
db_connection = mysql.connector.connect(
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DATABASE,
)
cursor = db_connection.cursor(dictionary=True)

# creating kafka producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)
print("Sending transactions to Kafka...")

# for obtaining the transactions
query = """
    SELECT * FROM transactions
    WHERE DATE(timestamp) BETWEEN '2025-04-01' AND '2025-04-04'
    ORDER BY timestamp ASC
"""
cursor.execute(query)
transactions = cursor.fetchall()

# sending transactions to Kafka
for transaction in transactions:
    if isinstance(transaction["timestamp"], (str, bytes)):
        pass
    else:
        transaction["timestamp"] = transaction["timestamp"].strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    for key, value in transaction.items():
        if isinstance(value, decimal.Decimal):
            transaction[key] = float(value)

    producer.send(KAFKA_TOPIC, value=transaction)
    print(f"Sent transaction_id={transaction['transaction_id']} to Kafka.")
    time.sleep(0.1)  #

cursor.close()
db_connection.close()
producer.flush()
producer.close()

print("All transactions were sent successfully.")
