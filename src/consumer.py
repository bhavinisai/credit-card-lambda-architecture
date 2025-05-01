import os
import json
import csv
import mysql.connector
from kafka import KafkaConsumer
from dotenv import load_dotenv


def is_location_close_enough(zip1, zip2):
    if not zip1 or not zip2 or len(zip1) < 5 or len(zip2) < 5:
        return False
    if zip1[:1] != zip2[:1]:
        return False
    if zip1[:2] != zip2[:2]:
        return True
    return True


# loading environment variables
load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_PORT = int(os.getenv("MYSQL_PORT"))
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "results")

# SQL connections
db = mysql.connector.connect(
    host=MYSQL_HOST,
    port=MYSQL_PORT,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DATABASE,
)
cursor = db.cursor(dictionary=True)

# creating the Kafka consumer
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda x: json.loads(x.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
)

print("Listening for messages from Kafka...")

# for csv
os.makedirs(OUTPUT_DIR, exist_ok=True)
output_file = os.path.join(OUTPUT_DIR, "stream_transactions.csv")

if not os.path.exists(output_file):
    with open(output_file, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "transaction_id",
                "card_id",
                "merchant_name",
                "timestamp",
                "amount",
                "location",
                "transaction_type",
                "related_transaction_id",
                "status",
                "pending_balance",
            ]
        )


# extracting the zip code
def extract_zip(address):
    if not address:
        return None
    parts = address.strip().split(" ")
    return parts[-1] if parts else None


# tracking balances
pending_balances = {}

# receiving messages
for message in consumer:
    tx = message.value

    card_id = tx["card_id"]
    amount = tx["amount"]
    merchant_location = tx["location"]
    transaction_type = tx["transaction_type"]
    timestamp = tx["timestamp"]
    merchant_name = tx["merchant_name"]
    transaction_id = tx["transaction_id"]
    related_transaction_id = tx.get("related_transaction_id") or ""

    # obtaining customer address and card info
    cursor.execute(
        """
        SELECT customers.address, cards.credit_limit, cards.current_balance
        FROM cards
        JOIN customers ON cards.customer_id = customers.customer_id
        WHERE cards.card_id = %s
        """,
        (card_id,),
    )
    result = cursor.fetchone()

    if not result:
        status = "declined"
        pending_balance = 0.0
        decline_reasons = ["Card not found"]
    else:
        credit_limit = float(result["credit_limit"])
        current_balance = float(result["current_balance"])
        customer_zip = extract_zip(result["address"])
        merchant_zip = extract_zip(merchant_location)

        pending_balance = pending_balances.get(card_id, current_balance)
        decline = False
        decline_reasons = []

        # Rule 1: Amount ≥ 50% of credit limit
        if abs(amount) >= 0.5 * credit_limit:
            decline = True
            decline_reasons.append("Amount exceeds 50% of credit limit")

        # Rule 2: Location check ONLY for purchases
        if transaction_type == "purchase":
            if not is_location_close_enough(customer_zip, merchant_zip):
                decline = True
                decline_reasons.append("Merchant location too far")

        # Rule 3: Pending balance exceeds credit limit
        test_pending = pending_balance
        if transaction_type in ["refund", "cancellation"]:
            test_pending -= abs(amount)
        else:
            test_pending += amount

        if test_pending > credit_limit:
            decline = True
            decline_reasons.append("Pending balance exceeds credit limit")

        # status
        status = "declined" if decline else "pending"

        # updating balance if approved
        if status == "pending":
            if transaction_type in ["refund", "cancellation"]:
                pending_balance -= abs(amount)
            else:
                pending_balance += amount

        pending_balances[card_id] = pending_balance

    if status == "declined":
        print(f"Declined transaction {transaction_id}: {', '.join(decline_reasons)}")

    # writing to CSV
    with open(output_file, mode="a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                transaction_id,
                card_id,
                merchant_name,
                timestamp,
                amount,
                merchant_location,
                transaction_type,
                related_transaction_id,
                status,
                round(pending_balance, 2),
            ]
        )
