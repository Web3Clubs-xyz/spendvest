from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Float, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid
import time
import json
import random, string 

# SQLite database connection
DATABASE_URL = "sqlite:///./site.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def create_all_tables():
    # Create tables
    Base.metadata.create_all(bind=engine)

def generate_uid(length=10):
    chars = string.ascii_letters  + string.digits
    uid = "".join(random.choice(chars) for _ in range(length))
    return uid

class MpesaCustomer(Base):
    __tablename__ = "mpesa_customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String, unique=True, index=True, default=generate_uid)
    whatsapp_client_number = Column(String, index=True, unique=True)
    mpesa_transaction_number = Column(String, unique=True)
    created_at = Column(Float, default=lambda: time.time())
    updated_at = Column(Float, default=lambda: time.time())

    @staticmethod
    def get_all_mpesa_customers(db):
        return db.query(MpesaCustomer).all()

    @staticmethod
    def get_single_user(db, mpesa_number):
        return db.query(MpesaCustomer).filter(MpesaCustomer.mpesa_transaction_number == mpesa_number).first()
    
    @staticmethod
    def get_user_reg_status(db, mpesa_number):
        customer = db.query(MpesaCustomer).filter(MpesaCustomer.mpesa_transaction_number == mpesa_number).first()
        return bool(customer)

    @staticmethod
    def add_mpesa_customer(db, mpesa_transaction_number, whatsapp_client_number):
        # Check if a customer with the same whatsapp_client_number or mpesa_transaction_number already exists
        existing_whatsapp_customer = db.query(MpesaCustomer).filter(MpesaCustomer.whatsapp_client_number == whatsapp_client_number).first()
        if existing_whatsapp_customer:
            raise ValueError(f"Customer with whatsapp_client_number {whatsapp_client_number} already exists.")
        
        existing_mpesa_customer = db.query(MpesaCustomer).filter(MpesaCustomer.mpesa_transaction_number == mpesa_transaction_number).first()
        if existing_mpesa_customer:
            raise ValueError(f"Customer with mpesa_transaction_number {mpesa_transaction_number} already exists.")
        
        customer = MpesaCustomer(
            whatsapp_client_number=whatsapp_client_number,
            mpesa_transaction_number=mpesa_transaction_number
        )
        customer.uid = generate_uid()
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer
    
    def __repr__(self):
        return f"user : {self.whatsapp_client_number}"
    


class AccountSummary(Base):
    __tablename__ = "account_summary"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String, unique=True, index=True, default=generate_uid)
    waid = Column(String, index=True, unique=True)
    total_deposit = Column(Integer, default=0)
    total_settlement = Column(Integer, default=0)
    pending_settlement = Column(Integer, default=0)
    amount_deposited = Column(Float, default=0.00)
    amount_settled = Column(Float, default=0.00)
    saving_percentage = Column(Integer, default=0)
    last_amount_saved = Column(Float, default=0.00)
    total_amount_saved = Column(Float, default=0.00)

    @staticmethod
    def add_summary(db, waid):
        # Check if an account summary with the same waid already exists
        existing_summary = db.query(AccountSummary).filter(AccountSummary.waid == waid).first()
        if existing_summary:
            raise ValueError(f"Account summary with waid {waid} already exists.")
        
        summary = AccountSummary(waid=waid)
        db.add(summary)
        db.commit()
        db.refresh(summary)
        return summary

    @staticmethod
    def get_acc_summary(db, waid):
        return db.query(AccountSummary).filter(AccountSummary.waid == waid).first()
    
    @staticmethod
    def update_acc_summary(db, waid, summary_payload):
        db.query(AccountSummary).filter(AccountSummary.waid == waid).update(summary_payload)
        db.commit()
    
    def __repr__(self):
        return f"AccountSummary(waid={self.waid}, total_deposit={self.total_deposit}, total_settlement={self.total_settlement})"


