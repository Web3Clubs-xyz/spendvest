from dataclasses import dataclass
from typing import Callable, Optional
import re
from twilio.twiml.messaging_response import MessagingResponse

from blu import Session
     
def output_bot_message(message):
    resp = MessagingResponse()
    resp.message(message)
    m = str(resp)
    print(f"'returning bot output {m}")
    return str(resp)

@dataclass
class QuestionState():
    next_state: 'QuestionState'
    valid_input: re.Pattern
    menu_message: str
    handler: Callable

    def handle_input(
            self,
            input_character,
    ) -> Optional['QuestionState']:
        match = self.valid_input.match(input_character)

        if match:
            successful_processing = self.handler(input_character)
            return successful_processing
        
        raise Exception("Invalid input.")


    def get_menu_message(message: str):
        output_bot_message(message)
    
@dataclass
class CircularQuestionList():
    head: QuestionState
    current_step: QuestionState
    trigger_input: str

    def append(self, trigger_input, valid_input, menu_message, handler):
        new_question = QuestionState(
            trigger_input=trigger_input,
            valid_input=valid_input,
            menu_message=menu_message,
            handler=handler
        )
        if not self.head:
            self.head = new_question
            self.head.next = self.head
            self.current_step = self.head
        else:
            current = self.head
            while current.next != self.head:
                current = current.next
            current.next = new_question
            new_question.next = self.head

    def set_current_step(self, step: QuestionState):
        self.current_step = step
        # Set slot in redis
        

    def handle_input(self, input_character: str):
        success = self.current_step.handle_input(
            input_character=input_character
        )

        if success:
            self.set_current_step(self.current_step.next_state)

        return success
    
# Send Money
send_money = CircularQuestionList()

# Lipa Pochi
lipa_pochi = CircularQuestionList()

# Buy Goods Till
buy_goods_till = CircularQuestionList()

# Paybill
paybill_till = CircularQuestionList()