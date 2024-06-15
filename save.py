import flask 
from flask import Flask, jsonify, request

from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse, Message
from twilio.rest import Client
import urllib
import redis
import random
import string 
import time

import re
import json
import telebot
import os 
from dotenv import load_dotenv
from Markup import clear_prev_markup, prompt_input_markup, start_one_markup

load_dotenv()
BOT_TOKEN = os.getenv('telegram_bot_auth_token')


from blu import Session
from models import RequestTask, AccountSummary, Settlement
from payments2 import send_user_stk, send_payment
from models  import Menu, MpesaCustomer
import uuid



# Account SID and Auth Token from www.twilio.com/console
client = Client('TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN')

# Telegram installation
tele_bot = telebot.TeleBot(BOT_TOKEN)

app = Flask(__name__)


def generate_uid(length=10):
    chars = string.ascii_letters  + string.digits
    uid = "".join(random.choice(chars) for _ in range(length))
    return uid

menu_listing = [
    {
    'menu_code':'ACC',
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
    # {
    # 'menu_code':'LBT',
    # 'media':['./static/bot_media/LipaTill.png'],
    # 'menu_message': "Lipa Till menu\n\nProceed by selecting one ofthe buttons",
    # 'menu_button':['Browse', 'Select', 'Cancel']
    # },
    # {
    # 'menu_code':'LBP',
    # 'media':['./static/bot_media/LipaPaybill.png'],
    # 'menu_message': "Lipa Paybill menu\n\nProceed by selecting one ofthe buttons",
    # 'menu_button':['Browse', 'Select', 'Cancel']
    # },
     {
    'menu_code':'ABT',
    'media':['./static/bot_media/About.png'],
    'menu_message': "About menu\n\nProceed by selecting one ofthe buttons",
    'menu_button':['Browse', 'Select', 'Cancel']
    },

]


slot_handlers = ["ru_handler", "sm_handler", "lp_handler", "lbt_handler", "lbp_handler", "start_handler"]


@app.route('/telegram', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        
        # Extract necessary information from the update
        if update.message:
            user_id = update.message.from_user.id
            user_name = update.message.from_user.username
            client_input = update.message.text.lower()

            # Print or process the extracted data
            print(f"User ID: {user_id}, Username: {user_name}, Client Input: {client_input}")

            if Session.is_first_time_contact(user_id):
                pass
            else:
                # Create new session if it's not the first time contact
                new_count = 0
                new_user_session = Session(uid=generate_uid(),
                                           waid=user_id,
                                           name=user_name,
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

                AccountSummary.add_summary(user_id)

                current_count = Session.get_browsing_count(user_id)

                menu_payload = menu_listing[current_count]
                print(f"current menu payload : {menu_payload}")

                menu_media_list = menu_payload['media']
                menu_message = menu_payload['menu_message']
                menu_buttons = menu_payload['menu_button']
                menu_code = menu_payload['menu_code']

                if menu_code == "ACC":
                    print(f"appending account 2 menu_message")

                    acc_summary = get_user_acc_summary_stmt(user_id, user_name)
                    new_message = f"{acc_summary}\n\n{menu_message}"
                    # The length of the bounding box
                    bounding_box_length = len("=====================================")

                    message_test = create_message_with_buttons(user_name, new_message, menu_buttons, bounding_box_length)

                    # Send the message with buttons and media
                    tele_bot.send_message(user_id, message_test)
                    tele_bot.send_media_group(user_id, [telebot.types.InputMediaDocument(media) for media in menu_media_list])

        # Process the update
        tele_bot.process_new_updates([update])
        return ''
    
    else:
        flask.abort(403)

#defining command handlers
# Define command handlers
@tele_bot.message_handler(commands=['start', 'help'])
def starter(message):
    tele_bot.send_chat_action(message.chat.id, 'typing')
    tele_bot.send_message(message.chat.id, "Sure!", reply_markup=clear_prev_markup())
    local_host = f'{os.getcwd()}/static/bot_media/Account.png'
    img = open(local_host, 'rb')
    tele_bot.send_document(message.chat.id, data=img)
    tele_bot.send_message(message.chat.id, "What would you like to do?", reply_markup=start_one_markup())


@tele_bot.message_handler(func=lambda message: True)
def echo_all(message):
    tele_bot.reply_to(message, message.text)


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
Last Amount Saved: {summary['last_amount_saved']}
Total Amount Saved: {summary['total_amount_saved']}
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
        tele_bot.set_webhook(url="https://ffb5-154-127-6-35.ngrok-free.app/telegram")
        app.run(debug=True, port=1000)
