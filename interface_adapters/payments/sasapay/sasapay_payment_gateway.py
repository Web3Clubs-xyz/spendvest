from asyncio import Queue
from configparser import Error
from dataclasses import dataclass, field
from logging import Logger
import os
from typing import Dict
from uuid import uuid4
from aiohttp import ClientSession
import aiohttp
from domain.entities.services.registration_event_publisher import (
    RegistrationEventsPublisher,
    RegistrationInputReceived,
    RegistrationUserPrompt,
)
from domain.entities.services.send_money_events_publisher import (
    ISendMoneyObserver,
    SendMoneyEventsPublisher,
    SendMoneyTransactionInputReceived,
    SendMoneyUserPrompt,
)
from domain.entities.services.withdraw_event_publisher import (
    IWithdrawObserver,
    WithdrawEventsPublisher,
)
from domain.entities.users import Customer
from domain.usecases.interfaces.register_account_interfaces import (
    IRegistrationEventObserver,
)
from interface_adapters.payments.sasapay.api_data_types import (
    ConfirmationResponseData,
    PersonalOnboardingConfirmationResponseParameters,
    PersonalOnboardingRequestParameters,
    PersonalOnboardingResponseParameters,
    RequestPaymentOTPRequestParameters,
    RequestPaymentRequestParameters,
    RequestPaymentResponseParameters,
    TransferFundsRequestParameters,
    TransferFundsResultsParameters,
)

from interface_adapters.payments.sasapay.payment_events_publisher import (
    PaymentEventsPublisher,
)


