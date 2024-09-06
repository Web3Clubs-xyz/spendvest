from configparser import Error
import os
from uuid import uuid4
from aiohttp import ClientSession
from dataclasses import dataclass, field
import aiohttp
from typing_extensions import Dict, override
from domain.entities.services.registration_event_publisher import (
    RegistrationCompleted,
    RegistrationEventsPublisher,
    RegistrationInputRequired,
    RegistrationUserPrompt,
)
from domain.entities.services.send_money_events_publisher import (
    ISendMoneyObserver,
    SendMoneyEventsPublisher,
    SendMoneyTransactionCompleted,
    SendMoneyTransactionInputRequired,
    SendMoneyUserPrompt,
)
from domain.entities.services.withdraw_event_publisher import (
    IWithdrawObserver,
    WithdrawCompleted,
    WithdrawEventsPublisher,
    WithdrawFailed,
    WithdrawInputRequired,
    WithdrawUserPrompt,
)
from domain.usecases.interfaces.register_account_interfaces import (
    IRegistrationEventObserver,
)


class WhatsappHomeInterfacePresenter:
    """
    Whatsapp presenter that informs users of available actions they can take.

    Attributes:
        facebook_endpoint_base_url (`str`): Facebook graph api endpoint we will
            be calling.
        whatsapp_access_token (`str`): Whatsapp access token
        whatsapp_business_account_id (`int`): Whatsapp business account id
        whatsapp_phone_number_id (`int`): Whatsapp phone number id

    Methods:
        render_registered_actions(): Renders actions available to registered
            users.
        render_unregistered_actions(): Renders actions that are avallable to
            unregistered customers.
    """

    facebook_endpoint_base_url: str = field(init=False)
    whatsapp_access_token: str = field(init=False)
    whatsapp_business_account_id: int = field(init=False)
    whatsapp_phone_number_id: int = field(init=False)
    whatsapp_headers: Dict = field(init=False)
    messages_url: str = field(init=False)

    def __init__(
        self,
        facebook_endpoint_base_url: str,
        whatsapp_access_token: str,
        whatsapp_business_account_id: int,
        whatsapp_phone_number_id: int,
    ) -> None:
        self.facebook_endpoint_base_url = facebook_endpoint_base_url
        self.whatsapp_access_token = whatsapp_access_token
        self.whatsapp_business_account_id = whatsapp_business_account_id
        self.whatsapp_phone_number_id = whatsapp_phone_number_id
        self.whatsapp_headers = {
            "Authorization": f"Bearer {whatsapp_access_token}",
            "Content-Type": "application/json",
        }
        self.messages_url = (
            self.facebook_endpoint_base_url
            + f"/{self.whatsapp_phone_number_id}/messages"
        )

    async def post_json_request(self, session: ClientSession, url: str, data: Dict):
        self.whatsapp_headers.update({
            "Authorization": os.getenv("WHATSAPP_ACCESS_TOKEN")
        })
        print(f"Whatsapp Headers: {self.whatsapp_headers}")
        async with session.post(
            url, json=data, headers=self.whatsapp_headers
        ) as response:
            return await response.json()

    async def render_registered_home_view(self, recepient: str):
        message = {
            "messaging_product": "whatsapp",
            "recepient_type": "individual",
            "to": recepient,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {"type": "text", "text": "Welcome"},
                "body": {
                    "text": "Pick from the list. What would you like to do today?"
                },
                "footer": {"text": "Spendvest helps you save while you make purchases"},
                "action": {
                    "sections": [
                        {
                            "title": "Spend",
                            "rows": [
                                {
                                    "id": "send_money",
                                    "title": "Send Money",
                                    "description": (
                                        "Send money to another mobile"
                                        " phone number and save."
                                    ),
                                }
                            ],
                        },
                        {
                            "title": "Withdraw",
                            "rows": [
                                {
                                    "id": "withdraw",
                                    "title": "Withdraw From Wallet",
                                    "description": (
                                        "Withdraw savings from your wallet"
                                    ),
                                }
                            ],
                        },
                    ],
                    "button": "Spending Options",
                },
            },
        }

        async with aiohttp.ClientSession() as session:
            await self.post_json_request(
                session=session, url=self.messages_url, data=message
            )

    async def render_unregistered_home_view(self, recepient):
        message = {
            "messaging_product": "whatsapp",
            "recepient_type": "individual",
            "to": recepient,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "header": {"text": "Sign Up For Spendvest", "type": "text"},
                "body": {"text": "Get to your saving goals by saving while spending."},
                "footer": {"text": "Register now to start saving"},
                "action": {
                    "buttons": [
                        {
                            "type": "reply",
                            "reply": {"id": "sign_up", "title": "Sign Up"},
                        }
                    ]
                },
            },
        }

        async with aiohttp.ClientSession() as session:
            print("Sending message to whatsapp...\n\n\n")
            response = await self.post_json_request(
                session=session, url=self.messages_url, data=message
            )
            print(f"Whatsapp Response: {response}")


