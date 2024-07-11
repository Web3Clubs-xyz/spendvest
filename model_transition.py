from pydantic import BaseModel, Field
import sqlite3
import redis
import uuid
import json
import time

# SQLite database connection
conn = sqlite3.connect('site.db')
cursor = conn.cursor()

# Redis connection for MpesaCustomer and SlotQuestion
redis_client = redis.Redis(
    host='redis-18019.c12.us-east-1-4.ec2.redns.redis-cloud.com',
    port=18019,
    password='5YQQuHQEPoC64Ccs2iEXANjyxlSO43LY')

class MpesaCustomer(BaseModel):
    uid: str
    whatsapp_client_number: str
    mpesa_transaction_number: str
    created_at: float
    updated_at: float

    @staticmethod
    def get_all_mpesa_customers():
        customer_keys = redis_client.keys('mpesa_customer:*')
        customers = []
        for key in customer_keys:
            customer = redis_client.hgetall(key)
            customer['mpesa_number'] = customer[b'mpesa_number'].decode('utf-8')
            customers.append(customer)
        return customers

    @staticmethod
    def get_single_user(mpesa_number):
        key = f"mpesa_customer:{mpesa_number}"
        return redis_client.hgetall(key)
    
    @staticmethod
    def get_user_reg_status(mpesa_number):
        key = f"mpesa_customer:{mpesa_number}"
        res = redis_client.hgetall(key)
        print(f"checking user registration, {res}")
        if res == {}:
            return False 
        else:
            return True 

    @staticmethod
    def add_mpesa_customer(mpesa_transaction_number, whatsapp_client_number):
        uid = str(uuid.uuid4())
        current_time = time.time()
        key = f"mpesa_customer:{whatsapp_client_number}"

        if redis_client.exists(key):
            print("customer already exists")
            return None  # Customer already exists
        customer = {
            'uid': uid,
            'whatsapp_client_number': whatsapp_client_number,
            'mpesa_transaction_number': mpesa_transaction_number,
            'created_at': current_time,
            'updated_at': current_time
        }
        redis_client.hmset(key, customer)
        return customer