@dataclass
class SasapayApiClient:
    """
    API client that talks to sasapay's api.
    """

    personal_onboarding_endpoint: str
    personal_onboarding_confirmation_endpoint: str
    access_token: str
    request_payment_endpoint: str
    transfer_funds_endpoint: str
    site_url: str
    merchant_code: str
    sasapay_headers: Dict
    payment_events_publisher: PaymentEventsPublisher
    logger: Logger

    async def post_json_request(self, session: ClientSession, url: str, data: Dict):
        self.sasapay_headers.update({
            "Authorization": f"Bearer {os.getenv('SASAPAY_ACCESS_TOKEN')}"
        })
        self.logger.info(f"Headers: {self.sasapay_headers}")
        self.logger.info(f"Access Token: {os.getenv('SASAPAY_ACCESS_TOKEN')}")
        self.logger.info(f"URL: {url}")
        self.logger.info(f"Payload: {data}")
        async with session.post(
            url, json=data, headers=self.sasapay_headers
        ) as response:
            data = await response.json()
            self.logger.info(f"Response from api: {data}")
            return data

    async def personal_onboarding_request(
        self,
        customer: Customer,
        otp_event_id: str,
        document_number: str,
        document_type: str,
    ) -> PersonalOnboardingResponseParameters:
        """
        API call to start the wallet registration process.

        Args:
            request_parameters (`PersonalOnboardingRequestParameters`): request
                parameters needed to initiate the wallet registration process.
        """
        registration_information = PersonalOnboardingRequestParameters(
            merchant_code=self.merchant_code,  # Get this from config
            first_name=customer.first_name,
            middle_name=customer.middle_name,
            last_name=customer.last_name,
            country_code="254",
            mobile_number=f"0{customer.phone_number}",
            document_number=document_number,
            document_type=document_type,
            email=customer.email,
            callback_url=self.site_url
            + "/api/v1/callbacks/sasapay/personal_onboarding/"
            + otp_event_id,
        )
        self.logger.info(f"Registration Info: {registration_information.to_dict()}")

        # Make personal on boarding request api call
        async with aiohttp.ClientSession() as session:
            response = await self.post_json_request(
                session=session,
                url=self.personal_onboarding_endpoint,
                data=registration_information.to_dict(),
            )

        if response is None:
            self.logger.critical(
                "Sasapay didn't return a response",
                extra={
                    "class": "SasapayApiClient",
                    "method": "personal_onboarding_request",
                    "customer_id": customer.id,
                },
            )
            raise ValueError("Sasapay didn't return a response")

        self.logger.info(f"Staged registration: {response}")
        # return data from callback endpoint
        return PersonalOnboardingResponseParameters(
            status=response["status"],
            response_code=response["responseCode"],
            message=response["message"],
            request_id=response["requestId"],
        )

    async def complete_registration(
        self, otp: str, request_id: str
    ) -> PersonalOnboardingConfirmationResponseParameters:
        """
        API call to complete a wallet registration.

        Args:
            request_parameters (`PersonalOnboardingConfirmation`): request
                parameters needed to complete the registration of a customer's
                wallet.
        """

        # Create personal onboarding confirmation payment event
        self.payment_events_publisher.create_event(event_id=request_id)

        # Make complete registration api call
        async with aiohttp.ClientSession() as session:
            response = await self.post_json_request(
                session=session,
                url=self.personal_onboarding_confirmation_endpoint,
                data={
                    "merchantCode": str(self.merchant_code),
                    "otp": str(otp),
                    "requestId": str(request_id),
                },
            )
            self.logger.info(f"Confirm Registration Response: {response}")

        if response["status"]:
            confirmation_data: ConfirmationResponseData = {
                "merchant_code": response["data"]["merchantCode"],
                "display_name": response["data"]["displayName"],
                "account_number": response["data"]["accountNumber"],
                "account_status": response["data"]["accountStatus"],
                "account_balance": response["data"]["accountBalance"],
            }

            return PersonalOnboardingConfirmationResponseParameters(
                status=response["status"],
                response_code=response["responseCode"],
                message=response["message"],
                data=confirmation_data,
            )

        return PersonalOnboardingConfirmationResponseParameters(
            status=response["status"],
            response_code=response["responseCode"],
            message=response["message"],
        )

    async def transfer_funds(
        self,
        amount: int,
        recepient_phone_number: int,
        external_wallet_id: str,
        event_id: str,
    ) -> TransferFundsResultsParameters | None:
        """
        API call to transfer funds from a wallet.

        Args:
            request_parameters (`TransferFundsRequestParameters`): request
                parameters needed to call the transfer funds api endpoint.
        """
        self.logger.info(
            (
                f"Transfering funds to {recepient_phone_number} from "
                "wallet of id {external_wallet_id}"
            )
        )

        # Create event
        self.payment_events_publisher.create_event(event_id=event_id)

        # Make transfer funds api call
        request_parameters = TransferFundsRequestParameters(
            merchant_code=self.merchant_code,
            transaction_reference=uuid4().hex,
            currency_code="KES",
            transaction_description="Sending money or withdrawing.",
            sender_number=external_wallet_id,
            amount=amount,
            reason="Sending money to save.",
            # `charge_account` identifies which account will be charged the
            # transaction fees
            charge_account=external_wallet_id,
            transaction_fee=0,
            channel="63902",
            receiver_number=str(recepient_phone_number),
            callback_url=self.site_url
            + "/api/v1/callbacks/sasapay/transfer_funds/"
            + event_id,
        )
        async with aiohttp.ClientSession() as session:
            response = await self.post_json_request(
                session=session,
                url=self.transfer_funds_endpoint,
                data=request_parameters.to_dict(),
            )

        if response["responseCode"] == "SP8000":
            raise Exception(f"Insufficient balance to withdraw {amount}.")

        # Wait for transfered funds payment event from callback
        transfer_funds_results = await self.payment_events_publisher.wait_for_event(
            event_id=event_id
        )

        if transfer_funds_results is None:
            self.logger.critical(
                "Sasapay didn't return any results for transfering funds.",
                extra={"class": "SasapayApiClient", "method": "transfer_funds"},
            )
            raise ValueError("Sasapay didn't return any result for transfering funds.")

        if int(transfer_funds_results.result_code) != 0:
            self.logger.warning(
                "There was an error transfering funds",
                extra={
                    "class": "SasaPayPaymentGatewayAdapter",
                    "error_code": transfer_funds_results.result_code,
                },
            )
            return None

        # return data from callback endpoint
        return transfer_funds_results

    async def request_payment(
        self,
        sender_phone_number: int,
        wallet_external_id: str,
        amount: int,
        event_id: str,
    ) -> RequestPaymentResponseParameters:
        """
        Requests payment from a phone number.

        Args:
            request_parameters (`RequestPaymentRequestParameters`): request
                parameters needed to call the request payment api endpoint.
        """
        # Make request payment api call
        request_payment_request_parameters = RequestPaymentRequestParameters(
            merchant_reference=uuid4().hex,
            network_code="63902",
            mobile_number=f"0{sender_phone_number}",
            receiver_account_number=wallet_external_id,
            amount=str(amount),
            transaction_fee="0",
            currency_code="KES",
            merchant_code=self.merchant_code,
            transaction_description="Requesting funds to wallet.",
            callback_url=self.site_url
            + "/api/v1/callbacks/sasapay/request_payment/"
            + event_id,
        )
        async with aiohttp.ClientSession() as session:
            request_payment_response_parameters = await self.post_json_request(
                session=session,
                url=self.request_payment_endpoint,
                data=request_payment_request_parameters.to_dict(),
            )

            if not request_payment_response_parameters["status"]:
                message = request_payment_response_parameters["message"]
                raise Error(f"There was a problem requesting payment: {message}")

            return RequestPaymentResponseParameters(
                status=request_payment_response_parameters["status"],
                response_code=request_payment_response_parameters["responseCode"],
                message=request_payment_response_parameters["message"],
                payment_gateway=request_payment_response_parameters["paymentGateway"],
                merchant_request_id=request_payment_response_parameters[
                    "merchantRequestID"
                ],
                checkout_request_id=request_payment_response_parameters[
                    "checkoutRequestID"
                ],
                transaction_reference=request_payment_response_parameters[
                    "transactionReference"
                ],
                customer_message=request_payment_response_parameters["customerMessage"],
            )

    async def process_payment(
        self, otp: str, external_wallet_id: str, checkout_request_id: str
    ) -> bool:
        """
        Receives a customer's otp that is sent after we make a 'request
        payment' api call.
        """
        # Create payment requested payment event
        event_id = uuid4().hex
        self.payment_events_publisher.create_event(event_id=event_id)

        otp_request_params = RequestPaymentOTPRequestParameters(
            merchant_code=self.merchant_code,
            receiver_account_number=external_wallet_id,
            checkout_request_id=checkout_request_id,
            verification_code=otp,
        )

        async with aiohttp.ClientSession() as session:
            response = await self.post_json_request(
                session=session,
                url=self.personal_onboarding_endpoint,
                data=otp_request_params.to_dict(),
            )

        if response is None:
            self.logger.critical(
                "Sasapay didn't return a response for request payment processing."
            )
            raise ValueError(
                "Sasapay didn't return a response for request payment processing."
            )

        if response["responseCode"] == 0:
            return True

        return False


