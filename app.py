import os
from flask import Flask, request, jsonify
import aiohttp
import asyncio
from dotenv import load_dotenv
from pprint import pprint
import string
import random

from blu import Session 
from models import SlotQuestion, AccountSummary, MpesaCustomer
import re

# Load environment variables from .env file
load_dotenv()

# Retrieve environment variables
GRAPH_API_TOKEN = os.getenv('GRAPH_API_TOKEN', "EAAUCpth1wAIBO8i1GmGZAElpMJZCCktMlWCluXT7eStoGO2Y9bouTyZCOuwZBieBgItlTnomMPl1tplmLaj9vjbkT1fKHaaowL7wjtghJza1TjnsYGAHbdY8HoVT50gTKjUlSLry8NCltchuk45YaSb1BLZBgCjzEZCXKfsRk6XwjbfMWtlVupqLZBjuZBEOPONnRPyMPxZBLbf2CqcaiUZCswQtNZAkWEZD")
WEBHOOK_VERIFY_TOKEN = os.getenv('WEBHOOK_VERIFY_TOKEN', "123456")
PORT = int(os.getenv('PORT', 1000))
WHATSAPP_API_URL = 'https://graph.facebook.com/v18.0'

# Initialize Flask app
app = Flask(__name__)

def generate_uid(length=10):
    chars = string.ascii_letters  + string.digits
    uid = "".join(random.choice(chars) for _ in range(length))
    return uid

def determine_message_update(data):
    try:
        # Extract changes from the webhook data
        changes = data['entry'][0]['changes'][0]['value']

        if 'messages' in changes:
            message = changes['messages'][0]
            message_type = message['type']

            # Check the type of the message
            if message_type == 'text':
                user_message = message['text']['body']
                user_waid = message['from']
                message_id = message['id']
                user_name = changes['contacts'][0]['profile']['name']
                business_phone_number_id = changes['metadata']['phone_number_id']

                print(f"Regular text message from {user_name} (ID: {user_waid}): {user_message}")
                return {
                    "type": "text",
                    "user_name": user_name,
                    "user_waid": user_waid,
                    "message_id": message_id,
                    "user_message": user_message,
                    "business_phone_number_id": business_phone_number_id
                }

            elif message_type == 'interactive':
                if message['interactive']['type'] == 'button_reply':
                    button_reply = message['interactive']['button_reply']
                    user_waid = message['from']
                    user_name = changes['contacts'][0]['profile']['name']
                    business_phone_number_id = changes['metadata']['phone_number_id']

                    print(f"Button reply from {user_name} (ID: {user_waid}): {button_reply}")
                    return {
                        "type": "button_reply",
                        "user_name": user_name,
                        "user_waid": user_waid,
                        "button_reply": button_reply,
                        "business_phone_number_id": business_phone_number_id
                    }

        elif 'statuses' in changes:
            status = changes['statuses'][0]
            status_type = status['status']
            recipient_id = status['recipient_id']
            timestamp = status['timestamp']

            print(f"Message status {status_type} for recipient {recipient_id} at {timestamp}")
            return {
                "type": "status",
                "status": status_type,
                "recipient_id": recipient_id,
                "timestamp": timestamp
            }

        else:
            print("No messages or statuses found in the webhook data.")
            return {"type": "none"}

    except KeyError as e:
        print(f"Key error: {e}")
        return {"error": "Invalid message format"}


