from flask import Flask, jsonify, request

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse, Message
from twilio.rest import Client
import urllib
import redis
import random
import string 
import time

import re
import json 

from blu import Session
from models import RequestTask, AccountSummary, Settlement
from payments2 import send_user_stk, send_payment
from models  import Menu, MpesaCustomer
import uuid



# Account SID and Auth Token from www.twilio.com/console
client = Client('TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN')

app = Flask(__name__)


def generate_uid(length=10):
    chars = string.ascii_letters  + string.digits
    uid = "".join(random.choice(chars) for _ in range(length))
    return uid


slot_handlers = ["ru_handler", "sm_handler", "lp_handler", "lbt_handler", "lbp_handler", "start_handler"]

# whatsapp ingress endpoint
@app.route("/whatsapp", methods=["POST"])
def web_hook():
    in_data = request.values 
    user_waid = in_data.get('WaId')
    user_name = in_data.get('ProfileName')
    print(f"incoming payload is , {in_data}")

    if Session.is_first_time_contact(user_waid):
        print(f"First time contact")

        if Session.is_slot_filling(user_waid):
            print(f"user is slot filling")
            current_handler = Session.get_session(user_waid)[b'current_slot_handler'].decode('utf-8')
            print(f"current handler is : {current_handler}")
            client_input = in_data.get('Body').lower()
            if current_handler == "st_handler":
                if client_input in ['/reg', '/sm', '/lp', '/lbt', '/lbp', '/st', '/cancel', '/refresh', '/about']:
                    if client_input == '/reg':
                        Session.load_handler(user_waid,"ru_handler", "RU", 0, 2)
                        # ask actual first question
                        curr_slot_details = Session.fetch_slot_details(user_waid)
                        menu_code = curr_slot_details['menu_code']
                        quiz_pack = Menu.load_question_pack(menu_code)
                        quiz = Session.return_current_slot_quiz(user_waid, quiz_pack)
                        Session.step_slotting(user_waid, quiz_pack)
                        return output_bot_message(quiz)
                    
                    elif client_input == '/sm':
                        Session.load_handler(user_waid, "sm_handler", "SM",0, 3)
                        curr_slot_details = Session.fetch_slot_details(user_waid)
                        menu_code = curr_slot_details['menu_code']
                        quiz_pack = Menu.load_question_pack(menu_code)
                        quiz = Session.return_current_slot_quiz(user_waid, quiz_pack)
                        Session.step_slotting(user_waid, quiz_pack)
                        return output_bot_message(quiz)
                    
                    elif client_input == "/lp":
                        message = "You have selected Lipa Pochi task"
                        return output_bot_message(message)
                        
                    elif client_input == "/lbt":
                        message = "You have selected buy goods and services task"
                        return output_bot_message(message)
                        
                    elif client_input == "/lbp":
                        message = "You have selected paybill task"
                        return output_bot_message(message)
                    
                    elif client_input == "/st" or client_input == "/refresh":
                        print(f"processing /st command")
                        Session.load_handler(user_waid,"st_handler", "ST", 0, 1)
                        curr_slot_details = Session.fetch_slot_details(user_waid)
                        menu_code = curr_slot_details['menu_code']
                        quiz_pack = Menu.load_question_pack(menu_code)
                        quiz = Session.return_current_slot_quiz(user_waid, quiz_pack)

                        # generaete str for account summary
                        generated_summary = get_user_acc_summary_stmt(user_waid, user_name)
                        # mix with quiz and return output
                        output_message = f"{generated_summary}\n\nMenu:\n\n{quiz}"
                        image_list = ['./static/bot_media/Account.png']

                        # Session.step_slotting(user_waid, quiz_pack)
                        return test_message_with_image(output_message, image_list)
                    
                    elif client_input == "/about":
                        image_list = ['./static/bot_media/AboutUs.mp4']
                        message_test = f"{user_name}\n\nI am spendvest bot, I can help you with your micro-savings plan!\nTo access services press /refresh"
                        return test_message_with_image(message_test,image_list)
                    

                else:
                    return output_bot_message("Enter comand /st to proceed")
                 
            elif current_handler == "ru_handler":
                curr_slot_details = Session.fetch_slot_details(user_waid)          
                menu_code = curr_slot_details['menu_code']
                count_ = curr_slot_details['slot_count']
                print(f"processing menu code {menu_code}, current_count {count_}")
                print(f"type for count_ {type(count_)}")

                
                if is_valid_yes_or_no(client_input):
                    print(f"{client_input}, is valid input")
                    Session.save_answer(user_waid, count_, client_input)
                    if client_input == "yes":

                        if Session.complete_reg_slotting(user_waid):
                            message = f"Your registeration using +{user_waid}\n\nfor spendvest is complete,\n\n"
                            Session.load_handler(user_waid, 'st_handler', 'ST',0, 1)
                            existing_customer = MpesaCustomer.get_single_user(user_waid)
                            print(f"existing customer value is : {existing_customer}")
                            
                            if existing_customer:   
                                print(f"customer is existing")
                                Session.clear_answer_slot(user_waid)
                                message = f"This number is already registerd"
                            else:
                                MpesaCustomer.add_mpesa_customer(user_waid)

                            return output_bot_message(message)
                        
                        else:
                            quiz_pack = Menu.load_question_pack(menu_code)
                            quiz = Session.return_current_slot_quiz(user_waid, quiz_pack)
                    
                            Session.step_slotting(user_waid, quiz_pack)
                
                            return output_bot_message(quiz)
 
                    elif client_input == "no":
                        print(f"Customer has cancelled")
                        Session.clear_answer_slot(user_waid)
                        message = f"You have cancelled the registeration process" 
                        Session.load_handler(user_waid, "st_handler", "ST", 1, 1)
                        return output_bot_message(message)
                
                else:
                    print(f"{client_input}, is invalid")
                    message = "Error\n\nThat input was invalid"
                    return output_bot_message(message)
                
            elif current_handler == "sm_handler":
                curr_slot_details = Session.fetch_slot_details(user_waid)          
                menu_code = curr_slot_details['menu_code']
                count_ = curr_slot_details['slot_count']
                print(f"processing menu code {menu_code}, current_count {count_}")
                print(f"type for count_ {type(count_)}")
                count_ = int(count_)

                if count_ == 0 or count_ == 1:
                    print(f"count is eith 0 or 1, {count_}")
                    # process quiz1
                    if is_valid_phone_number(client_input):
                        print(f"{client_input}, is valid")
                    
                        Session.save_answer(user_waid, count_, client_input)
                    
                        if Session.complete_sm_slotting(user_waid):
                            message = f"Your request for Send Money task has been submitted,\n\nPlease wait for Mpesa prompt on +{user_waid}\n\nThen enter your Mpesa PIN\n\nThank you 😊"
                            Session.load_handler(user_waid, 'st_handler', 'ST', 0, 1)
                            Session.clear_answer_slot(user_waid)

                            print(f"user number is : {user_waid}")
                            
                            return output_bot_message(message)
                        else:
                            quiz_pack = Menu.load_question_pack(menu_code)
                            quiz = Session.return_current_slot_quiz(user_waid, quiz_pack)
                    
                            Session.step_slotting(user_waid, quiz_pack)
                    
                    
                        return output_bot_message(quiz)
                    else:
                        print(f"{client_input}, is invalid")
                        message = "Error\n\nThat input was invalid"
                        return output_bot_message(message) 
                     
                elif count_ == 2:
                    print(f"count is 2")
                    if is_valid_payment_amount(client_input):
                        print(f"valid payment number : {client_input}")
                        Session.save_answer(user_waid, count_, client_input)
                        if Session.complete_sm_slotting(user_waid):
                            message = f"Your request for Send Money task has been submitted,\n\nPlease wait for Mpesa prompt on +{user_waid}\n\nThen enter your Mpesa PIN\n\nThank you 😊"
                            Session.load_handler(user_waid, 'st_handler', 'ST', 0, 1)
                            
                            print(f"user number is : {user_waid}")
                            end_number = Session.load_ans_payload(user_waid)
                            end_number = json.loads(end_number)
                            print(f"end_number_list : {end_number}")
                            print(f"end_number to set : {end_number[0]}, of type : {type(end_number[0])}")
                            Session.clear_answer_slot(user_waid)
                            send_user_stk(user_waid, int(client_input),'SM', end_number[0])
                            
                            return output_bot_message(message)
                        else:
                            quiz_pack = Menu.load_question_pack(menu_code)
                            quiz = Session.return_current_slot_quiz(user_waid, quiz_pack)
                    
                            Session.step_slotting(user_waid, quiz_pack)
                            return output_bot_message(quiz)
                    else:
                        print(f"{client_input}, is invalid")
                        message = "Error\n\nThat input was invalid"
                        return output_bot_message(message)  
                 
                    
                

                 
            elif current_handler == "lp_handler":
                pass
               
            elif current_handler == "lbt_handler":
                pass
                
            elif current_handler == "lbp_handler":
                pass           
        else:
            print(f"user is not slot filling")
    else:
        print(f"not first time contact, creating new session")
        
        new_user_session = Session(uid=generate_uid(), 
                           waid=user_waid,
                           name=in_data.get('ProfileName'), 
                           current_menu_code='ST', 
                           answer_payload='[]', 
                           user_flow='',
                           is_slot_filling=0, 
                           current_slot_count=0, 
                           slot_quiz_count=len(Menu.load_question_pack('ST')), 
                           current_slot_handler='st_handler')
        new_user_session.save()
        AccountSummary.add_summary(user_waid)

        # Session.set_slot_filling_on(user_waid)
        Session.set_slot_filling_on(user_waid)
        quiz_pack = Menu.load_question_pack('ST')
        print(f"current quiz pack, {quiz_pack}")
        quiz = Session.return_current_slot_quiz(user_waid, quiz_pack)

        # generaete str for account summary
        generated_summary = get_user_acc_summary_stmt(user_waid, user_name)
        # mix with quiz and return output
        output_message = f"{generated_summary}\n\nMenu:\n\n{quiz}"

        print(f"created session with slot_filling on is , {Session.get_session(user_waid)}")
        return output_bot_message(output_message)
    