class AccountSummary(BaseModel):
    waid: str
    total_deposit: int = 0
    total_settlement: int = 0
    pending_settlement: int = 0
    amount_deposited: float = 0.00
    amount_settled: float = 0.00
    saving_percentage: int = 0
    last_amount_saved: float = 0.00
    total_amount_saved: float = 0.00

    @staticmethod
    def add_summary(waid):
        cursor.execute("""
            INSERT INTO account_summary (
                waid, total_deposit, total_settlement, pending_settlement,
                amount_deposited, amount_settled, saving_percentage,
                last_amount_saved, total_amount_saved
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (waid, 0, 0, 0, 0.00, 0.00, 0, 0.00, 0.00))
        conn.commit()

    @staticmethod
    def get_acc_summary(waid):
        cursor.execute("SELECT * FROM account_summary WHERE waid=?", (waid,))
        return cursor.fetchone()
    
    @staticmethod
    def update_acc_summary(waid, summary_payload):
        columns = ', '.join([f"{key} = ?" for key in summary_payload.keys()])
        values = tuple(summary_payload.values())

        cursor.execute(f"UPDATE account_summary SET {columns} WHERE waid=?", (*values, waid))
        conn.commit()

class RequestTask(BaseModel):
    uid: str
    customer_waid: str
    service_menu: str
    service_description: str
    service_payload: str
    completed: int
    created_at: float
    updated_at: float

    @staticmethod
    def add_request_task(client_waid, quiz_code, service_description, service_payload):
        uid = str(uuid.uuid4())
        current_time = time.time()
        ref = service_payload['AccountReference']
        cursor.execute("""
            INSERT INTO request_task (
                uid, customer_waid, service_menu, service_description,
                service_payload, completed, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (uid, client_waid, quiz_code, service_description,
              json.dumps(service_payload), int(False), current_time, current_time))
        conn.commit()

    @staticmethod
    def get_task(ref):
        cursor.execute("SELECT * FROM request_task WHERE ref=?", (ref,))
        return cursor.fetchone()
    
    @staticmethod
    def complete_task(ref):
        cursor.execute("UPDATE request_task SET completed=? WHERE ref=?", (1, ref))
        conn.commit()

class Settlement(BaseModel):
    ref: str
    end_settlement_number: str
    menu_code: str
    amount: float
    completed: int
    created_at: float
    updated_at: float

    @staticmethod
    def add_settlement(client_waid, menu_code, amount, complete_bool, mpesa_ref):
        current_time = time.time()
        cursor.execute("""
            INSERT INTO settlement (
                ref, end_settlement_number, menu_code, amount, completed,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (mpesa_ref, client_waid, menu_code, amount, int(complete_bool), current_time, current_time))
        conn.commit()

    @staticmethod
    def get_customer_settlement(ref):
        cursor.execute("SELECT * FROM settlement WHERE ref=?", (ref,))
        return cursor.fetchone()
    
    @staticmethod
    def complete_customer_settlement(ref):
        cursor.execute("UPDATE settlement SET completed=? WHERE ref=?", (1, ref))
        conn.commit()


class SlotQuestion(BaseModel):
    uid: str
    slot_code: str
    slot_description: str
    question_payload: dict
    created_at: float
    updated_at: float

    @staticmethod
    def add_slot_question(slot_code, slot_description, question_payload):
        uid = str(uuid.uuid4())
        current_time = time.time()
        key = f"slot_question:{slot_code}"
        slot_question = {
            "uid": uid,
            "slot_code": slot_code,
            "slot_description": slot_description,
            "question_payload": json.dumps(question_payload),
            "created_at": current_time,
            "updated_at": current_time
        }
        redis_client.hmset(key, slot_question)

    @staticmethod
    def get_question_pack(slot_code):
        key = f"slot_question:{slot_code}"
        if redis_client.exists(key):
            slot_question = redis_client.hgetall(key)
            question_payload = json.loads(slot_question[b'question_payload'])
            return question_payload
        return None

    @staticmethod
    def get_slot_question(slot_code):
        key = f"slot_question:{slot_code}"
        if redis_client.exists(key):
            slot_question = redis_client.hgetall(key)
            slot_question_dict = {k.decode('utf-8'): v.decode('utf-8') for k, v in slot_question.items()}
            slot_question_dict['question_payload'] = json.loads(slot_question_dict['question_payload'])
            return slot_question_dict
        return None


def load_slotquizes():
    slot_data = [
        {
            "slot_code": "RU",
            "slot_description": "Register Mpesa Number",
            "question_payload": {
                0: "Register!\n\nWould you like us to register this number for Mpesa service?\n\n Yes or No",
                1: "Confirm registration, by re-entering previous answer"
            }
        },
        {
            "slot_code": "SM",
            "slot_description": "Send Money",
            "question_payload": {
                0: "Send money!\n\nEnter recipient Mpesa phone number",
                1: "Confirm number, by repeating it",
                2: "Enter amount to send"
            }
        },
        {
            "slot_code": "SA",
            "slot_description": "Set Saving Percentage",
            "question_payload": {
                0: "Set savings!\n\nEnter percentage value",
                1: "Confirm percentage, by repeating it"
            }
        },
        {
            "slot_code": "WD",
            "slot_description": "Withdraw Savings",
            "question_payload": {
                0: "Withdraw Savings!\n\nEnter amount to send",
                1: "Confirm amount, by repeating it"
            }
        },
        
       ]

    for data in slot_data:
        SlotQuestion.add_slot_question(
            slot_code=data['slot_code'],
            slot_description=data['slot_description'],
            question_payload=data['question_payload']
        )
    print("Slot quizzes loaded successfully")


# Example usage:
if __name__ == '__main__':
    # Initialize SQLite tables if they don't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS account_summary (
            waid TEXT PRIMARY KEY,
            total_deposit INTEGER,
            total_settlement INTEGER,
            pending_settlement INTEGER,
            amount_deposited REAL,
            amount_settled REAL,
            saving_percentage INTEGER,
            last_amount_saved REAL,
            total_amount_saved REAL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS request_task (
            uid TEXT PRIMARY KEY,
            customer_waid TEXT,
            service_menu TEXT,
            service_description TEXT,
            service_payload TEXT,
            completed INTEGER,
            created_at REAL,
            updated_at REAL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settlement (
            ref TEXT PRIMARY KEY,
            end_settlement_number TEXT,
            menu_code TEXT,
            amount REAL,
            completed INTEGER,
            created_at REAL,
            updated_at REAL
        )
    """)
    
    conn.commit()

    # Example usage:
    load_slotquizes()
