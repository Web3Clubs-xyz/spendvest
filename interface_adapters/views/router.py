from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import json
from logging import Logger
import traceback
from pydantic import BaseModel, Field
from typing_extensions import Dict, List, Optional
from domain.entities.services.session_service import SessionService
from domain.entities.sessions import SessionType, UserSession
from interface_adapters.ui.controllers.controllers import (
    InvalidInputController,
    NewSessionController,
    RegistrationController,
    SendMoneyController,
    WithdrawController,
)
from interface_adapters.ui.controllers.session_event_publisher import (
    ControllerEventPublisher,
)


class WhatsappProfile(BaseModel):
    name: str


class WhatsappValueContact(BaseModel):
    wa_id: str
    user_id: Optional[str] = None
    profile: WhatsappProfile


class WhatsappErrorData(BaseModel):
    details: str


class WhatsappError(BaseModel):
    code: int
    title: str
    message: str
    error_data: WhatsappErrorData


class WhatsappAudio(BaseModel):
    id: str
    mime_type: str


class WhatsappButton(BaseModel):
    payload: str
    text: str


class WhatsappMessageReferredProduct(BaseModel):
    catalog_id: str
    product_retailer_id: str


class WhatsappMessageContext(BaseModel):
    forwarded: Optional[bool] = None
    frequently_forwarded: Optional[bool] = None
    from_: str = Field(alias="from")
    id_: str = Field(alias="id")
    referred_product: Optional[WhatsappMessageReferredProduct] = None


class WhatsappDocument(BaseModel):
    caption: str
    file_name: str
    sha256: str
    mime_type: str
    id: str


class WhatsappIdentity(BaseModel):
    acknowledged: str
    created_timestamp: str
    hash: str


class WhatsappImage(BaseModel):
    caption: str
    sha256: str
    id: str
    mime_type: str


class WhatsappButtonReply(BaseModel):
    id: str
    title: str


class WhatsappListReply(BaseModel):
    id: str
    title: str
    description: str


class WhatsappFlowReply(BaseModel):
    name: str
    body: str
    response_json: str


class WhatsappInteractive(BaseModel):
    type_: str = Field(alias="type")
    button_reply: Optional[WhatsappButtonReply] = None
    list_reply: Optional[WhatsappListReply] = None
    nfm_reply: Optional[WhatsappFlowReply] = None


class WhatsappProductItems(BaseModel):
    product_retailer_id: str
    quantity: str
    item_price: str
    currency: str


class WhatsappOrder(BaseModel):
    catalog_id: str
    text: str
    product_items: WhatsappProductItems


class WhatsappReferral(BaseModel):
    source_url: str
    source_type: str
    source_id: str
    headline: str
    body: str
    media_type: str
    image_url: str
    video_url: str
    thumbnail_url: str
    ctwa_clid: str


class WhatsappSticker(BaseModel):
    mime_type: str
    sha256: str
    id: str
    animated: bool


class WhatsappSystem(BaseModel):
    body: str
    identity: str
    wa_id: str
    type_: str = Field(alias="type")
    customer: str


class WhatsappText(BaseModel):
    body: str


class WhatsappVideo(BaseModel):
    caption: str
    filename: str
    sha256: str
    id: str
    mime_type: str


class WhatsappMessage(BaseModel):
    audio: Optional[WhatsappAudio] = None
    button: Optional[WhatsappButton] = None
    context: Optional[WhatsappMessageContext] = None
    document: Optional[WhatsappDocument] = None
    errors: Optional[List[WhatsappError]] = None
    from_: str = Field(alias="from")
    id_: str = Field(alias="id")
    identity: Optional[WhatsappIdentity] = None
    image: Optional[WhatsappImage] = None
    interactive: Optional[WhatsappInteractive] = None
    order: Optional[WhatsappOrder] = None
    referral: Optional[WhatsappReferral] = None
    sticker: Optional[WhatsappSticker] = None
    system: Optional[WhatsappSystem] = None
    text: Optional[WhatsappText] = None
    timestamp: str
    type_: str = Field(alias="type")
    video: Optional[WhatsappVideo] = None


class WhatsappMetadata(BaseModel):
    display_phone_number: str
    phone_number_id: str


class WhatsappConversationOrigin(BaseModel):
    type: str


class WhatsappStatusConversation(BaseModel):
    id: str
    origin: WhatsappConversationOrigin
    expiration_timestamp: Optional[str] = None


class WhatsappPricing(BaseModel):
    category: str
    pricing_model: str


class WhatsappStatus(BaseModel):
    biz_opaque_callback_data: Optional[str] = None
    conversation: Optional[WhatsappStatusConversation] = None
    errors: Optional[List[WhatsappError]] = None
    id_: str = Field(alias="id")
    pricing: Optional[WhatsappPricing] = None
    recepient_id: Optional[str] = None
    status: str
    timestamp: str