def get_user_acc_summary_stmt(waid, user_name):
    acc_dict = AccountSummary.get_acc_summary(waid)
    if acc_dict:
        summary = {
            'total_deposit': acc_dict[b'total_deposit'].decode('utf-8'),
            'pending_settlement': acc_dict[b'pending_settlement'].decode('utf-8'),
            'total_settlement': acc_dict[b'total_settlement'].decode('utf-8'),
            'amount_deposited': acc_dict[b'amount_deposited'].decode('utf-8'),
            'amount_settled': acc_dict[b'amount_settled'].decode('utf-8'),
            'total_amount_saved':acc_dict[b'total_amount_saved'].decode('utf-8'),
            'last_amount_saved':acc_dict[b'last_amount_saved'].decode('utf-8')
        }
        return_string = f"""
=====================================
User: {user_name}

Total Deposit: {summary['total_deposit']}
Pending Settlement: {summary['pending_settlement']}
Total Settlement: {summary['total_settlement']}

Amount Deposited: {summary['amount_deposited']}
Amount Settled: {summary['amount_settled']}

Saving Percentage : 5%
Total Amount Saved: {summary['total_amount_saved']}
Last Amount Saved: {summary['last_amount_saved']}
=====================================
        """
        return return_string.strip()
    else:
        return f"No account summary found for user {user_name}."