class WhatsappRegistrationPresenter(IRegistrationEventObserver):
    """
    Whatsapp presenter that walks users through their account registration
    process.

    Attributes:
        facebook_endpoint_base_url (`str`): Facebook graph api endpoint we will
            be calling.
        whatsapp_access_token (`str`): Whatsapp access token
        whatsapp_business_account_id (`int`): Whatsapp business account id
        whatsapp_phone_number_id (`int`): Whatsapp phone number id

    Methods:
        render_form(): Renders a form for capturing information needed to
            register a sasapay wallet.
        render_invalid_form(): Informs the user that the input they gave was
            invalid.
        render_otp(): Prompts the user to enter the otp that was sent by
            sasapay.
        render_failed_otp(): Informs the customer that the otp they entered was
            invalid.
        render_successful_registration(): Informs the customer that their
            account has been successfully registered.
        update(event: `object`): Updates the presenter on registration events
            that it has subscribed to.
    """

    registration_event_publisher: RegistrationEventsPublisher = field(init=False)
    facebook_endpoint_base_url: str = field(init=False)
    whatsapp_access_token: str = field(init=False)
    whatsapp_business_account_id: int = field(init=False)
    whatsapp_phone_number_id: int = field(init=False)
    whatsapp_headers: Dict = field(init=False)
    messages_url: str = field(init=False)

    def __init__(
        self,
        facebook_endpoint_base_url: str,
        whatsapp_access_token: str,
        whatsapp_phone_number_id: int,
        whatsapp_business_account_id: int,
        registration_event_publisher: RegistrationEventsPublisher,
    ) -> None:
        self.whatsapp_access_token = whatsapp_access_token
        self.whatsapp_headers = {
            "Authorization": f"Bearer {self.whatsapp_access_token}",
            "Content-Type": "application/json",
        }
        self.whatsapp_phone_number_id = whatsapp_phone_number_id
        self.whatsapp_business_account_id = whatsapp_business_account_id
        self.facebook_endpoint_base_url = facebook_endpoint_base_url
        self.registration_event_publisher = registration_event_publisher
        self.messages_url = (
            self.facebook_endpoint_base_url
            + f"/{self.whatsapp_phone_number_id}/messages"
        )

    async def post_json_request(self, session: ClientSession, url: str, data: Dict):
        async with session.post(
            url, json=data, headers=self.whatsapp_headers
        ) as response:
            return await response.json()

    async def render_form(self, recepient: str) -> None:
        print("Sending registration form")
        message = {
            "recepient_type": "individual",
            "messaging_product": "whatsapp",
            "to": recepient,
            "type": "interactive",
            "interactive": {
                "type": "flow",
                "header": {"type": "text", "text": "Register on Spendvest"},
                "body": {"text": "Save while you make day to day purchases 🛒."},
                "footer": {"text": "Register now to start saving 💰."},
                "action": {
                    "name": "flow",
                    "parameters": {
                        "mode": "published",
                        "flow_message_version": "3",
                        "flow_token": uuid4().hex,
                        # We should move this to .env and check conditionally
                        # based on $ENVIRONMENT
                        "flow_id": "860335466252860",
                        "flow_cta": "Sign Up Form",
                        "flow_action": "navigate",
                        "flow_action_payload": {"screen": "REGISTRATION_SCREEN"},
                    },
                },
            },
        }

        async with aiohttp.ClientSession() as session:
            response = await self.post_json_request(
                session=session, url=self.messages_url, data=message
            )

            print(f"Whatsapp Form Response: {response}")

    async def render_otp(self, recepient: str):
        message = {
            "recepient_type": "individual",
            "messaging_product": "whatsapp",
            "to": recepient,
            "type": "text",
            "text": {
                "body": (
                    "An OTP was sent to the 📲 phone number you submitted for "
                    "registration. Text me the OTP sent to complete registering"
                    " your wallet 😁."
                )
            },
        }

        async with aiohttp.ClientSession() as session:
            await self.post_json_request(
                session=session, url=self.messages_url, data=message
            )

    async def render_failed_otp(self, recepient: str):
        message = {
            "recepient_type": "individual",
            "messaging_product": "whatsapp",
            "to": recepient,
            "type": "text",
            "text": {
                "body": (
                    "The OTP you entered was invalid 😥,"
                    " please confirm and send it to me again."
                )
            },
        }

        async with aiohttp.ClientSession() as session:
            await self.post_json_request(
                session=session, url=self.messages_url, data=message
            )

    async def render_successful_registration(self, recepient: str):
        message = {
            "recepient_type": "individual",
            "messaging_product": "whatsapp",
            "to": recepient,
            "type": "text",
            "text": {
                "body": (
                    "You have successfully registered your spendvest wallet 💳."
                    " Make purchases through spendvest to save!!"
                )
            },
        }

        async with aiohttp.ClientSession() as session:
            await self.post_json_request(
                session=session, url=self.messages_url, data=message
            )

    async def render_system_error(self, recepient: str):
        message = {
            "recepient_type": "individual",
            "messaging_product": "whatsapp",
            "to": recepient,
            "type": "text",
            "text": {
                "body": (
                    "There was a problem processing your"
                    "registration please try again later."
                )
            },
        }

        async with aiohttp.ClientSession() as session:
            await self.post_json_request(
                session=session, url=self.messages_url, data=message
            )

    @override
    async def update(self, event: object) -> None:
        print(f"Updating with {event}")
        if (
            isinstance(event, RegistrationUserPrompt)
            and event.event_name == "registration_info"
        ):
            await self.render_form(recepient=event.prompt_recepient)
            await self.registration_event_publisher.notify(
                event=RegistrationInputRequired(
                    input_name="registration_info",
                    prompt_recepient=event.prompt_recepient,
                )
            )

        if isinstance(event, RegistrationUserPrompt) and event.event_name == "otp":
            await self.render_otp(recepient=event.prompt_recepient)
            await self.registration_event_publisher.notify(
                event=RegistrationInputRequired(
                    input_name="otp",
                    prompt_recepient=event.prompt_recepient,
                )
            )

        if (
            isinstance(event, RegistrationUserPrompt)
            and event.event_name == "otp_failed"
        ):
            await self.render_failed_otp(recepient=event.prompt_recepient)
            await self.registration_event_publisher.notify(
                event=RegistrationInputRequired(
                    input_name="otp",
                    prompt_recepient=event.prompt_recepient,
                )
            )

        if (
            isinstance(event, RegistrationUserPrompt)
            and event.event_name == "registration_complete"
        ):
            await self.render_successful_registration(recepient=event.prompt_recepient)
            await self.registration_event_publisher.notify(
                event=RegistrationCompleted()
            )

        if (
            isinstance(event, RegistrationUserPrompt)
            and event.event_name == "invalid_input"
        ):
            await self.render_system_error(recepient=event.prompt_recepient)
            await self.registration_event_publisher.notify(
                event=RegistrationCompleted()
            )