@dataclass
class SasaPayPaymentGatewayAdapter(
    IRegistrationEventObserver, ISendMoneyObserver, IWithdrawObserver
):
    """
    Payment Gateway implementation for SasaPay

    Attributes:
        merchant_code (`str`): Short numeric code that is used to identify a
            merchant on sasapay's platform.
        sasapay_api_client (`SasapayApiClient`): Client that talks with sasapay
            api endpoints.
        payment_events_publisher (`IPaymentEventsPublisher`): Object that
            publishes events about payments to subscriber objects
        use_case_events_publisher (`IUseCaseEventPublisher`): Object that
            publishes events about use cases to subscriber objects
        send_money_event_publisher (`SendMoneyEventsPublisher`): Object that
            publishes events about send
        registration_info_queue (`Queue`): Async queue that is used to wait for
            registration information from the user or another object.
        request_payment_queue (`Queue`): Async queue that is used to wait for
            `request_payment` information from the user or another client.
        otp_queue (`Queue`): Async queue that is used to wait for otp
            information from the user.
        logger (`Logger`): Logger that gives information about the performance
            of the application.
        transaction_cost_brackets (`Dict`): A hashmap that stores the
            transaction costs that customers incur when transacting on sasapay.
    """

    merchant_code: str = field(init=False)
    sasapay_api_client: SasapayApiClient = field(init=False)
    send_money_event_publisher: SendMoneyEventsPublisher | None
    registration_event_publisher: RegistrationEventsPublisher | None
    withdraw_event_publisher: WithdrawEventsPublisher | None
    payment_events_publisher: PaymentEventsPublisher
    registration_info_queue: Queue
    request_payment_queue: Queue
    otp_queue: Queue
    logger: Logger
    transaction_cost_brackets: Dict

    def __init__(
        self,
        merchant_code: str,
        logger: Logger,
        sasapay_api_client: SasapayApiClient,
        payment_events_publisher: PaymentEventsPublisher,
        withdraw_event_publisher: WithdrawEventsPublisher | None = None,
        registration_event_publisher: RegistrationEventsPublisher | None = None,
        send_money_event_publisher: SendMoneyEventsPublisher | None = None,
    ) -> None:
        self.merchant_code = merchant_code
        self.sasapay_api_client = sasapay_api_client
        self.registration_event_publisher = registration_event_publisher
        self.send_money_event_publisher = send_money_event_publisher
        self.withdraw_event_publisher = withdraw_event_publisher
        self.payment_events_publisher = payment_events_publisher
        self.registration_info_queue = Queue()
        self.request_payment_queue = Queue()
        self.otp_queue = Queue()
        self.logger = logger
        self.transaction_cost_brackets = {
            (0, 49): 0,
            (50, 100): 0,
            (101, 500): 7,
            (501, 1000): 11,
            (1001, 1500): 19,
            (1501, 2500): 19,
            (2501, 3500): 24,
            (3501, 5000): 24,
            (5001, 7500): 24,
            (7501, 10000): 24,
            (10001, 15000): 29,
            (15001, 20000): 29,
            (20001, 25000): 39,
            (25001, 30000): 39,
            (30001, 35000): 39,
            (35001, 40000): 39,
            (40001, 45000): 39,
            (45001, 50000): 39,
            (50001, 70000): 39,
            (70001, 150000): 39,
        }

    async def send_money(
        self,
        total_requested_amount: int,
        original_amount: int,
        sending_phone_number: int,
        receiving_phone_number: int,
        external_wallet_id: str,
        session_id: str,
    ) -> bool:
        """
        Sends STK push to phone number and saves to the customer's wallet.

        Args:
            payment_amount (int): Amount, in shillings, of money that the
                customer is asked to pay. This is the amount they are sending
                marked up by the saving percentage set in their wallet.
            phone_number (int): Customer's phone number that is being charged.
        """
        self.logger.info("Requesting payment in payment gateway.")
        # Create callback event
        self.payment_events_publisher.create_event(event_id=session_id)

        # Request payment from api client
        request_payment_response = await self.sasapay_api_client.request_payment(
            sender_phone_number=sending_phone_number,
            wallet_external_id=external_wallet_id,
            amount=total_requested_amount,
            event_id=session_id,
        )
        self.logger.info(
            f"Received response after requesting payment: {request_payment_response}"
        )

        if self.send_money_event_publisher is None:
            raise Error("Registration event publisher is not defined.")

        await self.send_money_event_publisher.notify(
            event=SendMoneyUserPrompt(
                prompt_recepient=session_id,
                event_name="pin_prompt",
            )
        )

        callback_response = await self.payment_events_publisher.wait_for_event(
            event_id=session_id
        )

        self.logger.info(f"Received callback response: {callback_response}")

        if callback_response is None:
            self.logger.critical(
                "Sasapay didn't return a response for requesting funds."
            )

            return False

        if int(callback_response.result_code) != 0:
            await self.send_money_event_publisher.notify(
                event=SendMoneyUserPrompt(
                    prompt_recepient=session_id,
                    event_name="failed_funds_transfer",
                )
            )

            return False

        await self.send_money_event_publisher.notify(
            event=SendMoneyUserPrompt(
                prompt_recepient=session_id,
                event_name="successful_funds_request",
                data={
                    "phone_number": sending_phone_number,
                    "receiving_phone_number": receiving_phone_number,
                },
            )
        )

        transfer_funds_result = await self.sasapay_api_client.transfer_funds(
            amount=original_amount,
            recepient_phone_number=receiving_phone_number,
            external_wallet_id=external_wallet_id,
            event_id=session_id,
        )

        if transfer_funds_result is None:
            # TODO Inform user that we couldn't transfer funds
            await self.send_money_event_publisher.notify(
                event=SendMoneyUserPrompt(
                    prompt_recepient=session_id, event_name="failed_funds_transfer"
                )
            )
            return False

        await self.send_money_event_publisher.notify(
            event=SendMoneyUserPrompt(
                prompt_recepient=session_id,
                event_name="successful_funds_transfer",
                data={
                    "amount": original_amount,
                    "recepient_phone_number": receiving_phone_number,
                },
            ),
        )

        return True

    def calculate_transaction_cost(self, amount: int) -> int | None:
        """
        Calculates the transaction cost of a given amount
        """
        for (lower, upper), cost in self.transaction_cost_brackets.items():
            if lower <= amount <= upper:
                return cost

        return None

    async def register_wallet(
        self,
        customer: Customer,
        event_id: str,
        document_type: str,
        document_number: str,
    ) -> str:
        """
        Registers a sasapay wallet.

        Args:
            customer (`Customer`): Owner of the wallet being registered.
            wallet_service (`IWalletService`): Wallet service we will be
                communcating with.
        """
        self.logger.info(f"Customer information: {customer}")

        staged_registration_result = (
            await self.sasapay_api_client.personal_onboarding_request(
                customer=customer,
                otp_event_id=event_id,
                document_number=document_number,
                document_type=document_type,
            )
        )

        otp_retries_count = 1
        while True:
            # Depending on staged registration result, notify Use Case event
            # publisher of staged result
            input_name = "otp"

            if otp_retries_count > 1:
                input_name = "otp_failed"

            self.logger.info("Prompting user for OTP")

            if self.registration_event_publisher is None:
                raise Error("Registration event publisher is not defined")

            await self.registration_event_publisher.notify(
                event=RegistrationUserPrompt(
                    prompt_recepient=event_id, event_name=input_name
                )
            )

            otp_value = await self.otp_queue.get()
            print("Got otp from queue")

            otp_value = str(otp_value)

            # Complete registration with api client
            # Get registration status after sending otp which is sent by api client
            registration_info = await self.sasapay_api_client.complete_registration(
                otp=otp_value, request_id=staged_registration_result.request_id
            )

            otp_retries_count += 1
            if registration_info.response_code == "0":
                break

        if registration_info.data is not None:
            return registration_info.data["account_number"]

        raise Error("Account number was not provided")

    async def withdraw(
        self,
        amount: int,
        external_wallet_id: str,
        recepient_phone_number: int,
        session_id: str,
    ) -> bool:
        """
        Withdraws money from a sasapay wallet.

        Args:
            amount (`int`): Amount of money to withdraw from wallet.
            external_wallet_id (`str`): Unique identifier that sasapay uses to
                identify wallet to withdraw from.
        """
        self.logger.info("Withdrawing in payment gateway")
        results = await self.sasapay_api_client.transfer_funds(
            amount=amount,
            recepient_phone_number=recepient_phone_number,
            external_wallet_id=external_wallet_id,
            event_id=session_id,
        )

        if results is None:
            self.logger.critical("User was unable to withdraw")
            return False

        self.logger.info("User was able to withdraw")
        return True

    async def update(self, event: object) -> None:
        if isinstance(event, RegistrationInputReceived) and event.input_name == "otp":
            await self.otp_queue.put(event.user_input["otp"])

        if (
            isinstance(event, SendMoneyTransactionInputReceived)
            and event.input_name == "otp"
        ):
            await self.otp_queue.put(event.user_input["otp"])