def output_bot_message(message):
    resp = MessagingResponse()
    resp.message(message)
    m = str(resp)
    print(f"'returning bot output {m}")
    return str(resp)

def test_message_with_image(message, image_url_list):
    resp = MessagingResponse()
    msg = resp.message()
    
    # Add the text message
    msg.body(message)
    
    # Add each image to the message
    for image_url in image_url_list:
        msg.media(image_url)
    
    m = str(resp)
    print(f"Returning bot output with images: {m}")
    return str(resp)

def is_valid_yes_or_no(reg_ans):
    """Check if the input is 'yes' or 'no' after converting to lowercase."""
    reg_ans = reg_ans.lower()
    return reg_ans in ["yes", "no"] 

def is_valid_phone_number(phone_ans):
    phone_pattern = re.compile(r'^\d{10,15}$')
    return bool(phone_pattern.match(phone_ans))

def is_valid_paybill(paybill_ans):
    paybill_pattern = re.compile(r'^\d{5,10}$')
    return bool(paybill_pattern.match(paybill_ans))

def is_valid_till(till_ans):
    till_pattern = re.compile(r'^\d{5,10}$')
    return bool(till_pattern.match(till_ans))

def is_valid_payment_amount(payment):
    # Define the regex pattern for a valid payment amount
    pattern = r'^[\$\€\£]?\s*-?\d{1,3}(?:[,.\s]?\d{3})*(?:[.,]\d{1,2})?$'

    # Check if the input matches the pattern
    if re.match(pattern, payment):
        return True
    else:
        return False

