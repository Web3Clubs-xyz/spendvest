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
    def add_mpesa_customer(mpesa_number):
        uid = str(uuid.uuid4())
        current_time = time.time()
        key = f"mpesa_customer:{mpesa_number}"
        if redis_client.exists(key):
            return None  # Customer already exists
        customer = {
            'uid': uid,
            'mpesa_number': mpesa_number,
            'created_at': current_time,
            'updated_at': current_time
        }
        redis_client.hmset(key, customer)
        return customer

    @staticmethod
    def test_add_10_users():
        for _ in range(10):
            mpesa_number = "2547" + ''.join([str(random.randint(0, 9)) for _ in range(8)])
            MpesaCustomer.add_mpesa_customer(mpesa_number)
        print("10 users added successfully")

class Menu:
    @staticmethod
    def load_question_pack(menu_code):
        key = f"menu:{menu_code}"
        if redis_client.exists(key):
            menu = redis_client.hgetall(key)
            menu['question_payload'] = json.loads(menu[b'question_payload'])
            return menu['question_payload']
        return None

    @staticmethod
    def add_menu(menu_code, menu_description, question_payload):
        uid = str(uuid.uuid4())
        current_time = time.time()
        key = f"menu:{menu_code}"
        menu = {
            'uid': uid,
            'menu_code': menu_code,
            'menu_description': menu_description,
            'question_payload': json.dumps(question_payload),
            'created_at': current_time,
            'updated_at': current_time
        }
        redis_client.hmset(key, menu)
    
    @staticmethod
    def get_menu(menu_code):
        key = f"menu:{menu_code}"
        menu = redis_client.hgetall(key)
        if menu :
            return_menu = {
                'uid' : menu[b'uid'],
                'menu_code':menu[b'menu_code'],
                'menu_description':menu[b'menu_description'],
                'question_payload':menu[b'question_payload'],
                'created_at':menu[b'created_at'],
                'updated_at':menu[b'updated_at']
            }
            return return_menu
            
        else:
            return False  

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
    def add_request_task(client_waid, menu_code,service_description, service_payload):
        uid = str(uuid.uuid4())
        current_time = time.time()
        ref = service_payload['AccountReference']
        key = f"request_task:{ref}"
        task = {
            'uid': uid,
            'customer_waid': client_waid,
            'service_menu':menu_code,
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
            return {
                # 'uid':task[b'uid'],
                'customer_waid':task[b'customer_waid'].decode('utf-8'),
                'service_menu':task[b'service_menu'].decode('utf-8'),
                'service_description':task[b'service_description'].decode('utf-8'),
                'service_payload':task[b'service_payload'].decode('utf-8'),
                'completed':task[b'completed'].decode('utf-8'),
                'created_at':task[b'created_at'].decode('utf-8'),
                'updated_at':task[b'updated_at'].decode('utf-8')
            }
        
    @staticmethod
    def complete_task(ref):
        key = f"request_task:{ref}"
        return redis_client.hset(key, 'completed', 1)
         



class Settlement:
    @staticmethod
    def add_settlement(client_waid, menu_code, amount, complete_bool, ref):
        key = f"settlement:{ref}"
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
        settlement = {
            'end_settlement_number' : set[b'end_settlement_number'],
            'menu_code': set[b'menu_code'],
            'amount': set[b'amount'],
            'completed':set[b'completed'],
            'created_at':set[b'created_at'],
            'updated_at':set[b'updated_at']
        }
        return settlement

    @staticmethod
    def complete_customer_settlement(ref):
        return redis_client.hset(f"settlement:{ref}", 'completed', 1)
    
def load_menu_table():
    menu_data = [
        {
            "menu_code": "RU",
            "menu_description": "Request register user task",
            "question_payload": {
                0: "Register!\n\nWould you like us to register this number for Mpesa service?\n Yes or No",
                1: "Confirm registration, by re-entering previous answer"
            }
        },
        {
            "menu_code": "SM",
            "menu_description": "Request send money task",
            "question_payload": {
                0: "Send money!\n\nEnter recipient Mpesa phone number",
                1: "Confirm number, by repeating it",
                2: "Enter amount to send"
            }
        },
        {
            "menu_code": "LP",
            "menu_description": "Request lipa na pochi la biashara task",
            "question_payload": {
                0: "Lipa pochi!\n\nEnter recipient Mpesa phone number",
                1: "Confirm number, by repeating it",
                2: "Enter amount to send"
            }
        },
        {
            "menu_code": "LBT",
            "menu_description": "Request lipa na Buy Goods and Services task",
            "question_payload": {
                0: "Buy Goods and Services!\n\nEnter recipient Mpesa buy goods and services number",
                1: "Confirm number, by repeating it",
                2: "Enter amount to send"
            }
        },
        {
            "menu_code": "LBP",
            "menu_description": "Request lipa na paybill task",
            "question_payload": {
                0: "Paybill!\n\nEnter recipient Mpesa paybill number",
                1: "Confirm number, by repeating it",
                2: "Enter amount to send"
            }
        },
        {
            "menu_code": "ST",
            "menu_description": "Choose command to execute",
            "question_payload": {
                0: "Select the following commands to proceed: \n\n0./reg\nfor register Whatsapp number for Mpesa services\n\n1./sm\nfor send money\n\n2./lp\nfor lipa pochi\n\n3./lbt\nfor buy goods and services till\n\n4./lbp\nfor paybill till\n\n5./refresh\nfor refreshing accout transactions\n\nTo select any enter /command or number"
            }
        }
    ]

    for data in menu_data:
        Menu.add_menu(
            menu_code=data['menu_code'],
            menu_description=data['menu_description'],
            question_payload=data['question_payload']
        )
    print("Menu data loaded successfully")

# Example usage:
if __name__ == '__main__':
    MpesaCustomer.test_add_10_users()  # Add test users
    load_menu_table()  # Load initial menu data