@app.route('/webhook', methods=['POST'])
async def webhook():
    data = request.json
    message_info = determine_message_update(data)

    if message_info.get("error"):
        return jsonify({"error": "Invalid message format"}), 400

    message_type = message_info['type']

    if message_type == 'text':
        user_name = message_info['user_name']
        user_waid = message_info['user_waid']
        user_message = message_info['user_message']
        message_id = message_info['message_id']
        business_phone_number_id = message_info['business_phone_number_id']

        print(f"\n\nUser Name: {user_name}, User ID: {user_waid}, Client Input: {user_message}, Message ID: {message_id}, Business_phone_number_id: {business_phone_number_id}\n\n")

        if Session.is_first_time_contact(user_waid):
            print(f"Continuing user, waid: {user_waid}")
            if Session.is_main_menu_nav(user_waid) == '1':
                print(f"User is in main menu navigation")
                current_select = Session.get_main_menu_select(user_waid)
                print(f"current_select : {current_select}, for input : {user_message}")

                if current_select == "main_menu_select_home":
                    if MpesaCustomer.get_user_reg_status(user_waid):
                        print(f"Registered Mpesa user")
                        await send_mainmenu_reg_interactive_template(True, business_phone_number_id, user_waid, user_message, message_id)
                    else:
                        print(f"Unregistered Mpesa user")
                        await send_mainmenu_reg_interactive_template(False, business_phone_number_id, user_waid, user_message, message_id)

                    
                
            elif Session.is_sub1_menu_nav(user_waid) == '1':
                print(f"User is in sub1 menu navigation")
                current_message_input = user_message
                current_select = Session.get_sub1_menu_select(user_waid)
                print(f"Current select is: {current_select}")

                if current_select == "sub1_menu_select_about":
                    print(f"showing about template")
                    await send_sub1menu_about_interactive_template(business_phone_number_id, user_waid, user_message, message_id)
                 
                pass
            elif Session.is_sub2_menu_nav(user_waid) == '1':
                print(f"User is in sub2 menu navigation")
                pass
            else:
                print("User could be slot filling")
                print(f"user selected : {user_message}")
                #
                slot_details = Session.fetch_slot_details(user_waid)
                print(f"fetched slot details, {slot_details}")
                handler = slot_details['slot_handler']
                current_count_ = slot_details['slot_count']
                
                if  handler == "ru_handler":
                    
                    if current_count_ == '0': 
                        print(f"processing {handler}, with count {current_count_}")
                        user_input = user_message
                        if verify_is_yes(user_input):
                            # record
                            Session.save_reg_answer(user_waid,current_count_, user_input)
                            # update counter
                            # get question pack
                            quiz_pack = SlotQuestion.get_question_pack('RU')
                            print(f"fetched quiz_pack, {quiz_pack}")
                            # get first quiz
                            quiz = quiz_pack[str(int(current_count_) + 1)]
                            # ++ slotfilling
                            Session.step_slotting(user_waid, quiz_pack)
                            # send quiz
                            await send_slot_quiz_interactive_template(business_phone_number_id,user_waid,quiz,message_id)
                             
                        else:
                            error_message = "Please enter answer as instructed"
                            await send_slot_quiz_interactive_template(business_phone_number_id, user_waid, error_message, message_id)
                        
                    if current_count_ == '1': 
                        print(f"processing {handler}, with count {current_count_}")
                        user_input = user_message
                        if verify_is_yes(user_input):
                            # record
                            Session.save_reg_answer(user_waid,current_count_, user_input)
                            # update counter
                            # get question pack
                            quiz_pack = SlotQuestion.get_question_pack('RU')
                            print(f"fetched quiz_pack, {quiz_pack}")
                            # get first quiz
                            end_process_message = "Youre account has been succesfully registerd!"
                            MpesaCustomer.add_mpesa_customer(user_waid, user_waid)
                            Session.clear_answer_slot(user_waid)
                            Session.off_slot_filling(user_waid)
                            Session.on_main_menu_nav(user_waid, "main_menu_select_home")
                            # ++ slotfilling
                            # Session.step_slotting(user_waid, quiz_pack)
                            # send quiz
                            await send_slot_quiz_interactive_template(business_phone_number_id,user_waid,end_process_message,message_id)
                             
                        else:
                            error_message = "Please enter answer as instructed"
                            await send_slot_quiz_interactive_template(business_phone_number_id, user_waid, error_message, message_id)
                            
                    
                    

                

                
        else:
            print("New user, first time contact, creating session")
            new_user_session = Session(
                uid=generate_uid(),
                waid=user_waid,
                name=user_name,
                main_menu_nav=1,
                main_menu_select='main_menu_select_home',
                sub1_menu_nav=0,
                sub1_menu_select='',
                sub2_menu_nav=0,
                sub2_menu_select='',
                is_slot_filling=0,
                answer_payload='[]',
                current_slot_count=0,
                current_slot_code='',
                slot_quiz_count=0,
                current_slot_handler=''
            )

            print(f"Session object definition, user_name: {new_user_session.name}")
            new_user_session.save()

            # Set account summary
            AccountSummary.add_summary(user_waid)

            # Show unregistered landing
            await send_mainmenu_reg_interactive_template(False, business_phone_number_id, user_waid, user_message, message_id)

    elif message_type == 'button_reply':
        user_message=''
        message_id=''
        user_name = message_info['user_name']
        user_waid = message_info['user_waid']
        button_reply = message_info['button_reply']
        business_phone_number_id = message_info['business_phone_number_id']

        print(f"\n\nUser Name: {user_name}, User ID: {user_waid}, Button Reply: {button_reply}, Business_phone_number_id: {business_phone_number_id}\n\n")
        # Handle button reply logic here
        if button_reply['id'] == "main_menu_about_button":
            # update main_menu_select
            Session.off_main_menu_nav(user_waid)
            Session.on_sub1_menu_nav(user_waid,"sub1_menu_select_about")
            await send_sub1menu_about_interactive_template(business_phone_number_id, user_waid, user_message, message_id)

        if button_reply['id'] == "sub1_menu_about_done_button":
            Session.off_sub1_menu_nav(user_waid)
            Session.on_main_menu_nav(user_waid, "main_menu_select_home")
            if MpesaCustomer.get_user_reg_status(user_waid):
                    print(f"Registered Mpesa user")
                    await send_mainmenu_reg_interactive_template(True, business_phone_number_id, user_waid, user_message, message_id)
            else:
                    print(f"Unregistered Mpesa user")
                    await send_mainmenu_reg_interactive_template(False, business_phone_number_id, user_waid, user_message, message_id)

        if button_reply['id'] == "main_menu_account_button":
            Session.off_main_menu_nav(user_waid)
            Session.on_sub1_menu_nav(user_waid, "sub1_menu_select_acc")
            if MpesaCustomer.get_user_reg_status(user_waid):
                print(f"Registered Mpesa user")
                await send_sub1menu_acc_interactive_template(True, business_phone_number_id, user_waid, user_message, message_id)
            else:
                print(f"Unregisterd Mpesa user")
                await send_sub1menu_acc_interactive_template(False, business_phone_number_id, user_waid, user_message, message_id)
        
        if button_reply['id'] == "sub1_menu_acc_cancel_button":
            Session.off_sub1_menu_nav(user_waid)
            Session.on_main_menu_nav(user_waid,"main_menu_select_home")
            if MpesaCustomer.get_user_reg_status(user_waid):
                    print(f"Registered Mpesa user")
                    await send_mainmenu_reg_interactive_template(True, business_phone_number_id, user_waid, user_message, message_id)
            else:
                    print(f"Unregistered Mpesa user")
                    await send_mainmenu_reg_interactive_template(False, business_phone_number_id, user_waid, user_message, message_id)
        
        if button_reply['id'] == "sub1_menu_acc_reg_button":
            Session.off_sub1_menu_nav(user_waid)
            Session.on_sub2_menu_nav(user_waid,"sub2_menu_select_register")
            await send_sub2menu_register_interactive_template(business_phone_number_id,user_waid,user_message, message_id)
        
        if button_reply['id'] == "sub2_menu_reg_cancel_button":
            Session.off_sub2_menu_nav(user_waid)
            Session.on_sub1_menu_nav(user_waid, "sub1_menu_select_acc")
            if MpesaCustomer.get_user_reg_status(user_waid):
                print(f"Registered Mpesa user")
                await send_sub1menu_acc_interactive_template(True, business_phone_number_id, user_waid, user_message, message_id)
            else:
                print(f"Unregisterd Mpesa user")
                await send_sub1menu_acc_interactive_template(False, business_phone_number_id, user_waid, user_message, message_id)
        
        if button_reply['id'] =="sub2_menu_reg_proceed_button":
            print(f"About to start Reg Slotfilling")
            # off sub2_main_nav
            Session.off_sub2_menu_nav(user_waid)
            # on slotfilling with the slot_handler,slot_code
            Session.set_slot_filling_on(user_waid)
            Session.load_handler(user_waid, 'ru_handler', "RU",0,2)
             
            # get first question
            slot_details = Session.fetch_slot_details(user_waid)
            print(f"fetched slot details, {slot_details}")
            # get question pack
            quiz_pack = SlotQuestion.get_question_pack('RU')
            print(f"fetched quiz_pack, {quiz_pack}")
            # get first quiz
            quiz = quiz_pack[slot_details['slot_count']]
            # ++ slotfilling
            # Session.step_slotting(user_waid, quiz_pack)
            # send quiz
            await send_slot_quiz_interactive_template(business_phone_number_id,user_waid,quiz,message_id)

        if button_reply['id'] =="slot_filling_cancel_button":
            # set slotfilling off
            Session.off_slot_filling(user_waid)
            # clean answer payload
            Session.clear_answer_slot(user_waid)
            # return back to menu sub2_menu_select_reg
            Session.off_sub1_menu_nav(user_waid)
            Session.on_sub2_menu_nav(user_waid,"sub2_menu_select_register")
            await send_sub2menu_register_interactive_template(business_phone_number_id,user_waid,user_message, message_id)
        
             

        if button_reply['id'] == "main_menu_spend_button":
            pass 
        

    elif message_type == 'status':
        status = message_info['status']
        recipient_id = message_info['recipient_id']
        timestamp = message_info['timestamp']

        print(f"\n\nMessage status: {status} for recipient ID: {recipient_id} at {timestamp}\n\n")

    return jsonify({"status": "received"}), 200



