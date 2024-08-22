from uuid import uuid4
from aiohttp import ClientSession
from dataclasses import field
import aiohttp
from typing_extensions import Dict, override
from domain.entities.services.registration_event_publisher import (
    RegistrationCompleted,
    RegistrationInputRequired,
)
from domain.usecases.interfaces.presenter_interfaces import (
    IHomeInterfacePresenter,
    IRegisterSasapayWalletPresenter,
    ISasapayWithdrawPresenter,
)


class WhatsappHomeInterfacePresenter(IHomeInterfacePresenter):
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

    async def post_json_request(self, session: ClientSession, url: str, data: Dict):
        async with session.post(
            url, json=data, headers=self.whatsapp_headers
        ) as response:
            return response

    @override
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

    @override
    async def render_unregistered_home_view(self, recepient):
        message = {
            "messaging_product": "whatsapp",
            "recepient_type": "individual",
            "to": recepient,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "header": {"text": "Sign Up For Spendvest"},
                "body": {"text": "Get to your saving goals by saving while spending."},
                "footer": {"text": "Register now to start saving"},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": "1", "title": "Sign Up"}}
                    ]
                },
            },
        }

        async with aiohttp.ClientSession() as session:
            await self.post_json_request(
                session=session, url=self.messages_url, data=message
            )


class WhatsappRegistrationPresenter(IRegisterSasapayWalletPresenter):
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

    @override
    async def render_form(self, recepient: str) -> None:
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
                        "flow_message_version": "3",
                        "flow_token": uuid4().hex,
                        "flow_id": "1279210149910870",
                        "flow_cta": "Sign Up",
                        "flow_action": "data_exchange",
                        "flow_action_payload": {
                            "screen": "REGISTRATION_SCREEN",
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

    @override
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

    @override
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

    @override
    async def update(self, event: object) -> None:
        if (
            isinstance(event, RegistrationInputRequired)
            and event.input_name == "registration_info"
        ):
            await self.render_form(recepient=event.prompt_recepient)

        if isinstance(event, RegistrationInputRequired) and event.input_name == "otp":
            await self.render_otp(recepient=event.prompt_recepient)

        if (
            isinstance(event, RegistrationInputRequired)
            and event.input_name == "otp_failed"
        ):
            await self.render_failed_otp(recepient=event.prompt_recepient)

        if isinstance(event, RegistrationCompleted):
            await self.render_successful_registration(recepient=event.prompt_recepient)


class WhatsappSendMoneyPresenter:
    """
    Whatsapp presenter that renders messages taking people through steps to
    send money.
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

    async def render_successful_transaction(
        self, amount: int, recepient: str, recepient_phone_number: int
    ):
        message = {
            "recepient_type": "individual",
            "messaging_product": "whatsapp",
            "to": recepient,
            "type": "text",
            "text": {"body": f"KES {amount} has been sent to {recepient_phone_number}"},
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
                        "flow_message_version": "3",
                        "flow_token": uuid4().hex,
                        "flow_id": "1048396856627165",
                        "flow_cta": "Send Money",
                        "flow_action": "data_exchange",
                        "flow_action_payload": {
                            "screen": "SEND_MONEY_SCREEN",
                        },
                    },
                },
            },
        }

        async with aiohttp.ClientSession() as session:
            await self.post_json_request(
                session=session, url=self.messages_url, data=message
            )


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


class WhatsappWithdrawPresenter(ISasapayWithdrawPresenter):
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
        message = {
            "recepient_type": "individual",
            "messaging_product": "whatsapp",
            "to": recepient,
            "type": "interactive",
            "interactive": {
                "type": "flow",
                "header": {"type": "text", "text": "Withdraw Your Savings"},
                "body": {
                    "text": "You can withdraw and realise the efforts of you savings 💃."
                },
                "footer": {"text": "Withdraw"},
                "action": {
                    "name": "flow",
                    "parameters": {
                        "flow_message_version": "3",
                        "flow_token": uuid4().hex,
                        "flow_id": "1707011593449202",
                        "flow_cta": "Withdraw",
                        "flow_action": "data_exchange",
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
