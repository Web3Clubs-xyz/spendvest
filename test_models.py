import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, MpesaCustomer, AccountSummary, RequestTask, Settlement, SlotQuestion, DATABASE_URL
from payments2 import generate_uid, send_payment, send_user_stk

dev_proxy_url = "https://cb92-102-217-172-2.ngrok-free.app"

class TestModels(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(DATABASE_URL)
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)
        cls.db = TestingSessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        # Base.metadata.drop_all(bind=cls.engine)

    def test_add_mpesa_customer(self):
        customer = MpesaCustomer.add_mpesa_customer(self.db, "254703103960", "254703103960")
        print(f"customer with wahtsapp_client_number , {customer.whatsapp_client_number}")
        
        self.assertIsNotNone(customer)
        self.assertEqual(customer.mpesa_transaction_number, "254703103960")
        self.assertEqual(customer.whatsapp_client_number, "254703103960")

    def test_add_account_summary(self):
        summary = AccountSummary.add_summary(self.db, "254703103960")
        print(f"Account summary for user : {summary.waid}")

        self.assertIsNotNone(summary)
        self.assertEqual(summary.waid, "254703103960")

    def test_add_request_task(self):
        task = RequestTask.add_request_task(self.db, "254703103960", "SM", "description", {"key": "value"})
        print(f"task fetched for user : {task.customer_waid}")

        self.assertIsNotNone(task)
        self.assertEqual(task.customer_waid, "254703103960")
        self.assertEqual(task.service_menu, "SM")
        self.assertEqual(task.service_description, "description")
        self.assertEqual(task.service_payload, '{"key": "value"}')

    def test_add_settlement(self):
        settlement = Settlement.add_settlement(self.db, "254703103960", "menu_code", 100.0, True, "ref123")
        print(f"settlement for ref {settlement.ref}")

        self.assertIsNotNone(settlement)
        self.assertEqual(settlement.ref, "ref123")
        self.assertEqual(settlement.end_settlement_number, "254703103960")
        self.assertEqual(settlement.menu_code, "menu_code")
        self.assertEqual(settlement.amount, 100.0)
        self.assertEqual(settlement.completed, 1)

    def test_add_slot_question(self):
        slot_question = SlotQuestion.add_slot_question(self.db, "slot_code", "description", {"question": "payload"})
        self.assertIsNotNone(slot_question)
        self.assertEqual(slot_question.slot_code, "slot_code")
        self.assertEqual(slot_question.slot_description, "description")
        self.assertEqual(slot_question.question_payload, '{"question": "payload"}')
    
    def test_add_user_deposit(self):
        # example transactions : Deposit
        # simulating 
        # Flow : RequestTask, Settlement, AccountSummary
        user_mpesa_number = '254703103960'
        end_mpesa_number ='254701561559'
        slot_code = "SM"
        description = "Send Money"
        amount = 10

        body = {
        "MerchantCode": "600980",
        "NetworkCode": "63902",
        "PhoneNumber":user_mpesa_number,
        "TransactionDesc": "Deposit for Service",
        "AccountReference": generate_uid(10),
        "Currency": "KES",
        "Amount": amount,
        "TransactionFee": 0,
        "CallBackURL": f"{dev_proxy_url}/mpesa_callback"
        }
        merchant_request_id = "mpesaref123"

        RequestTask.add_request_task(self.db,user_mpesa_number, slot_code, description, body)
        Settlement.add_settlement(self.db, end_mpesa_number, slot_code, amount, False, merchant_request_id)
        
        summary = AccountSummary.get_acc_summary(self.db, user_mpesa_number)
        
        deposit_update = {
            'total_deposit':1,
            'pending_settlement':1,
        }
        AccountSummary.update_acc_summary(self.db, user_mpesa_number, deposit_update)
    

    def test_make_settlement(self):
        summary = AccountSummary.get_acc_summary(self.db, '254703103960')
        payment_amount=0
        bal1=3

        summary_update = {
                'pending_settlement':0,
                'total_settlement': summary.total_settlement + 1,
                'amount_settled' : summary.amount_settled + float(payment_amount),
                'total_amount_saved':summary.total_amount_saved  + float(bal1),
                'last_amount_saved':summary.last_amount_saved + float(bal1)

            }


        pass 

         

if __name__ == '__main__':
    unittest.main()
