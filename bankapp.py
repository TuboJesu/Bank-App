import sqlite3

import random
import re
import time
from datetime import datetime

import hashlib

from getpass import getpass


conn = sqlite3.connect("customers.db")
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON;")

cursor.execute("""
CREATE TABLE IF NOT EXISTS customers (
    account_number INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    balance NUMERIC (10,2) DEFAULT 0.00  
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS transaction_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    transaction_type TEXT NOT NULL,
    transaction_amount INT NOT NULL,
    transaction_time TEXT NOT NULL,
    balance INT NOT NULL,
    FOREIGN KEY (username) REFERENCES customers(username)
)
""")

def sign_up():

    print("***************Sign Up***************")

    while True:

        first_name = input("Enter your first name: ").strip()

        if not first_name:
            print("First name field cannot be left blank")
            continue
        break

    while True:
        last_name = input("Enter your last name: ").strip()

        if not last_name:
            print("Last name field cannot be left blank")
            continue
        break

    while True:
        username = input("Enter your username: ").strip()
        if not username:
            print("Username field cannot be left blank")
            continue

        valid = re.match(r'^[A-Za-z0-9!@.*?,_]+$', username)
        if not valid:
            print("You should only include alphanumerics and characters like '!@.*?,_' in your username")
            continue

        if len(username) < 3 and len(username) > 20:
            print("Your Username length must be between 3 and 20 characters")
            continue
        break


    while True:

        password = getpass("Enter your password: ").strip()
        if not password:
            print("Password field cannot be left blank")
            continue
        
        if len(password) < 8:
            print("Your passowrd length must be a minimum of 8 characters")
            continue
        

        valid = re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[\W_]).+$', password)
        if not valid:
            print("Your password must contain at least one uppercase letter, one lowercase letter, one number, and one special character")
            continue

        confirm_password = getpass("Confirm your password: ").strip()
        if not confirm_password:
            print("Confirm Password field cannot be left blank")
            continue


        if password != confirm_password:
            print("Those passwords don't match")
            continue

        break

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    while True:

        try:
            initial_deposit = float(input("Enter the initial deposit you want to save with us: "))
            balance = 0

            if initial_deposit < 2000:
                print("You can't have less than #2000 in your balance")
                continue

        except ValueError:
            print("Deposit amount must be a number")
            continue
        else:
            balance += initial_deposit
            break
    
    full_name = first_name + " " + last_name
    while True:
        account_number = random.randrange(1460676350, 3060676350)

        user_with_acct_no = cursor.execute("""
        SELECT * FROM customers WHERE account_number = ?
    """, (account_number,)).fetchone()
        
        if user_with_acct_no is not None:
            continue
        break

    

    try:
        cursor.execute("""
        INSERT INTO customers (account_number, full_name, username, password, balance) VALUES
        (?, ?, ?, ?, ?)
        """, (account_number, full_name, username, hashed_password, balance))
    except sqlite3.IntegrityError:
        print("Username already exists")
    else:
        conn.commit()
        print("Sign Up was successful")
        time.sleep(3)
        log_in()


def log_in():
    print("***************Log In***************")
    while True:
        username = input("Enter your username: ").strip()
        if not username:
            print("Username field cannot be left blank")
            continue
        break

    while True:
        password = getpass("Enter your password: ").strip()
        if not password:
            print("Password field cannot be left blank")
            continue
        break


    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    user = cursor.execute("""
    SELECT * FROM customers WHERE username = ? AND password = ?
    """, (username, hashed_password)).fetchone()

    if user is None:
        print("Invalid username or password: ")
        return
    print(f"Log In Successful... This is your account number: {user[0]} \n")

    time.sleep(2)
    operations_menu(user)
    
def account_details(user):
    account_number, full_name, _, _, balance = user

    print(f"Welcome {full_name}...\n")

    user = cursor.execute("""
        SELECT account_number, full_name, balance
        FROM customers
        WHERE full_name = ?
    """, (full_name,)).fetchone()

    print(f"""
Account number: {account_number}
Full name: {full_name}
Balance: #{balance}
    """)


def deposit(user):

    _, _, username, _, balance = user 

    while True:

        try:
            deposit_amount = float(input("Enter the amount you want to deposit in figure: "))

        except ValueError as e:
            print("You have to use figures only")
        else:
            current_balance = deposit_amount + balance
            
            cursor.execute("""
            UPDATE customers
            SET balance = ?
            WHERE username = ?
    """, (current_balance, username))
            conn.commit()

            transaction_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


            cursor.execute("""
            INSERT INTO transaction_history (username, transaction_type, transaction_amount, balance, transaction_time) VALUES
            (?, ?, ?, ?, ?)

    """, (username, "deposit", deposit_amount, current_balance, transaction_time))
            conn.commit()

            print("Deposit Sucessful")
            

def withdrawal(user):

    _, _, username, _, balance = user 
    

    while True:

        try:
            withdrawal_amount = float(input("Enter the amount you want to withdraw in figure: "))

        except ValueError as e:
            print("You have to use figures only")
            continue

        if withdrawal_amount > balance:
            print(f"You can't withdraw more than #{balance}!")
            continue

        current_balance = balance - withdrawal_amount 
        
        cursor.execute("""
        UPDATE customers
        SET balance = ?
        WHERE username = ?
""", (current_balance, username))
        conn.commit()

        transaction_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


        cursor.execute("""
        INSERT INTO transaction_history (username, transaction_type, transaction_amount, balance, transaction_time) VALUES
        (?, ?, ?, ?, ?)

""", (username, "withdrawal", withdrawal_amount, current_balance, transaction_time))
        conn.commit()

        print("Withdrawal Sucessful")
        