@dataclass
class WhatsappRegistrationPresenterFactory:
    facebook_endpoint_base_url: str
    whatsapp_access_token: str
    whatsapp_business_account_id: int
    whatsapp_phone_number_id: int

    def create(
        self, registration_event_publisher: RegistrationEventsPublisher
    ) -> WhatsappRegistrationPresenter:
        presenter = WhatsappRegistrationPresenter(
            facebook_endpoint_base_url=self.facebook_endpoint_base_url,
            whatsapp_access_token=self.whatsapp_access_token,
            whatsapp_business_account_id=self.whatsapp_business_account_id,
            whatsapp_phone_number_id=self.whatsapp_phone_number_id,
            registration_event_publisher=registration_event_publisher,
        )

        return presenter


@dataclass
class WhatsappSendMoneyPresenter(ISendMoneyObserver):
    """
    Whatsapp presenter that renders messages taking people through steps to
    send money.
    """

    send_money_events_publisher: SendMoneyEventsPublisher
    facebook_endpoint_base_url: str
    whatsapp_access_token: str
    whatsapp_business_account_id: int
    whatsapp_phone_number_id: int
    whatsapp_headers: Dict
    messages_url: str

    def __init__(
        self,
        send_money_events_publisher: SendMoneyEventsPublisher,
        facebook_endpoint_base_url: str,
        whatsapp_access_token: str,
        whatsapp_phone_number_id: int,
        whatsapp_business_account_id: int,
    ) -> None:
        self.send_money_events_publisher = send_money_events_publisher
        self.whatsapp_access_token = whatsapp_access_token
        self.whatsapp_headers = {
            "Authorization": f"Bearer {self.whatsapp_access_token}",
            "Content-Type": "application/json",
        }
        self.whatsapp_phone_number_id = whatsapp_phone_number_id
        self.whatsapp_business_account_id = whatsapp_business_account_id
        self.facebook_endpoint_base_url = facebook_endpoint_base_url
        self.messages_url = (
            self.facebook_endpoint_base_url
            + f"/{self.whatsapp_phone_number_id}/messages"
        )

    async def post_json_request(self, session: ClientSession, url: str, data: Dict):
        async with session.post(
            url, json=data, headers=self.whatsapp_headers
        ) as response:
            return await response.json()

    async def render_successful_transaction(
        self, amount: int, recepient: str, recepient_phone_number: int
    ):
        message = {
            "recepient_type": "individual",
            "messaging_product": "whatsapp",
            "to": recepient,
            "type": "text",
            "text": {
                "body": f"KES {amount} has been sent to 0{recepient_phone_number}"
            },
        }

        async with aiohttp.ClientSession() as session:
            await self.post_json_request(
                session=session, url=self.messages_url, data=message
            )

    async def render_unauthorized_action(self, recepient: str):
        message = {
            "recepient_type": "individual",
            "messaging_product": "whatsapp",
            "to": recepient,
            "type": "text",
            "text": {
                "body": "📵 You have to register first before you can send money."
            },
        }

        async with aiohttp.ClientSession() as session:
            await self.post_json_request(
                session=session, url=self.messages_url, data=message
            )

    async def prompt_user(self, recepient: str):
        message = {
            "recepient_type": "individual",
            "messaging_product": "whatsapp",
            "to": recepient,
            "type": "interactive",
            "interactive": {
                "type": "flow",
                "header": {"type": "text", "text": "Send Money With Spendvest"},
                "body": {"text": "Send money to friends or for purchases and save."},
                "footer": {"text": "Send money"},
                "action": {
                    "name": "flow",
                    "parameters": {
                        "mode": "published",
                        "flow_message_version": "3",
                        "flow_token": uuid4().hex,
                        # We should move this to .env and check conditionally
                        # based on $ENVIRONMENT
                        "flow_id": "1048396856627165",
                        "flow_cta": "Send Money Form",
                        "flow_action": "navigate",
                        "flow_action_payload": {
                            "screen": "SEND_MONEY_SCREEN",
                        },
                    },
                },
            },
        }

        async with aiohttp.ClientSession() as session:
            response = await self.post_json_request(
                session=session, url=self.messages_url, data=message
            )

            print(f"Received whatsapp response {response}")

    async def notify_successful_payment_request(
        self,
        recepient: str,
        phone_number: str,
        receiving_phone_number: str,
    ):
        message = {
            "recepient_type": "individual",
            "messaging_product": "whatsapp",
            "to": recepient,
            "type": "text",
            "text": {
                "body": (
                    f"🎉 We successfully received funds from 0{phone_number}!. "
                    "We will save a percentage and 🚚 send money "
                    f"to 0{receiving_phone_number}."
                )
            },
        }

        async with aiohttp.ClientSession() as session:
            await self.post_json_request(
                session=session, url=self.messages_url, data=message
            )

    async def notify_failed_fund_transfer(
        self,
        recepient: str,
    ):
        message = {
            "recepient_type": "individual",
            "messaging_product": "whatsapp",
            "to": recepient,
            "type": "text",
            "text": {"body": "🚫 A problem occurred. We couldn't transfer funds."},
        }

        async with aiohttp.ClientSession() as session:
            await self.post_json_request(
                session=session, url=self.messages_url, data=message
            )

    async def pin_prompt(self, recepient: str) -> None:
        print("Prompting user for pin")
        message = {
            "recepient_type": "individual",
            "messaging_product": "whatsapp",
            "to": recepient,
            "type": "text",
            "text": {
                "body": (
                    "Please enter your mpesa pin 🔢 *when prompted*"
                    " to send the funds."
                )
            },
        }

        async with aiohttp.ClientSession() as session:
            response = await self.post_json_request(
                session=session, url=self.messages_url, data=message
            )
            print(f"Whatsapp Response: {response}")

    async def notify_error(self, recepient: str) -> None:
        print("Notifying user of error")
        message = {
            "recepient_type": "individual",
            "messaging_product": "whatsapp",
            "to": recepient,
            "type": "text",
            "text": {
                "body": (
                    "A problem occurred while trying to send money. "
                    "Please try again later."
                )
            },
        }

        async with aiohttp.ClientSession() as session:
            response = await self.post_json_request(
                session=session, url=self.messages_url, data=message
            )
            print(f"Whatsapp Response: {response}")

    @override
    async def update(self, event: object) -> None:
        if isinstance(event, SendMoneyUserPrompt):
            match event.event_name:
                case "send_money_info":
                    await self.prompt_user(recepient=event.prompt_recepient)
                    await self.send_money_events_publisher.notify(
                        event=SendMoneyTransactionInputRequired(
                            input_name="send_money_info",
                            prompt_recepient=event.prompt_recepient,
                        )
                    )
                case "pin_prompt":
                    print("Received event notification.")
                    await self.pin_prompt(recepient=event.prompt_recepient)
                case "successful_funds_request":
                    if event.data is None:
                        raise Error("No data was sent about funds request")

                    await self.notify_successful_payment_request(
                        recepient=event.prompt_recepient,
                        phone_number=event.data["phone_number"],
                        receiving_phone_number=event.data["receiving_phone_number"],
                    )
                case "successful_funds_transfer":
                    if event.data is None:
                        raise Error(
                            "No data was sent about the successful transaction."
                        )

                    await self.render_successful_transaction(
                        amount=event.data["amount"],
                        recepient=event.prompt_recepient,
                        recepient_phone_number=event.data["recepient_phone_number"],
                    )
                    await self.send_money_events_publisher.notify(
                        event=SendMoneyTransactionCompleted()
                    )
                case "failed_funds_transfer":
                    await self.notify_failed_fund_transfer(
                        recepient=event.prompt_recepient
                    )
                case "error":
                    await self.notify_error(recepient=event.prompt_recepient)
                    await self.send_money_events_publisher.notify(
                        event=SendMoneyTransactionCompleted()
                    )


