import os
from flask import Flask, request, jsonify
import aiohttp
import asyncio
from dotenv import load_dotenv
from pprint import pprint
import string
import random
import json 

from blu import Session 
from models import SlotQuestion, AccountSummary, MpesaCustomer, Settlement,RequestTask
from payments2 import send_payment, send_user_stk
import re

# Load environment variables from .env file
load_dotenv()

# Retrieve environment variables
GRAPH_API_TOKEN = os.getenv('GRAPH_API_TOKEN', "EAAUCpth1wAIBOZCYAHogpxiflMq5WS3MSg2ICMprv4g5qO8TDljz79lMJvpis8TGEkXDYWXdIuKPgGXtvOTg2gIKK2TUQIaPBdkVnkpuywUAkr6oRyEYAjR4wAZBL8fXQ5QSgfm8O7lnlC21D2PCX180VCODc5225lqni8fDlZBgIiY763reAdFYqcsSPKm6JJN4UORAz5LZBTFPIOCCD8YasHM5")
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
                        await send_mainmenu_home_interactive_template(True, business_phone_number_id, user_waid, user_message, message_id)
                    else:
                        print(f"Unregistered Mpesa user")
                        await send_mainmenu_home_interactive_template(False, business_phone_number_id, user_waid, user_message, message_id)

                    
                
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
                            await send_slot_quiz_interactive_template("ru_handler",business_phone_number_id,user_waid,quiz,message_id)
                             
                        else:
                            error_message = "Please enter answer as instructed"
                            await send_slot_quiz_interactive_template("ru_handler",business_phone_number_id, user_waid, error_message, message_id)
                        
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
                            try:
                                MpesaCustomer.add_mpesa_customer(user_waid, user_waid)
                                Session.complete_reg_slotting(user_waid)
                                Session.clear_answer_slot(user_waid)
                                Session.off_slot_filling(user_waid)
                                Session.on_main_menu_nav(user_waid, "main_menu_select_home")
                                # ++ slotfilling
                                # Session.step_slotting(user_waid, quiz_pack)
                                # send quiz
                                await send_status_congrats_reg_interactive_template("ru_handler",business_phone_number_id,user_waid,end_process_message,message_id)

                            except Exception as e:
                                print(f"finish slot filling error, {e}")
                                end_process_message = "There seems to be an error with your submission"
                                await send_status_error_reg_interactive_template("ru_handler",business_phone_number_id,user_waid,end_process_message,message_id)
                                  
                        else:
                            error_message = "Please enter answer as instructed"
                            await send_slot_quiz_interactive_template("ru_handler",business_phone_number_id, user_waid, error_message, message_id)



                if handler == "sa_handler":
                    
                    if current_count_ == '0': 
                        print(f"processing {handler}, with count {current_count_}")
                        user_input = user_message
                        if verify_is_percentage(user_input):
                            # record
                            Session.save_reg_answer(user_waid,current_count_, user_input)
                            # update counter
                            # get question pack
                            quiz_pack = SlotQuestion.get_question_pack('SA')
                            print(f"fetched quiz_pack, {quiz_pack}")
                            # get first quiz
                            quiz = quiz_pack[str(int(current_count_) + 1)]
                            # ++ slotfilling
                            Session.step_slotting(user_waid, quiz_pack)
                            # send quiz
                            await send_slot_quiz_interactive_template("sa_handler",business_phone_number_id,user_waid,quiz,message_id)
                             
                        else:
                            error_message = "Please enter answer as instructed"
                            await send_slot_quiz_interactive_template("sa_handler",business_phone_number_id, user_waid, error_message, message_id)

                    if current_count_ == '1': 
                        print(f"processing {handler}, with count {current_count_}")
                        user_input = user_message
                        if verify_is_percentage(user_input):
                            # record
                            Session.save_reg_answer(user_waid,current_count_, user_input)
                            # should complete
                            # update counter
                            # get question pack
                            quiz_pack = SlotQuestion.get_question_pack('SA')
                            print(f"fetched quiz_pack, {quiz_pack}")
                            # get first quiz
                            end_process_message = "Youre saving percentage has been succesfully set!"
                            try:
                                AccountSummary.update_acc_summary(user_waid, {"saving_percentage":float(user_input)})
                                
                                Session.clear_answer_slot(user_waid)
                                Session.off_slot_filling(user_waid)
                                Session.on_main_menu_nav(user_waid, "main_menu_select_home")
                                # ++ slotfilling
                                # Session.step_slotting(user_waid, quiz_pack)
                                # send quiz
                                await send_status_congrats_reg_interactive_template("sa_handler",business_phone_number_id,user_waid,end_process_message,message_id)

                            except Exception as e:
                                print(f"finish slot filling error, {e}")
                                end_process_message = "There seems to be an error with your submission"
                                await send_status_error_reg_interactive_template("sa_handler",business_phone_number_id,user_waid,end_process_message,message_id)
                                  
                        else:
                            error_message = "Please enter answer as instructed"
                            await send_slot_quiz_interactive_template("sa_handler",business_phone_number_id, user_waid, error_message, message_id)
          
                    
                if handler == "sm_handler":
                    if current_count_ in ('0', '1'): 
                        print(f"processing {handler}, with count {current_count_}")
                        user_input = user_message
                        if is_valid_phonenumber(user_input):
                            # record
                            Session.save_reg_answer(user_waid,current_count_, user_input)
                            # update counter
                            # get question pack
                            quiz_pack = SlotQuestion.get_question_pack('SM')
                            print(f"fetched quiz_pack, {quiz_pack}")
                            # get first quiz
                            quiz = quiz_pack[str(int(current_count_) + 1)]
                            # ++ slotfilling
                            Session.step_slotting(user_waid, quiz_pack)
                            # send quiz
                            await send_slot_quiz_interactive_template("sa_handler",business_phone_number_id,user_waid,quiz,message_id)
                             
                        else:
                            error_message = "Please phone number as instructed"
                            await send_slot_quiz_interactive_template("sm_handler",business_phone_number_id, user_waid, error_message, message_id)

                    if current_count_ == '2': 
                        print(f"processing {handler}, with count {current_count_}")
                        user_input = user_message

                        if is_valid_amount(user_input):
                            # record
                            Session.save_reg_answer(user_waid,current_count_, user_input)
                            
                            # update counter
                            # get question pack
                            quiz_pack = SlotQuestion.get_question_pack('SM')
                            print(f"fetched quiz_pack, {quiz_pack}")
                            # get first quiz
                            end_process_message = "Your send money request has been succesfully set!"
                            try:
                                end_number = json.loads(Session.get_session(user_waid)[b'answer_payload'])[0]
                                print(f"sending to end number : {end_number}")
                                send_user_stk(user_waid, user_input, "SM", end_number)
                                Session.complete_sm_slotting(user_waid)                           
                                Session.clear_answer_slot(user_waid)
                                Session.off_slot_filling(user_waid)
                                Session.on_main_menu_nav(user_waid, "main_menu_select_home")
                                # ++ slotfilling
                                # Session.step_slotting(user_waid, quiz_pack)
                                # send quiz
                                await send_status_congrats_reg_interactive_template("sm_handler",business_phone_number_id,user_waid,end_process_message,message_id)

                            except Exception as e:
                                print(f"finish slot filling error, {e}")
                                end_process_message = "There seems to be an error with your submission"
                                await send_status_error_reg_interactive_template("sm_handler",business_phone_number_id,user_waid,end_process_message,message_id)
                                
                        else:
                            error_message = "Please enter amount as instructed"
                            await send_slot_quiz_interactive_template("sm_handler",business_phone_number_id, user_waid, error_message, message_id)



                

                
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
            await send_mainmenu_home_interactive_template(False, business_phone_number_id, user_waid, user_message, message_id)

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
                    await send_mainmenu_home_interactive_template(True, business_phone_number_id, user_waid, user_message, message_id)
            else:
                    print(f"Unregistered Mpesa user")
                    await send_mainmenu_home_interactive_template(False, business_phone_number_id, user_waid, user_message, message_id)

        if button_reply['id'] == "main_menu_account_button":
            Session.off_main_menu_nav(user_waid)
            Session.on_sub1_menu_nav(user_waid, "sub1_menu_select_acc")

            # Helper function to convert snake_case to Title Case
            def convert_to_title_case(snake_str):
                components = snake_str.split('_')
                return ' '.join(x.capitalize() for x in components)

            # Fetch the account summary
            acc_summary = AccountSummary.get_acc_summary(user_waid)

            # Decode, format and convert keys to Title Case
            formatted_summary = '\n\n'.join([f"{convert_to_title_case(key.decode('utf-8'))}: {value.decode('utf-8')}" for key, value in acc_summary.items()])

            # Construct the user message for the account summary
            user_message = f"Here is your account summary:\n\n{formatted_summary}"

            # Fetch the user registration information
            user_registration = MpesaCustomer.get_single_user(user_waid)

            # Selectively include only specific fields and format keys
            filtered_registration = {k: v for k, v in user_registration.items() if k.decode('utf-8') in ['whatsapp_client_number', 'mpesa_transaction_number', 'created_at']}
            formatted_registration = '\n'.join([f"{convert_to_title_case(key.decode('utf-8'))}: {value.decode('utf-8')}" for key, value in filtered_registration.items()])

            # Append the user registration information to the user message
            user_message += f"\n\nChecking user registration:\n\n{formatted_registration}"

            # Print or return the user message
            print(user_message)


            if MpesaCustomer.get_user_reg_status(user_waid):
                print(f"\n\nRegistered Mpesa user")
                await send_sub1menu_acc_interactive_template(True, business_phone_number_id, user_waid, user_message, message_id)
            else:
                print(f"\n\nUnregisterd Mpesa user")
                await send_sub1menu_acc_interactive_template(False, business_phone_number_id, user_waid, user_message, message_id)
        
        if button_reply['id'] == "sub1_menu_acc_cancel_button":
            Session.off_sub1_menu_nav(user_waid)
            Session.on_main_menu_nav(user_waid,"main_menu_select_home")
            if MpesaCustomer.get_user_reg_status(user_waid):
                    print(f"Registered Mpesa user")
                    await send_mainmenu_home_interactive_template(True, business_phone_number_id, user_waid, user_message, message_id)
            else:
                    print(f"Unregistered Mpesa user")
                    await send_mainmenu_home_interactive_template(False, business_phone_number_id, user_waid, user_message, message_id)
        
        if button_reply['id'] == "sub1_menu_acc_reg_button":
            Session.off_sub1_menu_nav(user_waid)
            Session.on_sub2_menu_nav(user_waid,"sub2_menu_select_register")
            await send_sub2menu_register_interactive_template(business_phone_number_id,user_waid,user_message, message_id)
        
        if button_reply['id'] == "sub2_menu_reg_cancel_button":
            Session.off_sub2_menu_nav(user_waid)
            Session.on_sub1_menu_nav(user_waid, "sub1_menu_select_acc")
            user_message="sure"
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
            await send_slot_quiz_interactive_template('ru_handler',business_phone_number_id,user_waid,quiz,message_id)

        if button_reply['id'] =="slot_filling_reg_cancel_button":
            # set slotfilling off
            Session.off_slot_filling(user_waid)
            # clean answer payload
            Session.clear_answer_slot(user_waid)
            # return back to menu sub2_menu_select_reg
            Session.off_sub1_menu_nav(user_waid)
            Session.on_sub2_menu_nav(user_waid,"sub2_menu_select_register")
            await send_sub2menu_register_interactive_template(business_phone_number_id,user_waid,user_message, message_id)
        
        if button_reply['id'] == "status_congrats_reg_done_button":
            Session.off_slot_filling(user_waid)
            Session.clear_answer_slot(user_waid)
            Session.on_main_menu_nav(user_waid,"main_menu_select_home")
            await send_mainmenu_home_interactive_template(True,business_phone_number_id,user_waid,user_message, message_id)

        if button_reply['id'] == "status_error_reg_cancel_button":
            Session.off_slot_filling(user_waid)
            Session.clear_answer_slot(user_waid)
            Session.on_main_menu_nav(user_waid,"main_menu_select_home")
            await send_mainmenu_home_interactive_template(False,business_phone_number_id,user_waid,user_message, message_id)

        if button_reply['id'] == "status_error_reg_redo_button":
            Session.off_sub1_menu_nav(user_waid)
            Session.on_sub2_menu_nav(user_waid,"sub2_menu_select_register")
            await send_sub2menu_register_interactive_template(business_phone_number_id,user_waid,user_message, message_id)
        
             

        
        if button_reply['id'] == "sub1_menu_acc_save_button":
            Session.off_sub1_menu_nav(user_waid)
            Session.on_sub2_menu_nav(user_waid,"sub2_menu_select_save")
            user_message = "Select your saving plan"
            await send_sub2menu_save_interactive_template(business_phone_number_id,user_waid,user_message, message_id)
        
        if button_reply['id'] == "sub2_menu_save_cancel_button":
            Session.off_sub2_menu_nav(user_waid)
            Session.on_sub1_menu_nav(user_waid, "sub1_menu_select_acc")
            if MpesaCustomer.get_user_reg_status(user_waid):
                print(f"Registered Mpesa user")
                await send_sub1menu_acc_interactive_template(True, business_phone_number_id, user_waid, user_message, message_id)
            else:
                print(f"Unregisterd Mpesa user")
                await send_sub1menu_acc_interactive_template(False, business_phone_number_id, user_waid, user_message, message_id)
            pass 

        if button_reply['id'] == "sub2_menu_save_proceed_button":
            print(f"About to start save slot filling")
            # off sub2_main_nav
            Session.off_sub2_menu_nav(user_waid)
            # on slotfilling
            Session.set_slot_filling_on(user_waid)
            Session.load_handler(user_waid, 'sa_handler', "SA",0,2)

            # get first question
            slot_details = Session.fetch_slot_details(user_waid)
            print(f"fetched slot details , {slot_details}")
            # get question pack
            quiz_pack = SlotQuestion.get_question_pack("SA")
            print(f"fetched quiz_pack, {quiz_pack}")
            # get first quiz
            quiz = quiz_pack[slot_details['slot_count']]

            handler = "sa_handler"
            await send_slot_quiz_interactive_template(handler, business_phone_number_id,user_waid,quiz,message_id)

        if button_reply['id'] == "slot_filling_save_cancel_button":
            # set slotfilling off
            Session.off_slot_filling(user_waid)
            # clean answer payload
            Session.clear_answer_slot(user_waid)
            # return back to menu sub2_menu_select_reg
            Session.off_sub1_menu_nav(user_waid)
            Session.on_sub2_menu_nav(user_waid,"sub2_menu_select_register")
            await send_sub2menu_save_interactive_template(business_phone_number_id,user_waid,user_message, message_id)
        

        if button_reply['id'] == "status_congrats_sa_done_button":
            Session.off_slot_filling(user_waid)
            Session.clear_answer_slot(user_waid)
            Session.on_main_menu_nav(user_waid,"main_menu_select_home")
            await send_mainmenu_home_interactive_template(True,business_phone_number_id,user_waid,user_message, message_id)

        if button_reply['id'] == "status_error_sa_redo_button":
            Session.off_sub1_menu_nav(user_waid)
            Session.on_sub2_menu_nav(user_waid,"sub2_menu_select_save")
            await send_sub2menu_save_interactive_template(business_phone_number_id,user_waid,user_message, message_id)


        # send money
        if button_reply['id'] == "main_menu_spend_button":
            Session.off_main_menu_nav(user_waid)
            Session.on_sub1_menu_nav(user_waid, "sub1_menu_select_spend")
            if MpesaCustomer.get_user_reg_status(user_waid):
                print(f"\n\nRegistered Mpesa user")
                await send_sub1menu_spend_interactive_template(True, business_phone_number_id, user_waid, user_message, message_id)
            else:
                print(f"\n\nUnregisterd Mpesa user")
                await send_sub1menu_spend_interactive_template(False, business_phone_number_id, user_waid, user_message, message_id)
        
        if button_reply['id'] == "sub1_menu_spend_cancel_button":
            Session.off_sub1_menu_nav(user_waid)
            Session.on_main_menu_nav(user_waid,"main_menu_select_home")
            if MpesaCustomer.get_user_reg_status(user_waid):
                    print(f"Registered Mpesa user")
                    await send_mainmenu_home_interactive_template(True, business_phone_number_id, user_waid, user_message, message_id)
            else:
                    print(f"Unregistered Mpesa user")
                    await send_mainmenu_home_interactive_template(False, business_phone_number_id, user_waid, user_message, message_id)
         

        if button_reply['id'] == "sub1_menu_spend_sendmoney_button":
            Session.off_sub1_menu_nav(user_waid)
            Session.on_sub2_menu_nav(user_waid,"sub2_menu_select_sendmoney")
            await send_sub2menu_sendmoney_interactive_template(business_phone_number_id,user_waid,user_message, message_id) 

        if button_reply['id'] == "sub2_menu_sendmoney_proceed_button":
            print(f"proceed with sending money slot filling")
            # off sub2_main_nav
            Session.off_sub2_menu_nav(user_waid)
            # on slotfilling
            Session.set_slot_filling_on(user_waid)
            Session.load_handler(user_waid, 'sm_handler', "SM",0,3)

            # get first question
            slot_details = Session.fetch_slot_details(user_waid)
            print(f"fetched slot details , {slot_details}")
            # get question pack
            quiz_pack = SlotQuestion.get_question_pack("SM")
            print(f"fetched quiz_pack, {quiz_pack}")
            # get first quiz
            quiz = quiz_pack[slot_details['slot_count']]

            handler = "sm_handler"
            await send_slot_quiz_interactive_template(handler, business_phone_number_id,user_waid,quiz,message_id)


        if button_reply['id'] == "sub2_menu_sendmoney_cancel_button":
           Session.off_sub2_menu_nav(user_waid)
           Session.on_sub1_menu_nav(user_waid, "sub1_menu_select_spend")
           await send_sub1menu_spend_interactive_template(True,business_phone_number_id, user_waid, user_message, message_id)
        
        if button_reply['id'] == "slot_filling_sm_cancel_button":
            # set slotfilling off
            Session.off_slot_filling(user_waid)
            # clean answer payload
            Session.clear_answer_slot(user_waid)
            # return back to menu sub2_menu_select_reg
            Session.off_sub1_menu_nav(user_waid)
            Session.on_sub2_menu_nav(user_waid,"sub2_menu_select_spend")
            await send_sub2menu_sendmoney_interactive_template(business_phone_number_id,user_waid,user_message, message_id)
        
        

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


