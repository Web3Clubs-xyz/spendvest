from states import CircularQuestionList, output_bot_message
from typing import List
import re

class QuestionContext():
    user_flows: List[CircularQuestionList]
    current_flow: CircularQuestionList

    def set_current_flow(self, flow_trigger):
        pattern = re.compile(r'^(/reg|/sm|/lp|/bgt|/pb)$')

        if not pattern.match:
            raise Exception("Invalid Input")
        
        for flow in self.user_flows:
            if flow_trigger == flow.trigger_input:
                # Set slot in redis
                self.current_flow = flow

    def trigger_flow_step(self, input_character):
        """
        Trigger the current step in the current flow
        """
        try:
            handler_status = self.current_flow.handle_input(
                input_character=input_character
            )

            if handler_status:
                pass
        except Exception as e:
            print(e)

    def display_main_menu():
        main_menu_question_payload = "Select the following commands to proceed: \n\n0./reg\nfor register Whatsapp number for Mpesa services\n\n1./sm\nfor send money\n\n2./lp\nfor lipa pochi\n\n3./lbt\nfor buy goods and services till\n\n4./lbp\nfor paybill till\n\nTo select any enter /command or number"
        output_bot_message(main_menu_question_payload)