media_map = {
    'SpendMedia.png': '821648629635070', 
    'Save%Media.png': '515551787710292', 
    'WithdrawMedia.png': '1452073195670175', 
    'LandingMedia0.png': '1176661470344662', 
    'RegisterationMedia.png': '401341472927044', 
    'StatusSuccessMedia.png': '7784914981555724', 
    'SendMoneyMedia.png': '335593469597823', 
    'StatusErrorMedia.png': '3678408332488408', 
    'AccountMedia.png': '707545534817088', 
    'AboutMedia.png': '445867451661198'
    }

def verify_is_yes(input):
    pattern = re.compile(r'^yes$', re.IGNORECASE)
    return bool(pattern.match(input))


async def send_mainmenu_reg_interactive_template(reg_status, business_phone_number_id, to, message, reply_message_id):
    headers = {
        "Content-Type":"application/json",
        "Authorization":f"Bearer {GRAPH_API_TOKEN}"
    }

    button_set = [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "main_menu_account_button",
                            "title": "Account"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "main_menu_about_button",
                            "title": "About"
                        }
                    }
                ]
    
    if reg_status == True:
        button_set.insert(1,{
                        "type": "reply",
                        "reply": {
                            "id": "main_menu_spend_button",
                            "title": "Spend"
                        }
                    })

    data = {
        "messaging_product":"whatsapp",
        "to":to,
        "type":"interactive",
        "interactive":{
            "type":"button",
            "header":{
                "type": "image",
                "image": {
                    "id": f"{media_map['LandingMedia0.png']}"
                }
            },
            "body":{
                "text":"Welcome to SpendVest, your savings bot"
            },
            "footer":{
                "text":"Choose an option below"
            },
            "action" : {
                 "buttons": button_set
            }

        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{WHATSAPP_API_URL}/{business_phone_number_id}/messages", headers=headers, json=data) as response:
            if response.status == 200:
                print("Message sent successfully")
            else:
                print(f"Failed to send message: {response.status}")
                print(await response.text())



async def send_sub1menu_about_interactive_template(business_phone_number_id, to, message, reply_message_id):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GRAPH_API_TOKEN}"
    }

    button_set = [
        {
            "type": "reply",
            "reply": {
                "id": "sub1_menu_about_done_button",
                "title": "Done"
            }
        }
    ]

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {
                "type": "image",
                "image": {
                    "id": f"{media_map['AboutMedia.png']}"
                }
            },
            "body": {
                "text": "Learn more about SpendVest and how it can help you save."
            },
            "footer": {
                "text": "Choose an option below"
            },
            "action": {
                "buttons": button_set
            }
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{WHATSAPP_API_URL}/{business_phone_number_id}/messages", headers=headers, json=data) as response:
            if response.status == 200:
                print("Message sent successfully")
            else:
                print(f"Failed to send message: {response.status}")
                print(await response.text())