@dataclass
class SasaPayPaymentGatewayAdapterFactory:
    merchant_code: str
    logger: Logger
    sasapay_api_client: SasapayApiClient
    payment_events_publisher: PaymentEventsPublisher

    def create_for_registration(
        self, registration_event_publisher: RegistrationEventsPublisher
    ):
        payment_gateway = SasaPayPaymentGatewayAdapter(
            merchant_code=self.merchant_code,
            registration_event_publisher=registration_event_publisher,
            logger=self.logger,
            sasapay_api_client=self.sasapay_api_client,
            payment_events_publisher=self.payment_events_publisher,
        )

        registration_event_publisher.subscribe(observer=payment_gateway)

        return payment_gateway

    def create_for_send_money(
        self, send_money_events_publisher: SendMoneyEventsPublisher
    ):
        payment_gateway = SasaPayPaymentGatewayAdapter(
            merchant_code=self.merchant_code,
            send_money_event_publisher=send_money_events_publisher,
            logger=self.logger,
            sasapay_api_client=self.sasapay_api_client,
            payment_events_publisher=self.payment_events_publisher,
        )

        send_money_events_publisher.subscribe(observer=payment_gateway)

        return payment_gateway

    def create_for_withdraw(
        self, withdraw_events_publisher: WithdrawEventsPublisher
    ) -> SasaPayPaymentGatewayAdapter:
        pass
        payment_gateway = SasaPayPaymentGatewayAdapter(
            merchant_code=self.merchant_code,
            withdraw_event_publisher=withdraw_events_publisher,
            logger=self.logger,
            sasapay_api_client=self.sasapay_api_client,
            payment_events_publisher=self.payment_events_publisher,
        )

        withdraw_events_publisher.subscribe(observer=payment_gateway)

        return payment_gateway