@dataclass
class WhatsappSendMoneyPresenterFactory:
    facebook_endpoint_base_url: str
    whatsapp_access_token: str
    whatsapp_business_account_id: int
    whatsapp_phone_number_id: int

    def create(
        self, send_money_events_publisher: SendMoneyEventsPublisher
    ) -> WhatsappSendMoneyPresenter:
        presenter = WhatsappSendMoneyPresenter(
            send_money_events_publisher=send_money_events_publisher,
            facebook_endpoint_base_url=self.facebook_endpoint_base_url,
            whatsapp_access_token=self.whatsapp_access_token,
            whatsapp_phone_number_id=self.whatsapp_phone_number_id,
            whatsapp_business_account_id=self.whatsapp_business_account_id,
        )

        send_money_events_publisher.subscribe(presenter)

        return presenter


class WhatsappProcessingPresenter:
    """
    Informs the user that the operation they have initiated is being processed.
    """

    facebook_endpoint_base_url: str = field(init=False)
    whatsapp_access_token: str = field(init=False)
    whatsapp_business_account_id: int = field(init=False)
    whatsapp_phone_number_id: int = field(init=False)
    whatsapp_headers: Dict = field(init=False)
    messages_url: str = field(init=False)

    def __init__(
        self,
        facebook_endpoint_base_url: str,
        whatsapp_access_token: str,
        whatsapp_phone_number_id: int,
        whatsapp_business_account_id: int,
    ) -> None:
        self.whatsapp_access_token = whatsapp_access_token
        self.whatsapp_headers = {
            "Authorization": f"Bearer {self.whatsapp_access_token}",
            "Content-Type": "application/json",
        }
        self.whatsapp_phone_number_id = whatsapp_phone_number_id
        self.whatsapp_business_account_id = whatsapp_business_account_id
        self.facebook_endpoint_base_url = facebook_endpoint_base_url
        self.messages_url = (
            self.facebook_endpoint_base_url
            + f"/{self.whatsapp_phone_number_id}/messages"
        )

    async def post_json_request(self, session: ClientSession, url: str, data: Dict):
        async with session.post(
            url, json=data, headers=self.whatsapp_headers
        ) as response:
            return response

    async def prompt_processing(self, recepient: str):
        message = {
            "recepient_type": "individual",
            "messaging_product": "whatsapp",
            "to": recepient,
            "type": "text",
            "text": {"body": "_processing..._"},
        }

        async with aiohttp.ClientSession() as session:
            await self.post_json_request(
                session=session, url=self.messages_url, data=message
            )


