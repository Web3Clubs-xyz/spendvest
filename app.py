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

menu_listing = [
    {
    'menu_code':'Acc',
    'media':['./static/bot_media/Account.png'],
    'menu_message': "Account menu\n\nProceed by selecting one ofthe buttons",
    'menu_button':['Browse', 'Select', 'Cancel']
    },
    {
    'menu_code':'SM',
    'media':['./static/bot_media/SendMoney.png'],
    'menu_message': "Send Money menu\n\nProceed by selecting one ofthe buttons",
    'menu_button':['Browse', 'Select', 'Cancel']
    },
    {
    'menu_code':'LBT',
    'media':['./static/bot_media/LipaTill.png'],
    'menu_message': "Lipa Till menu\n\nProceed by selecting one ofthe buttons",
    'menu_button':['Browse', 'Select', 'Cancel']
    },
    {
    'menu_code':'LBP',
    'media':['./static/bot_media/LipaPaybill.png'],
    'menu_message': "Lipa Paybill menu\n\nProceed by selecting one ofthe buttons",
    'menu_button':['Browse', 'Select', 'Cancel']
    },
     {
    'menu_code':'Abt',
    'media':['./static/bot_media/About.png'],
    'menu_message': "About menu\n\nProceed by selecting one ofthe buttons",
    'menu_button':['Browse', 'Select', 'Cancel']
    },

]

@app.route("/whatsapp", methods=["POST"])
def web_hook():
    in_data = request.values 
    user_waid = in_data.get('WaId')
    user_name = in_data.get('ProfileName')
    client_input = in_data.get('Body').lower()

    print(f"incoming payload is , {in_data}")

    if Session.is_first_time_contact(user_waid):

        if Session.is_main_browsing_main(user_waid):
            if client_input in ['browse', 'select', 'cancel']:
                if client_input == "browse":
                    return output_bot_message(f"you selected : {client_input}")
                elif client_input == "select":
                    return output_bot_message(f"you selected : {client_input}")
                else:
                    return output_bot_message(f"you selected : {client_input}")
                 
            else:
                message = "please use the selection suggested above"
                return output_bot_message(message)
        else:
            pass 
        current_count = Session.get_browsing_cout(user_waid)
        menu_payload = menu_listing[current_count]
        print(f"current menu payload : {menu_payload}")
        menu_media_list = menu_payload['media']
        menu_message = menu_payload['menu_message']
        menu_buttons = menu_payload['menu_button']
        
        # The length of the bounding box
        bounding_box_length = len("=====================================")

        # Generate the message with centered buttons
        message_test = create_message_with_buttons(user_name, menu_message, menu_buttons, bounding_box_length)

        # Return the final message with images
        return test_message_with_image(message_test, menu_media_list)
    
        
    else:
        print("new user to create session")
        new_count = 0
        new_user_session = Session(uid=generate_uid(), 
                           waid=user_waid,
                           name=in_data.get('ProfileName'), 
                           current_menu_code='ST', 
                           answer_payload='[]', 
                           user_flow='',

                           main_menu_browsing=1,
                           sub_menu_browsing=0,
                           browsing_count=new_count,

                           is_slot_filling=0, 
                           current_slot_count=0, 
                           slot_quiz_count=len(Menu.load_question_pack('ST')), 
                           current_slot_handler='st_handler')
        new_user_session.save()
        AccountSummary.add_summary(user_waid)
        
        current_count = Session.get_browsing_cout(user_waid)
        menu_payload = menu_listing[current_count]
        print(f"current menu payload : {menu_payload}")
        menu_media_list = menu_payload['media']
        menu_message = menu_payload['menu_message']
        menu_buttons = menu_payload['menu_button']
        
        # The length of the bounding box
        bounding_box_length = len("=====================================")

        # Generate the message with centered buttons
        message_test = create_message_with_buttons(user_name, menu_message, menu_buttons, bounding_box_length)

        # Return the final message with images
        return test_message_with_image(message_test, menu_media_list)
    
         

     


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


def generate_centered_buttons_text(buttons, bounding_box_length):
    # Function to center text within a given width
    def center_text(text, width):
        padding = (width - len(text)) // 2
        return " " * padding + text + " " * (width - len(text) - padding)

    # Generate the centered text for each button
    centered_buttons = [center_text(button, bounding_box_length) for button in buttons]
    
    # Join the centered buttons with newlines
    return "\n".join(centered_buttons)

def create_message_with_buttons(user_name, menu_message, menu_buttons, bounding_box_length):
    # Concatenate buttons with ' || ' separator
    buttons_text = " || ".join(menu_buttons)
    
    # Calculate the padding needed to center the text
    padding = (bounding_box_length - len(buttons_text)) // 2
    
    # Generate the centered buttons text with padding
    centered_buttons_text = " " * padding + buttons_text + " " * (bounding_box_length - len(buttons_text) - padding)
    
    # Construct the full message
    message_test = f"""
{user_name}

{menu_message}:

{"=" * bounding_box_length}
            {centered_buttons_text}
{"=" * bounding_box_length}
"""
    return message_test

def output_bot_message(message):
    resp = MessagingResponse()
    resp.message(message)
    m = str(resp)
    print(f"returning bot output {m}")
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

def show_acc_main_message(menu_code):
    pass 

def show_acc_wallet_message():
    pass 

def show_sm_message():
    pass 


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
        app.run(debug=True, port=1000)
