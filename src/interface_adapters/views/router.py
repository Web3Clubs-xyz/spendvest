from abc import ABC, abstractmethod
from dataclasses import dataclass
from pydantic import BaseModel, Field
from typing_extensions import Dict, List, Optional, override

from domain.entities.services.session_service import ISessionService
from domain.entities.sessions import UserSession
from interface_adapters.ui.controllers.controller_interfaces import (
    IInvalidInputController,
    INewSessionController,
    IRegistrationController,
    ISendMoneyController,
    IWithdrawController,
)


class WhatsappProfile(BaseModel):
    name: str


class WhatsappValueContact(BaseModel):
    wa_id: str
    user_id: str
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
    forwarded: bool
    frequently_forwarded: bool
    from_: str = Field(alias="from")
    id_: str = Field(alias="id")
    referred_product: WhatsappMessageReferredProduct


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


class WhatsappInteractiveType(BaseModel):
    button_reply: Optional[WhatsappButtonReply]
    list_reply: Optional[WhatsappListReply]
    nfm_reply: Optional[WhatsappFlowReply]


class WhatsappInteractive(BaseModel):
    type_: WhatsappInteractiveType = Field(alias="type")


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
    audio: Optional[WhatsappAudio]
    button: Optional[WhatsappButton]
    context: Optional[WhatsappMessageContext]
    document: Optional[WhatsappDocument]
    errors: List[WhatsappError]
    from_: str = Field(alias="from")
    id_: str = Field(alias="id")
    identity: Optional[WhatsappIdentity]
    image: Optional[WhatsappImage]
    interactive: Optional[WhatsappInteractive]
    order: Optional[WhatsappOrder]
    referral: Optional[WhatsappReferral]
    sticker: Optional[WhatsappSticker]
    system: Optional[WhatsappSystem]
    text: Optional[WhatsappText]
    timestamp: str
    type_: str = Field(alias="type")
    video: Optional[WhatsappVideo]


class WhatsappMetadata(BaseModel):
    display_phone_number: str
    phone_number_id: str


class WhatsappConversationOrigin(BaseModel):
    type: str


class WhatsappStatusConversation(BaseModel):
    id: str
    origin: WhatsappConversationOrigin
    expiration_timestamp: Optional[str]


class WhatsappPricing(BaseModel):
    category: str
    pricing_model: str


class WhatsappStatus(BaseModel):
    biz_opaque_callback_data: str
    conversation: WhatsappStatusConversation
    errors: List[WhatsappError]
    id_: str = Field(alias="id")
    pricing: WhatsappPricing
    recepient_id: str
    status: str
    timestamp: str


class WhatsappValue(BaseModel):
    contacts: List[WhatsappValueContact]
    errors: List[WhatsappError]
    messaging_product: str
    messages: List[WhatsappMessage]
    metadata: WhatsappMetadata
    statuses: List[WhatsappStatus]


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


class SpendvestMessage(BaseModel):
    """
    Datastructure that spendvest uses to communicate with controllers
    """

    _whatsapp_id: str = Field(init=False)
    _message_type: str = Field(init=False)
    _text: Optional[WhatsappText] = Field(init=False)
    _interactive: Optional[WhatsappInteractive] = Field(init=False)

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
class WhatsappRouter(IRouter):
    session_service: ISessionService
    new_session_controller: INewSessionController
    registration_controller: IRegistrationController
    send_money_controller: ISendMoneyController
    withdraw_controller: IWithdrawController
    invalid_input_controller: IInvalidInputController

    def extract_data(self, message: SpendvestMessage) -> Dict:
        message_type = message.message_type

        match message_type:
            case "text":
                if message.text is None:
                    return {}

                return {"data": message.text.body}
            case "list_reply":
                if message.interactive is None:
                    return {}

                if message.interactive.type_.list_reply is None:
                    return {}

                return {"data": message.interactive.type_.list_reply.id}
            case "nfm_reply":
                if message.interactive is None:
                    return {}

                if message.interactive.type_.nfm_reply is None:
                    return {}

                return {"data": message.interactive.type_.nfm_reply.response_json}
            case _:
                return {}

    @override
    async def route(
        self, session: UserSession | None, message: SpendvestMessage
    ) -> None:

        if message.message_type == "NOT_ALLOWED":
            await self.invalid_input_controller.reject_input()

            return

        if session is None:
            await self.new_session_controller.create_session(
                external_id=message.whatsapp_id, session_type="new"
            )

            return

        session_type = session.session_type.id

        if (
            session_type == 1
            and message.interactive is not None
            and message.interactive.type_.list_reply is not None
        ):
            # This is a new session check what user picked in list and
            # start that session state machine.
            # identify which controller to use based on selection
            option = message.interactive.type_.list_reply.id

            match option:
                case 2:
                    # Call send money controller
                    await self.send_money_controller.send_money()
                case 3:
                    # call withdraw controller
                    await self.withdraw_controller.withdraw()
                case _:
                    # Handle invalid option
                    pass
        elif session_type == 2:
            # Emit event to registration controller
            data = self.extract_data(message=message)
            await self.registration_controller.emit_registration_event(
                session=session, data=data
            )
        elif session_type == 3:
            # Emit event to send money controller
            data = self.extract_data(message=message)
            await self.send_money_controller.emit_send_money_event(
                session=session, data=data
            )
        elif session_type == 4:
            # Emit event to withdraw controller
            data = self.extract_data(message=message)
            await self.withdraw_controller.emit_withdraw_event(
                session=session, data=data
            )
        else:
            # handle invalid session type
            pass

    async def handle_message(self, message: WhatsappMessage):
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
