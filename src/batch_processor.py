import os
import csv
from helper import calculate_credit_score_adjustment, calculate_new_credit_limit


class BatchProcessor:
    def __init__(self):
        os.makedirs("results", exist_ok=True)

    # approving pending transactions
    def approve_pending_transactions(self, stream_file, batch_file):
        approved_txns = []
        declined_txns = []

        with open(stream_file, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["status"].strip().lower() == "pending":
                    row["status"] = "approved"
                    approved_txns.append(row)
                elif row["status"].strip().lower() == "declined":
                    declined_txns.append(row)

        if approved_txns:
            with open(batch_file, mode="w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=approved_txns[0].keys())
                writer.writeheader()
                writer.writerows(approved_txns)
            print(f"Saved {len(approved_txns)} approved transactions to {batch_file}")
        else:
            print("There are no approved transactions to write.")

    # updating card balances
    def update_card_balances(self, cards_file, batch_file, output_file):
        with open(cards_file, newline="") as f:
            cards = list(csv.DictReader(f))

        for card in cards:
            card["card_id"] = int(card["card_id"])
            card["current_balance"] = float(card["current_balance"])

        with open(batch_file, newline="") as f:
            transactions = list(csv.DictReader(f))

        for txn in transactions:
            if txn["status"].strip().lower() == "approved":
                card_id = int(txn["card_id"])
                amount = float(txn["amount"])
                for card in cards:
                    if card["card_id"] == card_id:
                        card["current_balance"] += amount
                        break

        for card in cards:
            card["current_balance"] = f"{card['current_balance']:.2f}"

        with open(output_file, mode="w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=cards[0].keys())
            writer.writeheader()
            writer.writerows(cards)

        print(f"The updated card balances are saved to {output_file}")

    # updating customer scores and reducing credit limits
    def update_customer_scores_and_limits(
        self, customers_file, cards_file, updated_customers_file, updated_cards_file
    ):
        with open(customers_file, newline="") as f:
            customers = list(csv.DictReader(f))
        with open(cards_file, newline="") as f:
            cards = list(csv.DictReader(f))

        for customer in customers:
            customer["customer_id"] = int(customer["customer_id"])
            customer["credit_score"] = int(customer["credit_score"])
        for card in cards:
            card["customer_id"] = int(card["customer_id"])
            card["credit_limit"] = float(card["credit_limit"])
            card["current_balance"] = float(card["current_balance"])

        negative_scores = {}

        for customer in customers:
            cid = customer["customer_id"]
            user_cards = [card for card in cards if card["customer_id"] == cid]
            total_balance = sum(card["current_balance"] for card in user_cards)
            total_limit = sum(card["credit_limit"] for card in user_cards)
            usage_pct = (total_balance / total_limit * 100) if total_limit > 0 else 0
            score_change = calculate_credit_score_adjustment(usage_pct)
            new_score = max(300, min(850, customer["credit_score"] + score_change))
            if score_change < 0:
                negative_scores[cid] = score_change
            customer["credit_score"] = new_score

        with open(updated_customers_file, mode="w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=customers[0].keys())
            writer.writeheader()
            writer.writerows(customers)
        print(f"Updated credit scores saved to {updated_customers_file}")

        # credit limits are reduced for customers with score drop
        for card in cards:
            cid = card["customer_id"]
            if cid in negative_scores:
                score_change = negative_scores[cid]
                new_limit = calculate_new_credit_limit(
                    card["credit_limit"], score_change
                )
                card["credit_limit"] = round(new_limit, 2)

        for card in cards:
            card["credit_limit"] = f"{card['credit_limit']:.2f}"
            card["current_balance"] = f"{card['current_balance']:.2f}"

        with open(updated_cards_file, mode="w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=cards[0].keys())
            writer.writeheader()
            writer.writerows(cards)
        print(f"Updated cards with new credit limits saved to {updated_cards_file}")


if __name__ == "__main__":
    processor = BatchProcessor()
    processor.approve_pending_transactions(
        stream_file="results/stream_transactions.csv",
        batch_file="results/batch_transactions.csv",
    )
    processor.update_card_balances(
        cards_file="dataset/cards.csv",
        batch_file="results/batch_transactions.csv",
        output_file="results/cards_updated.csv",
    )
    processor.update_customer_scores_and_limits(
        customers_file="dataset/customers.csv",
        cards_file="results/cards_updated.csv",
        updated_customers_file="results/customers_updated.csv",
        updated_cards_file="results/cards_updated.csv",
    )