class RequestTask(Base):
    __tablename__ = "request_task"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String, unique=True, index=True, default=generate_uid)
    customer_waid = Column(String, index=True)
    service_ref = Column(String, index=True)
    service_menu = Column(String)
    service_description = Column(String)
    service_payload = Column(Text)
    completed = Column(Integer, default=0)
    created_at = Column(Float, default=lambda: time.time())
    updated_at = Column(Float, default=lambda: time.time())

    @staticmethod
    def add_request_task(db, client_waid, service_ref, quiz_code, service_description, service_payload):
        # Check if a task with the same service_ref already exists
        existing_task = db.query(RequestTask).filter(RequestTask.service_ref == service_ref).first()
        if existing_task:
            raise ValueError(f"Request task with service_ref {service_ref} already exists.")
        
        task = RequestTask(
            customer_waid=client_waid,
            service_ref=service_ref,
            service_menu=quiz_code,
            service_description=service_description,
            service_payload=json.dumps(service_payload)
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def get_all_tasks(db):
        return db.query(RequestTask).all()
    
    @staticmethod
    def get_task(db, ref):
        return db.query(RequestTask).filter(RequestTask.service_ref == ref).first()
    
    @staticmethod
    def complete_task(db, ref):
        db.query(RequestTask).filter(RequestTask.service_ref == ref).update({"completed": 1})
        db.commit()
    
    def __repr__(self):
        return f"RequestTask(customer_waid={self.customer_waid}, service_menu={self.service_menu}, completed={self.completed})"



class Settlement(Base):
    __tablename__ = "settlement"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String, unique=True, index=True, default=generate_uid)
    ref = Column(String, index=True, unique=True)
    end_settlement_number = Column(String, index=True)
    menu_code = Column(String)
    amount = Column(Float)
    completed = Column(Integer, default=0)
    created_at = Column(Float, default=lambda: time.time())
    updated_at = Column(Float, default=lambda: time.time())

    @staticmethod
    def add_settlement(db, client_waid, menu_code, amount, complete_bool, mpesa_ref):
        # Check if a settlement with the same ref already exists
        existing_settlement = db.query(Settlement).filter(Settlement.ref == mpesa_ref).first()
        if existing_settlement:
            raise ValueError(f"Settlement with ref {mpesa_ref} already exists.")
        
        settlement = Settlement(
            ref=mpesa_ref,
            end_settlement_number=client_waid,
            menu_code=menu_code,
            amount=amount,
            completed=int(complete_bool)
        )
        db.add(settlement)
        db.commit()
        db.refresh(settlement)
        return settlement

    @staticmethod
    def get_customer_settlement(db, ref):
        return db.query(Settlement).filter(Settlement.ref == ref).first()
    
    @staticmethod
    def complete_customer_settlement(db, ref):
        db.query(Settlement).filter(Settlement.ref == ref).update({"completed": 1})
        db.commit()
    
    def __repr__(self):
        return f"Settlement(ref={self.ref}, end_settlement_number={self.end_settlement_number}, completed={self.completed})"


class SlotQuestion(Base):
    __tablename__ = "slot_question"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String, unique=True, index=True, default=generate_uid)
    slot_code = Column(String, index=True, unique=True)
    slot_description = Column(String)
    question_payload = Column(Text)
    created_at = Column(Float, default=lambda: time.time())
    updated_at = Column(Float, default=lambda: time.time())

    def __repr__(self):
        return f"id : {self.id}, slot_code : {self.slot_code}"
    
    @staticmethod
    def add_slot_question(db, slot_code, slot_description, question_payload):
        # Check if a slot question with the same slot_code already exists
        existing_slot_question = db.query(SlotQuestion).filter(SlotQuestion.slot_code == slot_code).first()
        if existing_slot_question:
            raise ValueError(f"Slot question with slot_code {slot_code} already exists.")
        
        slot_question = SlotQuestion(
            slot_code=slot_code,
            slot_description=slot_description,
            question_payload=json.dumps(question_payload)
        )
        db.add(slot_question)
        db.commit()
        db.refresh(slot_question)
        return slot_question

    @staticmethod
    def get_question_pack(db, slot_code):
        slot_question = db.query(SlotQuestion).filter(SlotQuestion.slot_code == slot_code).first()
        if slot_question:
            return json.loads(slot_question.question_payload)
        return None

    @staticmethod
    def get_slot_question(db, slot_code):
        slot_question = db.query(SlotQuestion).filter(SlotQuestion.slot_code == slot_code).first()
        if slot_question:
            slot_question_dict = slot_question.__dict__
            slot_question_dict['question_payload'] = json.loads(slot_question_dict['question_payload'])
            return slot_question_dict
        return None



def load_slotquizes(db):
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
        }
    ]

    for data in slot_data:
        SlotQuestion.add_slot_question(
            db,
            slot_code=data['slot_code'],
            slot_description=data['slot_description'],
            question_payload=data['question_payload']
        )
    print("Slot quizzes loaded successfully")

# Example usage
if __name__ == '__main__':
    create_all_tables()
    db = SessionLocal()
    load_slotquizes(db)
    db.close()