def verify_is_percentage(input):
    pattern = re.compile(r'^\s*\d+(\.\d+)?\s*%?\s*$')
    return bool(pattern.match(input))

def is_valid_amount(input):
    pattern = re.compile(r'^\d+$')
    return bool(pattern.match(input))

def is_valid_phonenumber(input):
    pattern = re.compile(r'^07\d{8,10}$')
    return bool(pattern.match(input))

async def send_mainmenu_home_interactive_template(reg_status, business_phone_number_id, to, message, reply_message_id):
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
                "text": f"{message}"
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
                "id": "sub2_menu_save_proceed_button",
                "title": "Proceed"
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": "sub2_menu_save_cancel_button",
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
                "id": "sub1_menu_spend_sendmoney_button",
                "title": "Send Money"
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": "sub1_menu_spend_buyairtime_button",
                "title": "Buy Airtime"
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": "sub1_menu_spend_cancel_button",
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
    

async def send_slot_quiz_interactive_template(slot_handler, business_phone_number_id, to, message, reply_message_id):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GRAPH_API_TOKEN}"
    }

    if slot_handler == "ru_handler":
        button_set = [
        {
            "type": "reply",
            "reply": {
                "id": "slot_filling_reg_cancel_button",
                "title": "Cancel"
            }
        }
    ]

    elif slot_handler == "sa_handler":
        button_set = [
        {
            "type": "reply",
            "reply": {
                "id": "slot_filling_save_cancel_button",
                "title": "Cancel"
            }
        }
    ]
         

    elif slot_handler == "sm_handler":
        button_set = [
        {
            "type": "reply",
            "reply": {
                "id": "slot_filling_sm_cancel_button",
                "title": "Cancel"
            }
        }
    ]
        

    elif slot_handler == "wd_handler":
        button_set = [
        {
            "type": "reply",
            "reply": {
                "id": "slot_filling_wd_cancel_button",
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

     



async def send_status_congrats_reg_interactive_template(slot_handler,business_phone_number_id, to, message, reply_message_id):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GRAPH_API_TOKEN}"
    }

   
    
    if slot_handler == "ru_handler":
         button_set = [
        {
            "type": "reply",
            "reply": {
                "id": "status_congrats_reg_done_button",
                "title": "Done"
            }
        }
    ]

    elif slot_handler == "sa_handler":
        button_set = [
        {
            "type": "reply",
            "reply": {
                "id": "status_congrats_sa_done_button",
                "title": "Done"
            }
        }
    ]
    
         

    elif slot_handler == "sm_handler":
        button_set = [
        {
            "type": "reply",
            "reply": {
                "id": "slot_filling_sm_cancel_button",
                "title": "Done"
            }
        }
    ]
        

    elif slot_handler == "wd_handler":
        button_set = [
        {
            "type": "reply",
            "reply": {
                "id": "slot_filling_wd_cancel_button",
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

     

async def send_status_error_reg_interactive_template(slot_handler, business_phone_number_id, to, message, reply_message_id):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GRAPH_API_TOKEN}"
    }

    

    if slot_handler == "ru_handler":
        button_set = [
        {
            "type": "reply",
            "reply": {
                "id": "status_error_reg_redo_button",
                "title": "Redo"
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": "status_error_reg_cancel_button",
                "title": "Cancel"
            }
        }
    ]

    elif slot_handler == "sa_handler":
       button_set = [
        {
            "type": "reply",
            "reply": {
                "id": "status_error_sa_redo_button",
                "title": "Redo"
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": "status_error_sa_cancel_button",
                "title": "Cancel"
            }
        }
    ]
    
         

    elif slot_handler == "sm_handler":
       button_set = [
        {
            "type": "reply",
            "reply": {
                "id": "status_error_sm_redo_button",
                "title": "Redo"
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": "status_error_sm_cancel_button",
                "title": "Cancel"
            }
        }
    ]
        

    elif slot_handler == "wd_handler":
        button_set = [
        {
            "type": "reply",
            "reply": {
                "id": "status_error_wd_redo_button",
                "title": "Redo"
            }
        },
        {
            "type": "reply",
            "reply": {
                "id": "status_error_wd_cancel_button",
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


def convert_phone_number(end_number):
    end_number = end_number.decode('utf-8')
    pattern = re.compile(r'^0(\d{8,10})$')
    match = pattern.match(end_number)
    if match:
        return '+254' + match.group(1)
    return end_number



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
    print(f"\n\nfetched task is : {requested_task}")

    print("\n\n\n")
    requested_settlement = Settlement.get_customer_settlement(ref)
    print(f"fetched settlement is : {requested_settlement}")

    customer_waid = requested_task[b'customer_waid'].decode('utf-8')
    

    requested_acc_summary = AccountSummary.get_acc_summary(customer_waid)
    print(f"fetched account summary is : {requested_acc_summary}")

    save_percentage = requested_acc_summary[b'saving_percentage'].decode('utf-8')
    save_percentage = float(save_percentage)

    print(f"fetched saving percentage : {save_percentage}")
    
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
            return 'ok'
        else:
            end_number = requested_settlement[b'end_settlement_number'].decode('utf-8')
            payment_amount = requested_settlement[b'amount']
            payment_amount = payment_amount.decode('utf-8')
            print(f"now settling payment")
            # end_number = "0" + end_number[4:]

            print(f"end_number : {end_number}")
            print(f"payment amount : {payment_amount}")
            # update acc summary, for pending settlements,total settlements , amount settlement, total amount saved and last amount saved

            original_amount = float(payment_amount) / float(1.0 + save_percentage)
            bal1 = float(payment_amount) - original_amount

            summary_update = {
                'pending_settlement':0,
                'total_settlement': float(requested_acc_summary[b'total_settlement'].decode('utf-8')) + 1,
                'amount_settled' : float(requested_acc_summary[b'amount_settled'].decode('utf-8')) + float(payment_amount),
                'total_amount_saved':float(requested_acc_summary[b'total_amount_saved'].decode('utf-8')) + float(bal1),
                'last_amount_saved':float(requested_acc_summary[b'total_amount_saved'].decode('utf-8')) + float(bal1)

            }

            AccountSummary.update_acc_summary(requested_task[b'customer_waid'], summary_update)

            
            send_payment(str(end_number), payment_amount)
            
    
    return 'ok'


@app.route("/mpesa_callback_timeout", methods=['POST'])
def process_callback_timeout():
    print(f"recieved callback data is, {request.get_json()}")

    return 'ok'


@app.route("/", methods=["GET"])
async def index():
    return "<pre>Nothing to see here.\nCheckout README.md to start.</pre>"

if __name__ == "__main__":
    app.run(port=PORT, debug=True)
