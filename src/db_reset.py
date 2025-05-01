import csv
import mysql.connector


def reset_tables_from_csv():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="yourpassword",
        database="credit_card_system",
    )
    cursor = conn.cursor()

    # Truncate first
    cursor.execute("TRUNCATE TABLE cards")
    cursor.execute("TRUNCATE TABLE customers")

    # Reload cards
    with open("dataset/cards.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute(
                """
                INSERT INTO cards (card_id, customer_id, card_type_id, card_number, expiration_date, credit_limit, current_balance, issue_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
                (
                    int(row["card_id"]),
                    int(row["customer_id"]),
                    int(row["card_type_id"]),
                    row["card_number"],
                    row["expiration_date"],
                    float(row["credit_limit"]),
                    float(row["current_balance"]),
                    row["issue_date"],
                ),
            )

    # reloading customers
    with open("dataset/customers.csv") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute(
                """
                INSERT INTO customers (customer_id, name, phone_number, address, email, credit_score, annual_income)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
                (
                    int(row["customer_id"]),
                    row["name"],
                    row["phone_number"],
                    row["address"],
                    row["email"],
                    int(row["credit_score"]),
                    float(row["annual_income"]),
                ),
            )

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Reset complete: cards and customers restored to original state.")


reset_tables_from_csv()