class WhatsappWithdrawPresenter(IWithdrawObserver):
    """
    Whatsapp presenter that renders messages taking people through steps to
    withdraw their savings.
    """

    facebook_endpoint_base_url: str = field(init=False)
    whatsapp_access_token: str = field(init=False)
    whatsapp_business_account_id: int = field(init=False)
    whatsapp_phone_number_id: int = field(init=False)
    whatsapp_headers: Dict = field(init=False)
    messages_url: str = field(init=False)
    withdraw_event_publisher: WithdrawEventsPublisher

    def __init__(
        self,
        facebook_endpoint_base_url: str,
        whatsapp_access_token: str,
        whatsapp_phone_number_id: int,
        whatsapp_business_account_id: int,
        withdraw_event_publisher: WithdrawEventsPublisher,
    ) -> None:
        self.whatsapp_access_token = whatsapp_access_token
        self.whatsapp_headers = {
            "Authorization": f"Bearer {self.whatsapp_access_token}",
            "Content-Type": "application/json",
        }
        self.whatsapp_phone_number_id = whatsapp_phone_number_id
        self.whatsapp_business_account_id = whatsapp_business_account_id
        self.facebook_endpoint_base_url = facebook_endpoint_base_url
        self.messages_url = (
            self.facebook_endpoint_base_url
            + f"/{self.whatsapp_phone_number_id}/messages"
        )
        self.withdraw_event_publisher = withdraw_event_publisher

    async def post_json_request(self, session: ClientSession, url: str, data: Dict):
        async with session.post(
            url, json=data, headers=self.whatsapp_headers
        ) as response:
            response_data = await response.json()
            print(f"Response from whatsapp: {response_data}")
            return response_data

    async def render_failed_withdrawal(self, recepient: str) -> None:
        message = {
            "recepient_type": "individual",
            "messaging_product": "whatsapp",
            "to": recepient,
            "type": "text",
            "text": {
                "body": (
                    "🚫 We encountered a problem while trying "
                    "to withdraw funds from your wallet. Please try again later."
                )
            },
        }

        async with aiohttp.ClientSession() as session:
            await self.post_json_request(
                session=session, url=self.messages_url, data=message
            )

    async def render_successful_withdrawal(self, recepient: str, amount: int):
        message = {
            "recepient_type": "individual",
            "messaging_product": "whatsapp",
            "to": recepient,
            "type": "text",
            "text": {"body": f"🎉 You have successfully withdrawn KES {amount}"},
        }

        async with aiohttp.ClientSession() as session:
            await self.post_json_request(
                session=session, url=self.messages_url, data=message
            )

    async def prompt_user(self, recepient: str):
        print("Prompting user to fill form.")
        message = {
            "recepient_type": "individual",
            "messaging_product": "whatsapp",
            "to": recepient,
            "type": "interactive",
            "interactive": {
                "type": "flow",
                "header": {"type": "text", "text": "Withdraw Your Savings"},
                "body": {"text": "You can withdraw your savings now! 💃."},
                "footer": {"text": "Withdraw"},
                "action": {
                    "name": "flow",
                    "parameters": {
                        "mode": "published",
                        "flow_message_version": "3",
                        "flow_token": uuid4().hex,
                        # We should move this to .env and check conditionally
                        # based on $ENVIRONMENT
                        "flow_id": "1707011593449202",
                        "flow_cta": "Withdraw Form",
                        "flow_action": "navigate",
                        "flow_action_payload": {
                            "screen": "WITHDRAW_SCREEN",
                        },
                    },
                },
            },
        }

        async with aiohttp.ClientSession() as session:
            await self.post_json_request(
                session=session, url=self.messages_url, data=message
            )

    @override
    async def update(self, event: object) -> None:
        if isinstance(event, WithdrawUserPrompt):
            event_name = event.event_name

            match event_name:
                case "withdraw_info":
                    print("Received prompt event")
                    await self.prompt_user(recepient=event.prompt_recepient)
                    await self.withdraw_event_publisher.notify(
                        event=WithdrawInputRequired(
                            input_name="withdraw_info",
                            prompt_recepient=event.prompt_recepient,
                        )
                    )
                case "successful_withdraw":
                    if event.data is None:
                        raise ValueError(
                            "Data wasn't provided for successful withdrawal."
                        )
                    await self.render_successful_withdrawal(
                        recepient=event.prompt_recepient, amount=event.data["amount"]
                    )
                    await self.withdraw_event_publisher.notify(
                        event=WithdrawCompleted()
                    )

        if isinstance(event, WithdrawFailed):
            await self.render_failed_withdrawal(recepient=event.prompt_recepient)