def convert_phone_number(byte_phone_number):
    # Decode the byte string to a regular string
    phone_number_str = byte_phone_number.decode('utf-8')
    
    # Ensure the phone number starts with '0' before replacing it
    if phone_number_str.startswith('0'):
        phone_number_str = '254' + phone_number_str[1:]
    
    # Convert the resulting string to an integer
    phone_number_int = int(phone_number_str)
    
    return phone_number_int

# mpesa
@app.route("/mpesa_callback", methods=['POST'])
def process_callback():
    # check if is user cancelled also
    # update task as complete if user input pin
    # also update for settlement as complete
    print(f"recieved data is : {request}, and is of type : {type(request)}")

    in_data = request.get_json()
    print(f"recieved callback data is, {in_data}")

    ref = in_data['MerchantRequestID']
    requested_task = RequestTask.get_task(ref)
    print(f"fetched task is : {requested_task}")
    print("\n\n\n")
    requested_settlement = Settlement.get_customer_settlement(ref)
    print(f"fetched settlement is : {requested_settlement}")
    requested_acc_summary = AccountSummary.get_acc_summary(requested_task['customer_waid'])
    print(f"fetched account summary is : {requested_acc_summary}")
    
    if 'MerchantAccountBalance' in in_data.keys():
        # send-payment callback
        # update task and settlemtnt
        
        print(f"send_payment callback")
        Settlement.complete_customer_settlement(ref)
        RequestTask.complete_task(ref)
        # update acc summarys
        pass
    else:
        # send_user_stk : 0 or 1
        # send_payment()
        if in_data['ResultCode'] == '1032':
            print(f"user has cancelled stk push")
        else:
            end_number = requested_settlement['end_settlement_number']
            payment_amount = requested_settlement['amount']
            payment_amount = payment_amount.decode('utf-8')
            print(f"now settling payment")
            end_number = convert_phone_number(end_number)
            print(f"end_number : {end_number}")
            print(f"payment amount : {payment_amount}")
            # update acc summary, for pending settlements,total settlements , amount settlement, total amount saved and last amount saved

            summary_update = {
                'pending_settlement':0,
                'total_settlement': float(requested_acc_summary[b'total_settlement'].decode('utf-8')) + 1,
                'amount_settled' : float(requested_acc_summary[b'amount_settled'].decode('utf-8')) + float(payment_amount),
                'total_amount_saved':float(requested_acc_summary[b'total_amount_saved'].decode('utf-8')) + float(5),
                'last_amount_saved':float(requested_acc_summary[b'total_amount_saved'].decode('utf-8')) + float(5)

            }

            AccountSummary.update_acc_summary(requested_task['customer_waid'], summary_update)

            send_payment(str(end_number), payment_amount)
            
    
    return 'ok'


@app.route("/mpesa_callback_timeout", methods=['POST'])
def process_callback_timeout():
    print(f"recieved callback data is, {request.get_json()}")

    return 'ok'

# landing page
@app.route('/')
def index():
    return 'ok'

if __name__ == "__main__":
    with app.app_context():
        app.run(debug=True, port=80)
