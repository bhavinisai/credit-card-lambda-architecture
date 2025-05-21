# Banking System with Lambda Architecture

This project implements a **Banking System** using the **Lambda Architecture** model. It simulates a credit card transaction processing system that includes:

- **Real-time stream processing** using Kafka
- **Batch processing** for balance, credit score, and limit updates
- A **serving layer** to sync final results to MySQL

The system ensures valid transactions are approved, balances are updated, and customer credit scores are adjusted based on usage.

---

## Dataset Description and Schema 
The project uses a MySQL database named `banking_system`, that has to be initialized using the `banking_schema.sql` file. It defines the key tables and relationships needed for simulating a credit card transaction system.

The dataset used in this project represents a simplified legacy banking system, provided in CSV format. It consists of key entities related to credit card transactions, customers, and financial operations.

### Customers

Contains information about each banking customer:

- `customer_id`, `name`, `phone_number`, `address` , `email`
- `credit_score`, `annual_income`

### Cards

Represents each customer's issued credit card:

- `card_id`, `customer_id`,`card_type_id`, 
- `card_number`, `expiration_date`, `credit_limit`, 
- `current_balance`, `issue_date`

### Credit Card Types

Metadata defining card types and eligibility:

- `card_type_id`, `name`, `credit_score_min`, `credit_score_max` 
- `credit_limit_min`, `credit_limit_max`
- `annual_fee`, `rewards_rate`

### Transactions

Captures raw transactional activity on credit cards:

- `transaction_id`, `card_id`, `merchant_name`
- `timestamp`, `amount`, `location`
- `transaction_type`, `related_transaction_id`

All datasets are stored in the `dataset/` directory, and output files are written to `results/`.

Before starting the stream layer, make sure the initial dataset is loaded into the MySQL database, so that the Kafka producer and stream validator can operate on real records.

---

## Required Packages

Install all dependencies with:

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install kafka-python mysql-connector-python python-dotenv black
```

---

## Execution

> **Ensure MySQL and Kafka are installed and running before proceeding.**

### 1. Set Up Environment

Create a `.env` file by copying `.env.example`:

```bash
cp .env.example .env
```

Update `.env` with your database credentials and Kafka settings:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=banking_system

KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=bank-transactions
OUTPUT_DIR=results
```

### 2. Start Kafka

In one terminal, start Zookeeper:
```bash
cd ~/kafka/kafka_2.13-3.8.1 (path can be changed accordingly)
bin/zookeeper-server-start.sh config/zookeeper.properties

```

In another terminal, start the Kafka server:
```bash
cd ~/kafka/kafka_2.13-3.8.1 (path can be changed accordingly)
bin/kafka-server-start.sh config/server.properties
```
### 3. Create the 'bank-transactions' topic
cd ~/kafka/kafka_2.13-3.8.1
bin/kafka-topics.sh --create --topic bank-transactions --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

### 4. Run Kafka Producer

Send transactions from MySQL to Kafka:

```bash
python3 src/producer.py
```

###  5. Run Kafka Consumer

Validate transactions using amount, location, and balance logic:

```bash
python3 src/consumer.py
```

Expected output:
- `results/stream_transactions.csv`

**NOTE:**
**Make sure Kafka and Zookeeper are running before the producer/consumer.**
**Also, check that the Kafka topic (`bank-transactions`) exists before starting the producer.**

### 6. Run Batch Processor

Process and approve transactions (from `stream_transactions.csv`), update balances and scores:

```bash
python3 src/batch_processor.py
```

Expected outputs:
- `results/batch_transactions.csv`
- `results/cards_updated.csv`
- `results/customers_updated.csv`


### 7. Update MySQL Tables for Serving Layer

Use the following SQL commands in MySQL to sync updates for the customers and cards tables:

```sql
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE cards;
TRUNCATE TABLE customers;

LOAD DATA LOCAL INFILE '/absolute/path/to/cards_updated.csv'
INTO TABLE cards
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS;

LOAD DATA LOCAL INFILE '/absolute/path/to/customers_updated.csv'
INTO TABLE customers
FIELDS TERMINATED BY ',' ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 ROWS;

SET FOREIGN_KEY_CHECKS = 1;
```

Replace `/absolute/path/to/...` with your actual file path from WSL.

---

## Output

After running the full pipeline:
- `stream_transactions.csv` will contain validated transactions
- `batch_transactions.csv` will contain approved ones
- `cards_updated.csv` and `customers_updated.csv` will reflect balance and score changes
- Final tables in MySQL will be updated accordingly

---

## Data Validation

Data validation is performed in the **stream layer** by the Kafka consumer, ensuring only valid transactions are forwarded to the batch processor. Each incoming transaction is validated using a set of business rules defined in the project:

1. **Amount Threshold Check**  
   - If the transaction amount is **greater than or equal to 50%** of the card’s credit limit, it is **declined**.

2. **Location Proximity Check**  
   - For **purchase** transactions, the ZIP code of the **customer's address** and the **merchant's address** are compared.
   - If the first digit differs, the transaction is **declined** (too far).
   - If only the second digit differs, it is **accepted** as “moderately close”.

3. **Credit Limit Check**  
   - If the **pending balance (current balance + transaction amount)** exceeds the card’s credit limit, the transaction is **declined**.
   - For **refund** and **cancellation** transactions, the amount is subtracted from the pending balance.

---

## Status

- If a transaction passes all rules → marked as `"pending"`
- If it fails any rule → marked as `"declined"` 

All validated transactions are written to `results/stream_transactions.csv`, including:
- `status`: `"pending"` or `"declined"`
- `pending_balance`: computed based on current card balance and transaction type

---

## Summary

- Uses Kafka for real-time streaming
- Processes and validates financial transactions
- Adjusts credit scores and credit limits based on usage
- Uses class-based structure and inlined helper functions
- Manual SQL sync used for serving layer

---

## Author

**Bhavini Sai Mallu**  
Graduate Student at 
Rochester Institute of Technology  
bm5726@rit.edu  

This project was completed as part of the **DSCI-644** course: Software Engineering for Data Science at Rochester Institute of Technology. This project focuses on building a scalable Banking System using **Lambda Architecture** by integrating real-time validation through Kafka, batch processing using Python, and a serving layer through MySQL, along with modular, testable code design and pipeline compatibility.


---