import os
from flask import Flask, request
import telebot
from dotenv import load_dotenv
from blu import Session
import string 
import random
import time 
from models import RequestTask, AccountSummary, Settlement
from payments2 import send_user_stk, send_payment
from models  import Menu, MpesaCustomer
import uuid
from Markup import clear_prev_markup, main_markup
import re 


# Load environment variables from .env file
load_dotenv()

# Retrieve Telegram bot token from environment variable
BOT_TOKEN = os.getenv('telegram_bot_auth_token')

# Initialize Flask app
app = Flask(__name__)

# Initialize Telegram bot
tele_bot = telebot.TeleBot(BOT_TOKEN)

def listener(messages):
    """Whenever a message arrives for the blu bot (forwarded), Telebot will call this method"""
    for message in messages:
        if message.content_type == 'text':
            print(f"{message.chat.first_name} [{message.chat.id}]: {message.text}")


tele_bot.set_update_listener(listener)


def generate_uid(length=10):
    chars = string.ascii_letters  + string.digits
    uid = "".join(random.choice(chars) for _ in range(length))
    return uid

# Sample menu listing
main_menu_listing = [
    {
        'menu_code': 'ACC',
        'media': ['https://ibb.co/TPByKzF'],
        'menu_message': "Account menu\n\nProceed by selecting one of the buttons",
        'menu_sticker':'CAACAgIAAxkBAANzZmxCgEYuHF3IpoGd7NFQCENjHO8AAjY_AAL8N0hJftW8yfivq4Y1BA'
    },
    {
        'menu_code': 'SM',
        'media': ['https://ibb.co/b1wCMxd'],
        'menu_message': "Send Money menu\n\nProceed by selecting one of the buttons",
        'menu_sticker':'CAACAgIAAxkBAAIBZGZs9KXiH_ZL4fk3xaFKQDZt5cJHAALDPQACzBMpSoUPzZoaigNGNQQ'
    },
    {
        'menu_code': 'ABT',
        'media': ['https://ibb.co/mH3qLVL'],
        'menu_message': "About menu\n\nProceed by selecting one of the buttons",
        'menu_sticker':'CAACAgIAAxkBAAIBYGZs9Evmq29uftu5IIEYYavi5YSGAAJHOQACXlZxSlYd7J-sP8XeNQQ'
    },  
]


@tele_bot.message_handler(commands=['test1'])
def test1(message):
    # Send a typing action to indicate that the bot is processing
    tele_bot.send_chat_action(message.chat.id, 'typing')
    sticker_id = "CAACAgIAAxkBAANzZmxCgEYuHF3IpoGd7NFQCENjHO8AAjY_AAL8N0hJftW8yfivq4Y1BA"
    tele_bot.send_sticker(message.chat.id,sticker_id)
    # Define the link to the image
    image_link = 'https://i.ibb.co/ck8CxYG/Spend-Vest.png'  # Replace this with your actual image URL
    # Send a message with the link to the image
    tele_bot.send_message(message.chat.id, f"Here is the image you requested: {image_link}")


@tele_bot.message_handler(content_types=['sticker'])
def handle_sticker(message):
    # Retrieve the sticker file ID
    sticker_file_id = message.sticker.file_id
    
    # Log or print the sticker file ID for reference
    print(f"Received sticker with file ID: {sticker_file_id}")
    
    # Send a response message acknowledging the sticker
    tele_bot.send_message(message.chat.id, "Nice sticker! Thanks for sharing.")
    
    # Optionally, you can also send a sticker back to the user
    # Here, replace 'CAADAgADQAADyIsGAAE7MpzFPFQX7QI' with the file ID of the sticker you want to send
    response_sticker_file_id = sticker_file_id
    tele_bot.send_sticker(message.chat.id, response_sticker_file_id)


@app.route('/telegram', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)

        # Process the update only once
        tele_bot.process_new_updates([update])

        # Extract necessary information from the update
        if update.message:
            user_id = update.message.from_user.id
            user_name = update.message.from_user.username
            client_input = update.message.text.lower() if update.message.text else ''

            # Print or process the extracted data
            print(f"User ID: {user_id}, Username: {user_name}, Client Input: {client_input}")

            if Session.is_first_time_contact(user_id):
                print(f"is continuing user ")
                if int(Session.is_main_browsing(user_id))==1:
                    if client_input in ['browse', 'select', 'cancel']:
                        if client_input == "browse":
                            Session.browse_main(user_id)

                            current_count = Session.get_browsing_count(user_id)
                            menu_payload = main_menu_listing[current_count]
                            print(f"current payload after reseting \n\n {menu_payload}")
                            # Send the message with buttons and media

                            tele_bot.send_chat_action(update.message.chat.id, 'typing')
                            sticker_file_id = menu_payload['menu_sticker']
                            image_link = menu_payload['media'][0]

                            tele_bot.send_sticker(update.message.chat.id, sticker_file_id)
                            tele_bot.send_photo(update.message.chat.id, image_link)
                            tele_bot.send_message(user_id, f"{menu_payload['menu_message']}", main_markup())

                            return 'ok'

                        elif client_input == "select":
                            input_message = f"you selected {client_input}"
                            tele_bot.send_message(update.message.chat.id, input_message)
                            return 'ok' 
                        else:
                            Session.reset_browsing_count(user_id)
                            current_count = Session.get_browsing_count(user_id)
                            menu_payload = main_menu_listing[current_count]
                            print(f"current payload after reseting \n\n {menu_payload}")
                            # Send the message with buttons and media

                            tele_bot.send_chat_action(update.message.chat.id, 'typing')
                            sticker_file_id = menu_payload['menu_sticker']
                            image_link = menu_payload['media'][0]

                            tele_bot.send_sticker(update.message.chat.id, sticker_file_id)
                            tele_bot.send_photo(update.message.chat.id, image_link)
                            tele_bot.send_message(user_id, f"{menu_payload['menu_message']}", main_markup())
                            return 'ok'
                    else:
                        return_message = "please use the buttons to navigate"
                        tele_bot.send_message(update.message.chat.id, return_message) 
                else:
                    pass 
            else:
                print(f"is user first time, creating session")
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

                menu_payload = main_menu_listing[current_count]
                print(f"current menu payload : {menu_payload}\n\n")

                menu_message = menu_payload['menu_message']
                menu_code = menu_payload['menu_code']

                if menu_code == "ACC":
                    print(f"appending account 2 menu_message")

                    acc_summary = get_user_acc_summary_stmt(user_id, user_name)
                    new_message = f"{acc_summary}\n\n{menu_message}"
                    print(f"printing menu message : {menu_message}")
                    
                    # Send the message with buttons and media
                    tele_bot.send_chat_action(update.message.chat.id, 'typing')
                    sticker_file_id = menu_payload['menu_sticker']
                    image_link = menu_payload['media'][0]

                    tele_bot.send_sticker(update.message.chat.id, sticker_file_id)
                    tele_bot.send_photo(update.message.chat.id, image_link)
                    tele_bot.send_message(user_id, f"{menu_message}", main_markup())
                                        
        return ''
    
    else:
        return 'Invalid request', 403



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


if __name__ == '__main__':
    with app.app_context():
        time.sleep(0.5)
        tele_bot.set_webhook(url="https://ffb5-154-127-6-35.ngrok-free.app/telegram")

    app.run(debug=True, port=1000)