class WhatsappValue(BaseModel):
    contacts: Optional[List[WhatsappValueContact]] = None
    errors: Optional[List[WhatsappError]] = None
    messaging_product: str
    messages: Optional[List[WhatsappMessage]] = None
    metadata: WhatsappMetadata
    statuses: Optional[List[WhatsappStatus]] = None


class WhatsappChange(BaseModel):
    value: WhatsappValue
    field: str


class WhatsappEntry(BaseModel):
    id: str
    changes: List[WhatsappChange]


class WhatsappWebhook(BaseModel):
    """
    Datastructure used for type safety at the fastapi endpoint.
    """

    object: str
    entry: List[WhatsappEntry]


class SpendvestMessage:
    """
    Datastructure that spendvest uses to communicate with controllers

    Attributes:
        whatsapp_id (`str`): The customer's whatsapp id
        message_type (`str`): The type of message the user has sent
        text (`Optional[WhatsappText]`): Available if a user sent a text message
        interactive (`Optional[WhatsappInteractive]`): Available if a user sent
            an interactive message.
    """

    _whatsapp_id: str
    _message_type: str
    _text: Optional[WhatsappText] = None
    _interactive: Optional[WhatsappInteractive] = None

    @property
    def whatsapp_id(self) -> str:
        return self._whatsapp_id

    @whatsapp_id.setter
    def whatsapp_id(self, whatsapp_id: str) -> None:
        self._whatsapp_id = whatsapp_id

    @property
    def message_type(self) -> str:
        return self._message_type

    @message_type.setter
    def message_type(self, message_type: str) -> None:
        self._message_type = message_type

    @property
    def text(self) -> WhatsappText | None:
        return self._text

    @text.setter
    def text(self, text: WhatsappText | None) -> None:
        self._text = text

    @property
    def interactive(self) -> WhatsappInteractive | None:
        return self._interactive

    @interactive.setter
    def interactive(self, interactive: WhatsappInteractive | None) -> None:
        self._interactive = interactive

    def __str__(self):
        return (
            f"whatsapp_id: {self.whatsapp_id}, message_type:"
            f"{self.message_type}, text: {self.text}, interactive: {self.interactive}"
        )


class IRouter(ABC):
    @abstractmethod
    async def handle_registration(self):
        pass

    @abstractmethod
    async def handle_send_money(self):
        pass

    @abstractmethod
    async def handle_withdraw(self):
        pass

    @abstractmethod
    async def route(self, session: UserSession | None, message: SpendvestMessage):
        pass