async def send_sub1menu_acc_interactive_template(reg_status,business_phone_number_id, to, message, reply_message_id):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GRAPH_API_TOKEN}"
    }

    button_set = [
        {
            "type": "reply",
            "reply": {
                "id": "sub1_menu_acc_reg_button",
                "title": "Register Mpesa"
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": "sub1_menu_acc_cancel_button",
                "title": "Cancel"
            }
        }
    ]

    if reg_status == True:
        button_set = [
        {
            "type": "reply",
            "reply": {
                "id": "sub1_menu_acc_save_button",
                "title": "Save %"
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": "sub1_menu_acc_withdraw_button",
                "title": "Withdraw To Mpesa"
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": "sub1_menu_acc_cancel_button",
                "title": "Cancel"
            }
        }
    ]

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {
                "type": "image",
                "image": {
                    "id": f"{media_map['AccountMedia.png']}"
                }
            },
            "body": {
                "text": "Learn more about SpendVest and how it can help you save."
            },
            "footer": {
                "text": "Choose an option below"
            },
            "action": {
                "buttons": button_set
            }
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{WHATSAPP_API_URL}/{business_phone_number_id}/messages", headers=headers, json=data) as response:
            if response.status == 200:
                print("Message sent successfully")
            else:
                print(f"Failed to send message: {response.status}")
                print(await response.text())
 