def transfer(user):

    _, _, username, _, balance = user 

    while True:
        try:
            recipient_account = int(input("Enter recipient account number: "))
        except ValueError as e:
            print("Provide the account number in figure!")
        else:
            account_num_verification = len(str(recipient_account))
            if account_num_verification != 10:
                print("Wrong account number provided!.... It has to be 10 digits")
                continue

            recipient_details = cursor.execute("""
                SELECT full_name, username, account_number, balance FROM customers
                WHERE account_number = ?
""", (recipient_account, )).fetchone()
            if recipient_details is None:
                print("No customer with that account number!")
                continue

            recipient_full_name, recipient_username, _, recipient_balance = recipient_details
            break
    
    while True:
            
            try:
                transfer_amount = float(input("Enter the amount you want to transfer: "))
            except ValueError as e:
                print("Provide the amount in figure!")
            else:

                if transfer_amount > balance:
                    print(f"You can't transfer more than {balance}!")
                    continue
                break
    
    while True:
                confirmation_prompt = input(f"Enter YES to proceed to transfer {transfer_amount} to {recipient_full_name} or 'NO' to cancel and go back to operations menu: ").upper().strip()
                if confirmation_prompt == "NO":
                    print("Canceling...")
                    time.sleep(1)
                    return
                
                elif confirmation_prompt == "YES":

                    print("")
                    time.sleep(2)
                    print("Transfer Completed...")

                    sender_current_balance = balance - transfer_amount
                    cursor.execute("""
                    UPDATE customers
                    SET balance = ?
                    WHERE username = ?
                    """, (sender_current_balance, username))
                    conn.commit()

                    transaction_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    cursor.execute("""
                    INSERT INTO transaction_history (username, transaction_type, transaction_amount, balance, transaction_time) VALUES
                    (?, ?, ?, ?, ?)

                    """, (username, "transfer", transfer_amount, sender_current_balance, transaction_time))
                    conn.commit()

                    recipient_current_balance = recipient_balance + transfer_amount
                    cursor.execute("""
                    UPDATE customers
                    SET balance = ?
                    WHERE username = ?
                    """, (recipient_current_balance, recipient_details[1]))
                    conn.commit()
                    

                    transaction_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    cursor.execute("""
                    INSERT INTO transaction_history (username, transaction_type, transaction_amount, balance, transaction_time) VALUES
                    (?, ?, ?, ?, ?)

                    """, (recipient_username, "deposit", transfer_amount, recipient_current_balance, transaction_time))
                    conn.commit()
                    return

                else:
                    print("Wrong inputs.. choose only YES or NO")
                    continue
                


def check_balance(user):

    _, full_name, username, _, balance = user

    print(f"Welcome {full_name}...\n")
    customer_balance = cursor.execute("""
        SELECT balance
        FROM customers
        WHERE username = ?
    """, (username,)).fetchone()

    for balance in customer_balance:
        print(f"You have #{balance} in your account.")
        break

    print("")
    time.sleep(1)

        
def check_history(user):
    _, _, username, _, _ = user

    print("These are your transaction histories...")
    user_transactions = cursor.execute("""
        SELECT transaction_type, transaction_amount, balance, transaction_time
        FROM transaction_history
        WHERE username = ?
    """, (username,)).fetchall()

    for transaction_details in user_transactions:
        print(f"""
Transaction type: {transaction_details[0]}
Transaction amount: {transaction_details[1]}
Balance: #{transaction_details[2]}
Transaction time: {transaction_details[3]}\n\n
""")
    

def operations_menu(user):
    print("")

    _, full_name, _, _, _ = user

    while True:
        print(f"""********* Welcome, {full_name} *********** \n\n
            Choose the operation you want to perform today:
            1. Check Account details
            2. Deposit
            3. Withdrawal
            4. Transfer
            5. Check Balance
            6. Check Transaction History
            7. Go back to main menu
            
            """)
        
        user_choice = input("Select from the above options from 1 - 6: ")

        if user_choice == "7":
            return main_menu
        
        elif user_choice == "1":
            account_details(user)
        
        elif user_choice == "2":
            deposit(user)
        
        elif user_choice == "3":
            withdrawal(user)

        elif user_choice == "4":
            transfer(user)
        
        elif user_choice == "5":
            check_balance(user)
        
        elif user_choice == "6":
            check_history(user)

        user_choice = input("Press 0 to go back to operations menu: ")
        if user_choice == "0":
            print("")
            continue
        else:
            print("You have entered a wrong input")
            return
        
        
        
        


main_menu = """
    ****** Welcome to our Bank, You can kindly choose an option from the Menu ******"\n\n
    1. Sign Up
    2. Log In
    3. Close App\n\n
    """


try:
    while True:
        print(main_menu)
        choice = input("Choose an option from the menu above: ").strip()

        if choice == "3":
            print("Thanks for banking with us!")
            break

        if choice == "1":
            sign_up()

        elif choice == "2":
            log_in()
        else:
            print("Invalid choice, select from the menu")

except Exception as e:
    print(f"Oops! Something went wrong: {e}")
finally:
    conn.close()