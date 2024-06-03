# Registration
from blu import Session
from models import Menu, MpesaCustomer
from states import CircularQuestionList, output_bot_message
import re


def registration_handler(user_waid, count_, client_input):
    if client_input == "yes":

        if Session.complete_reg_slotting(user_waid):
            Session.save_answer(user_waid, count_, client_input)
            message = f"Your registeration using +{user_waid}\n\nfor spendvest is complete,\n\n"
            Session.load_handler(user_waid, 'st_handler', 'ST',0, 1)
            existing_customer = MpesaCustomer.query.filter_by(mpesa_number=user_waid).first()
            
            if existing_customer:
                print(f"customer is existing")
                Session.clear_answer_slot(user_waid)
                message = f"This number is already registerd"
            else:
                MpesaCustomer.add_mpesa_customer(user_waid)

            return output_bot_message(message)
        
        else:
            Session.save_answer(user_waid, count_, client_input)
            quiz_pack = Menu.load_question_pack("RU")
            quiz = Session.return_current_slot_quiz(user_waid, quiz_pack)
    
            Session.step_slotting(user_waid, quiz_pack)

            return output_bot_message(quiz)
    
    elif client_input == "no":
        print(f"Customer has cancelled")
        Session.clear_answer_slot(user_waid)
        message = f"You have cancelled the registeration process" 
        Session.load_handler(user_waid, "st_handler", "ST", 1, 1)
        return output_bot_message(message)

registration = CircularQuestionList()
question_payload = "Register!\n\nWould you like us to register this number for Mpesa service?\n Yes or No"
registration.append(
    trigger_input="/reg",
    valid_input=re.compile(r'^(yes|no)$'),
    menu_message=question_payload,
    handler=registration_handler
)

question_payload = "Confirm registeration, by re-entering previous answer"
registration.append(
    valid_input=re.compile(r'^(yes|no)$'),
    menu_message=question_payload,
    handler=registration_handler
)