async def send_sub2menu_register_interactive_template(business_phone_number_id, to, message, reply_message_id):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GRAPH_API_TOKEN}"
    }

    button_set = [
        {
            "type": "reply",
            "reply": {
                "id": "sub2_menu_reg_proceed_button",
                "title": "Proceed"
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": "sub2_menu_reg_cancel_button",
                "title": "Cancel"
            }
        }
    ]

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {
                "type": "image",
                "image": {
                    "id": f"{media_map['RegisterationMedia.png']}"
                }
            },
            "body": {
                "text": "Learn more about SpendVest and how it can help you save."
            },
            "footer": {
                "text": "Choose an option below"
            },
            "action": {
                "buttons": button_set
            }
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{WHATSAPP_API_URL}/{business_phone_number_id}/messages", headers=headers, json=data) as response:
            if response.status == 200:
                print("Message sent successfully")
            else:
                print(f"Failed to send message: {response.status}")
                print(await response.text())
 

async def send_sub2menu_save_interactive_template(business_phone_number_id, to, message, reply_message_id):
    headers = {
        "Content-Type":"application/json",
        "Authorization":f"Bearer {GRAPH_API_TOKEN}"
    }

    button_set = [
        {
            "type": "reply",
            "reply": {
                "id": "sub2_menu_save%_proceed_button",
                "title": "Proceed"
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": "sub2_menu_save%_cancel_button",
                "title": "Cancel"
            }
        }
    ]

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {
                "type": "image",
                "image": {
                    "id": f"{media_map['Save%Media.png']}"
                }
            },
            "body": {
                "text": f"{message}"
            },
            "footer": {
                "text": "To proceed choose an option below"
            },
            "action": {
                "buttons": button_set
            }
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{WHATSAPP_API_URL}/{business_phone_number_id}/messages", headers=headers, json=data) as response:
            if response.status == 200:
                print("Message sent successfully")
            else:
                print(f"Failed to send message: {response.status}")
                print(await response.text())
     

async def send_sub2menu_withdraw_interactive_template(business_phone_number_id, to, message, reply_message_id):
    headers = {
        "Content-Type":"application/json",
        "Authorization":f"Bearer {GRAPH_API_TOKEN}"
    }

    button_set = [
        {
            "type": "reply",
            "reply": {
                "id": "sub2_menu_withdraw_proceed_button",
                "title": "Proceed"
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": "sub2_menu_withdraw_cancel_button",
                "title": "Cancel"
            }
        }
    ]

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {
                "type": "image",
                "image": {
                    "id": f"{media_map['WithdrawMedia.png']}"
                }
            },
            "body": {
                "text": f"{message}"
            },
            "footer": {
                "text": "To withdraw chose the buttons below"
            },
            "action": {
                "buttons": button_set
            }
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{WHATSAPP_API_URL}/{business_phone_number_id}/messages", headers=headers, json=data) as response:
            if response.status == 200:
                print("Message sent successfully")
            else:
                print(f"Failed to send message: {response.status}")
                print(await response.text())
     