@dataclass
class WhatsappWithdrawPresenterFactory:
    facebook_endpoint_base_url: str
    whatsapp_access_token: str
    whatsapp_phone_number_id: int
    whatsapp_business_account_id: int

    def create(
        self, withdraw_event_publisher: WithdrawEventsPublisher
    ) -> WhatsappWithdrawPresenter:
        presenter = WhatsappWithdrawPresenter(
            facebook_endpoint_base_url=self.facebook_endpoint_base_url,
            whatsapp_access_token=self.whatsapp_access_token,
            whatsapp_phone_number_id=self.whatsapp_phone_number_id,
            whatsapp_business_account_id=self.whatsapp_business_account_id,
            withdraw_event_publisher=withdraw_event_publisher,
        )

        withdraw_event_publisher.subscribe(observer=presenter)

        return presenter


class WhatsappInvalidInputPresenter:
    """
    Whatsapp presenter that informs the user that the input they provided was
    invalid.
    """

    facebook_endpoint_base_url: str = field(init=False)
    whatsapp_access_token: str = field(init=False)
    whatsapp_business_account_id: int = field(init=False)
    whatsapp_phone_number_id: int = field(init=False)
    whatsapp_headers: Dict = field(init=False)
    messages_url: str = field(init=False)

    def __init__(
        self,
        facebook_endpoint_base_url: str,
        whatsapp_access_token: str,
        whatsapp_business_account_id: int,
        whatsapp_phone_number_id: int,
    ) -> None:
        self.facebook_endpoint_base_url = facebook_endpoint_base_url
        self.whatsapp_access_token = whatsapp_access_token
        self.whatsapp_business_account_id = whatsapp_business_account_id
        self.whatsapp_phone_number_id = whatsapp_phone_number_id
        self.whatsapp_headers = {
            "Authorization": f"Bearer {whatsapp_access_token}",
            "Content-Type": "application/json",
        }

    async def post_json_request(self, session: ClientSession, url: str, data: Dict):
        async with session.post(
            url, json=data, headers=self.whatsapp_headers
        ) as response:
            return response

    async def render_rejected_input(self, recepient: str):
        message = {
            "recepient_type": "individual",
            "messaging_product": "whatsapp",
            "to": recepient,
            "type": "text",
            "text": {"body": "I couldn't understand the message you sent."},
        }

        async with aiohttp.ClientSession() as session:
            await self.post_json_request(
                session=session, url=self.messages_url, data=message
            )