@dataclass
class WhatsappRouter:
    """
    Router that takes incoming whatsapp messages and directs them to the
    appropriate client (use cases, controllers, event publishers etc).

    Attributes:
        session_service (`SessionService`): Service that manages sessions.
        new_session_controller (`NewSessionController`): controller that takes
            input needed to create a new session.
        registration_controller (`RegistrationController`): Controller that
            takes input needed to register a customer.
        send_money_controller (`SendMoneyController`): Controller that takes
            input needed to send money to a mobile phone number.
        withdraw_controller (`WithdrawController`): Controller that takes input
            needed to withdraw funds.
        invalid_input_controller (`InvalidInputController`): Controller that
            handles invalid input sent by the customer.
        controller_event_publisher (`ControllerEventPublisher`): Event
            publisher that is use cases use to listen for input in the middle of
            operations.

    """

    session_service: SessionService
    new_session_controller: NewSessionController
    registration_controller: RegistrationController
    send_money_controller: SendMoneyController
    withdraw_controller: WithdrawController
    invalid_input_controller: InvalidInputController
    controller_event_publisher: ControllerEventPublisher
    logger: Logger

    def extract_data(self, message: SpendvestMessage) -> Dict:
        message_type = message.message_type

        match message_type:
            case "text":
                if message.text is None:
                    return {}

                return {"data": message.text.body}
            case "interactive":
                if message.interactive is None:
                    return {}

                if message.interactive.list_reply is not None:
                    return {"data": message.interactive.list_reply.id}

                if message.interactive.nfm_reply is not None:
                    data = json.loads(message.interactive.nfm_reply.response_json)
                    return {"data": data}

                if message.interactive.button_reply is not None:
                    return {"data": message.interactive.button_reply.id}

                return {}
            case _:
                return {}

    async def route(
        self, session: UserSession | None, message: SpendvestMessage
    ) -> None:
        print("Routing...")
        if session is None:
            print("Creating new session")
            await self.new_session_controller.create_session(
                external_id=message.whatsapp_id
            )

            return

        if message.message_type == "NOT_ALLOWED":
            # TODO
            # We should pass a session id here so presenter knows who to send
            # the message to.
            await self.invalid_input_controller.reject_input(session=session)

            return

        session_type = session.session_type.id

        if (
            session_type == 1
            and message.interactive is not None
            and message.interactive.list_reply is not None
        ):
            # This is a new session check what user picked in list and
            # start that session state machine.
            # identify which controller to use based on selection
            option = message.interactive.list_reply.id

            match option:
                case "send_money":
                    # Update session type
                    session.session_type = SessionType(id=3, name="SEND_MONEY")
                    await self.session_service.save_customer_session(
                        customer_session=session
                    )

                    # Call send money controller
                    await self.send_money_controller.send_money(session=session)
                case "withdraw":
                    # Update session type
                    session.session_type = SessionType(id=4, name="WITHDRAW")
                    await self.session_service.save_customer_session(
                        customer_session=session
                    )

                    # call withdraw controller
                    await self.withdraw_controller.withdraw(session=session)
                case _:
                    # Handle invalid option
                    pass
        elif (
            session_type == 1
            and message.interactive is not None
            and message.interactive.button_reply is not None
        ):
            button_id = message.interactive.button_reply.id

            if button_id == "sign_up":
                # Update session type
                session.session_type = SessionType(id=2, name="REGISTRATION")
                await self.session_service.save_customer_session(
                    customer_session=session
                )

                # Call send money controller
                print("Calling register_user()")
                await self.registration_controller.register_user(session=session)

        elif session_type == 2:
            # This is a registration session
            # Send session and input data to controller for processing

            if (
                message.interactive is not None
                and message.interactive.type_ == "nfm_reply"
            ):
                try:
                    extracted_data = self.extract_data(message=message)
                    data = extracted_data["data"]

                    user_input = {
                        "first_name": data["first_name"],
                        "middle_name": data["middle_name"],
                        "last_name": data["last_name"],
                        "phone_number": data["phone_number"],
                        "email": data["email"],
                        "document_type": data["document_type"],
                        "document_number": data["document_number"],
                        "saving_percentage": data["saving_percentage"],
                        "whatsapp": session.id,
                    }

                    self.controller_event_publisher.notify(
                        event_id=session.id, event_type="registration", data=user_input
                    )
                except Exception as e:
                    print(f"An error occured while notifying controllers {str(e)}")
                    traceback.print_exc()  # Logs the full traceback to the console

            if message.text is not None:
                # We are processing an OTP
                otp = self.extract_data(message=message)["data"]

                self.controller_event_publisher.notify(
                    event_id=session.id, event_type="registration_otp", data=otp
                )

        elif session_type == 3:
            # Send session and data to controller for processing

            if (
                message.interactive is not None
                and message.interactive.type_ == "nfm_reply"
            ):
                data = self.extract_data(message=message)["data"]
                self.logger.info(f"Processing send money flow information {data}")
                user_input = {
                    "payment_amount": int(data["payment_amount"]),
                    "receiving_phone_number": data["receiving_phone_number"],
                    "session": session,
                }
                self.controller_event_publisher.notify(
                    event_id=session.id, event_type="send_money", data=user_input
                )

            if message.text is not None:
                pass

        elif session_type == 4:
            # Emit event to withdraw controller
            if (
                message.interactive is not None
                and message.interactive.type_ == "nfm_reply"
            ):
                data = self.extract_data(message=message)["data"]

                user_input = {
                    "amount": int(data["amount"]),
                    "receiving_phone_number": data["receiving_phone_number"],
                }
                self.controller_event_publisher.notify(
                    event_id=session.id, event_type="withdraw", data=user_input
                )

        else:
            # handle invalid session type
            pass

    def old_message(self, message_timestamp: int) -> bool:
        current_time = datetime.now().timestamp()
        time_delta = current_time - message_timestamp

        return time_delta > 120

    async def handle_message(self, message: WhatsappMessage):
        message_timestamp = int(message.timestamp)

        if self.old_message(message_timestamp=message_timestamp):
            self.logger.warning("Received old message.")
            return

        whatsapp_id = message.from_
        input: SpendvestMessage = SpendvestMessage()
        input.whatsapp_id = whatsapp_id

        session = await self.session_service.get_customer_session(
            external_id=whatsapp_id
        )

        if message.text is not None:
            input.message_type = "text"
            input.text = message.text
        elif message.interactive is not None:
            input.message_type = "interactive"
            input.interactive = message.interactive
        else:
            input.message_type = "NOT_ALLOWED"

        await self.route(session=session, message=input)

    async def handle_value(self, value: WhatsappValue):
        messages = value.messages
        statuses = value.statuses

        if statuses is None and messages is not None:
            for message in messages:
                await self.handle_message(message=message)

    async def handle_changes(self, changes: List[WhatsappChange]):
        for change in changes:
            value = change.value
            await self.handle_value(value)

    async def handle_whatsapp_webhook(self, data: WhatsappWebhook):
        entries = data.entry

        for entry in entries:
            changes = entry.changes
            await self.handle_changes(changes=changes)
