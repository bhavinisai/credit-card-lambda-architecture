-- created a database schema for a banking system with customers, credit card types, cards, and transactions.
USE banking_system;

-- 1. Customers Table
CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    name VARCHAR(255),
    phone_number VARCHAR(20),
    address VARCHAR(255),
    email VARCHAR(255),
    credit_score INT,
    annual_income DECIMAL(15,2)
);

-- 2. Credit Card Types Table
CREATE TABLE credit_card_types (
    card_type_id INT PRIMARY KEY,
    name VARCHAR(50),
    credit_score_min INT,
    credit_score_max INT,
    credit_limit_min DECIMAL(10,2),
    credit_limit_max DECIMAL(10,2),
    annual_fee DECIMAL(10,2),
    rewards_rate DECIMAL(5,4)
);

-- 3. Cards Table
CREATE TABLE cards (
    card_id INT PRIMARY KEY,
    customer_id INT,
    card_type_id INT,
    card_number VARCHAR(30),
    expiration_date VARCHAR(10),
    credit_limit DECIMAL(10,2),
    current_balance DECIMAL(10,2),
    issue_date DATE,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (card_type_id) REFERENCES credit_card_types(card_type_id)
);

-- 4. Transactions Table
CREATE TABLE transactions (
    transaction_id INT PRIMARY KEY,
    card_id INT,
    merchant_name VARCHAR(255),
    timestamp DATETIME,
    amount DECIMAL(10,2),
    location VARCHAR(255),
    transaction_type VARCHAR(50),
    related_transaction_id INT NULL,
    FOREIGN KEY (card_id) REFERENCES cards(card_id)
);
