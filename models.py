import redis
import uuid
import time
import random
import json

# Create a Redis client
# redis_client = redis.StrictRedis(host='localhost', port=6379, db=10)

redis_client = redis.Redis(
  host='redis-18019.c12.us-east-1-4.ec2.redns.redis-cloud.com',
  port=18019,
  password='5YQQuHQEPoC64Ccs2iEXANjyxlSO43LY')

class MpesaCustomer:
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
        print(f"checking user registeration, {res}")
        if res == {}:
            return False 
        else:
            return True 

    @staticmethod
    def add_mpesa_customer(mpesa_transaction_number,whatsapp_client_number):
        uid = str(uuid.uuid4())
        current_time = time.time()
        key = f"mpesa_customer:{whatsapp_client_number}"

        if redis_client.exists(key):
            print("customer already exists")
            return None  # Customer already exists
        customer = {
            'uid': uid,
            'whatsapp_client_number':whatsapp_client_number,
            'mpesa_transaction_number': mpesa_transaction_number,
            'created_at': current_time,
            'updated_at': current_time
        }
        redis_client.hmset(key, customer)
        return customer

class AccountSummary:
    @staticmethod
    def add_summary(waid):
        key = f"account_summary:{waid}"
        summary = {
            'total_deposit':0,
            'total_settlement':0,
            'pending_settlement':0,
            'amount_deposited':0.00,
            'amount_settled':0.00,
            'saving_percentage':0,
            'last_amount_saved':0.00,
            'total_amount_saved':0.00,
        }
        redis_client.hmset(key, summary)
         

    @staticmethod
    def get_acc_summary(waid):
        key = f"account_summary:{waid}"
        return redis_client.hgetall(key) 
    
    @staticmethod
    def update_acc_summary(waid,summary_payload):
        key=f"account_summary:{waid}"
        return redis_client.hmset(key,summary_payload)


class RequestTask:
    @staticmethod
    def add_request_task(client_waid, quiz_code, service_description, service_payload):
        uid = str(uuid.uuid4())
        current_time = time.time()
        ref = service_payload['AccountReference']
        key = f"request_task:{ref}"
        task = {
            'uid': uid,
            'customer_waid': client_waid,
            'service_menu':quiz_code,
            'service_description': service_description,
            'service_payload': json.dumps(service_payload),
            'completed': int(False),
            'created_at': current_time,
            'updated_at': current_time
        }
        redis_client.hmset(key, task)
        return task
    
    @staticmethod
    def get_task(ref) :
        key = f"request_task:{ref}"
        task = redis_client.hgetall(key)
        if task != None :
            return task
        
    @staticmethod
    def complete_task(ref):
        key = f"request_task:{ref}"
        return redis_client.hset(key, 'completed', 1)
         

   
class SlotQuestion:
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
        return redis_client.hmset(key, slot_question)

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


class Settlement:
    @staticmethod
    def add_settlement(client_waid, menu_code, amount, complete_bool, mpesa_ref):
        key = f"settlement:{mpesa_ref}"
        current_time = time.time()
     
        settlement = {
            'end_settlement_number' : client_waid,
            'menu_code':menu_code,
            'amount':amount,
            'completed':int(complete_bool),
            'created_at':current_time,
            'updated_at':current_time
        }

        return redis_client.hmset(key, settlement)
        

    @staticmethod
    def get_customer_settlement(ref):
        key = f"settlement:{ref}"
        set = redis_client.hgetall(key)

        # settlement = {
        #     'end_settlement_number' : set[b'end_settlement_number'],
        #     # 'menu_code': set[b'menu_code'],
            # 'amount': set[b'amount'],
            # 'completed':set[b'completed'],
            # 'created_at':set[b'created_at'],
            # 'updated_at':set[b'updated_at']
        # }
        return set

    @staticmethod
    def complete_customer_settlement(ref):
        return redis_client.hset(f"settlement:{ref}", 'completed', 1)


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
    # MpesaCustomer.test_add_10_users()  # Add test users
    load_slotquizes()  # Load initial menu data