async def send_sub1menu_spend_interactive_template(reg_status,business_phone_number_id, to, message, reply_message_id):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GRAPH_API_TOKEN}"
    }

    button_set = [
        
    ]

    if reg_status == True:
        button_set = [
        {
            "type": "reply",
            "reply": {
                "id": "sub1_menu_send_sendmoney_button",
                "title": "Send Money"
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": "sub1_menu_send_cancel_button",
                "title": "Cancel"
            }
        }
    ]
    
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {
                "type": "image",
                "image": {
                    "id": f"{media_map['SpendMedia.png']}"
                }
            },
            "body": {
                "text": "Learn more about SpendVest and how it can help you save."
            },
            "footer": {
                "text": "Choose an option below"
            },
            "action": {
                "buttons": button_set
            }
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{WHATSAPP_API_URL}/{business_phone_number_id}/messages", headers=headers, json=data) as response:
            if response.status == 200:
                print("Message sent successfully")
            else:
                print(f"Failed to send message: {response.status}")
                print(await response.text())
    pass

async def send_sub2menu_sendmoney_interactive_template(business_phone_number_id, to, message, reply_message_id):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GRAPH_API_TOKEN}"
    }

    button_set = [
        {
            "type": "reply",
            "reply": {
                "id": "sub2_menu_sendmoney_proceed_button",
                "title": "Proceed"
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": "sub2_menu_sendmoney_cancel_button",
                "title": "Cancel"
            }
        }
    ]

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {
                "type": "image",
                "image": {
                    "id": f"{media_map['SendMoneyMedia.png']}"
                }
            },
            "body": {
                "text": "Send money and save it while at it"
            },
            "footer": {
                "text": "Choose an option below"
            },
            "action": {
                "buttons": button_set
            }
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{WHATSAPP_API_URL}/{business_phone_number_id}/messages", headers=headers, json=data) as response:
            if response.status == 200:
                print("Message sent successfully")
            else:
                print(f"Failed to send message: {response.status}")
                print(await response.text())
    

async def send_slot_quiz_interactive_template(business_phone_number_id, to, message, reply_message_id):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GRAPH_API_TOKEN}"
    }

    button_set = [
        {
            "type": "reply",
            "reply": {
                "id": "slot_filling_cancel_button",
                "title": "Cancel"
            }
        }
    ]

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            # "header": {
            #     "type": "image",
            #     "image": {
            #         "id": f"{media_map['AboutMedia.png']}"
            #     }
            # },
            "body": {
                "text": f"{message}"
            },
            "footer": {
                "text": "To cancel choose an option below"
            },
            "action": {
                "buttons": button_set
            }
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{WHATSAPP_API_URL}/{business_phone_number_id}/messages", headers=headers, json=data) as response:
            if response.status == 200:
                print("Message sent successfully")
            else:
                print(f"Failed to send message: {response.status}")
                print(await response.text())

     



async def send_status_congrats_interactive_template(business_phone_number_id, to, message, reply_message_id):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GRAPH_API_TOKEN}"
    }

    button_set = [
        {
            "type": "reply",
            "reply": {
                "id": "status_congrats_done_button",
                "title": "Done"
            }
        }
    ]

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {
                "type": "image",
                "image": {
                    "id": f"{media_map['StatusSuccessMedia.png']}"
                }
            },
            "body": {
                "text": f"{message}"
            },
            "footer": {
                "text": "To proceed choose an option below"
            },
            "action": {
                "buttons": button_set
            }
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{WHATSAPP_API_URL}/{business_phone_number_id}/messages", headers=headers, json=data) as response:
            if response.status == 200:
                print("Message sent successfully")
            else:
                print(f"Failed to send message: {response.status}")
                print(await response.text())

     

async def send_status_error_interactive_template(business_phone_number_id, to, message, reply_message_id):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GRAPH_API_TOKEN}"
    }

    button_set = [
        {
            "type": "reply",
            "reply": {
                "id": "status_error_redo_button",
                "title": "Redo"
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": "status_error_cancel_button",
                "title": "Cancel"
            }
        }
    ]

    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {
                "type": "image",
                "image": {
                    "id": f"{media_map['StatusErrorMedia.png']}"
                }
            },
            "body": {
                "text": f"{message}"
            },
            "footer": {
                "text": "To proceed choose an option below"
            },
            "action": {
                "buttons": button_set
            }
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{WHATSAPP_API_URL}/{business_phone_number_id}/messages", headers=headers, json=data) as response:
            if response.status == 200:
                print("Message sent successfully")
            else:
                print(f"Failed to send message: {response.status}")
                print(await response.text())
 


@app.route("/", methods=["GET"])
async def index():
    return "<pre>Nothing to see here.\nCheckout README.md to start.</pre>"

if __name__ == "__main__":
    app.run(port=PORT, debug=True)
