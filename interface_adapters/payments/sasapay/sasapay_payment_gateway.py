from asyncio import Queue
from dataclasses import dataclass, field
from logging import Logger
import math
from typing import Any, AsyncGenerator, Dict
from uuid import uuid4
from aiohttp import ClientSession
import aiohttp
from domain.entities.services.registration_event_publisher import (
    RegistrationEventsPublisher,
    RegistrationInputReceived,
    RegistrationInputRequired,
)
from domain.entities.services.send_money_events_publisher import (
    SendMoneyEventsPublisher,
    SendMoneyTransactionInputReceived,
)
from domain.entities.users import Customer
from domain.usecases.interfaces.register_account_interfaces import (
    IRegistrationEventObserver,
)
from interface_adapters.payments.sasapay.api_data_types import (
    PersonalOnboardingConfirmation,
    PersonalOnboardingConfirmationResponseParameters,
    PersonalOnboardingRequestParameters,
    PersonalOnboardingResponseParameters,
    RequestPaymentCallbackResultsParameters,
    RequestPaymentOTPRequestParameters,
    RequestPaymentRequestParameters,
    RequestPaymentResponseParameters,
    TransferFundsRequestParameters,
    TransferFundsResultsParameters,
)

from interface_adapters.payments.sasapay.payment_events_publisher import (
    PaymentEventsPublisher,
)


class SasapayApiClient:
    """
    API client that talks to sasapay's api.
    """

    personal_onboarding_endpoint: str
    access_token: str
    request_payment_endpoint: str
    transfer_funds_endpoint: str
    site_url: str
    merchant_code: str
    sasapay_headers: Dict
    payment_events_publisher: PaymentEventsPublisher
    logger: Logger

    async def post_json_request(self, session: ClientSession, url: str, data: Dict):
        self.sasapay_headers.update({"Authorization": f"Bearer {self.access_token}"})
        async with session.post(
            url, json=data, headers=self.sasapay_headers
        ) as response:
            return response

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
            mobile_number=str(customer.phone_number),
            document_number=document_number,
            document_type=document_type,
            email=customer.email,
            callback_url=self.site_url
            + "/api/v1/callbacks/sasapay/personal_onboarding/"
            + otp_event_id,
        )
        # create personal onboarding response payment event
        self.payment_events_publisher.create_event(event_id=otp_event_id)
        # Make personal on boarding request api call
        async with aiohttp.ClientSession() as session:
            await self.post_json_request(
                session=session,
                url=self.personal_onboarding_endpoint,
                data=registration_information.to_dict(),
            )

        # Wait for personal onboarding response payment event from callback
        callback_response = await self.payment_events_publisher.wait_for_event(
            event_id=otp_event_id, timeout=False
        )

        if callback_response is None:
            self.logger.critical(
                "Sasapay didn't return a response",
                extra={
                    "class": "SasapayApiClient",
                    "method": "personal_onboarding_request",
                    "customer_id": customer.id,
                },
            )
            raise ValueError("Sasapay didn't return a response")

        self.logger.info(
            "Staged registration", extra={"request_id": callback_response["request_id"]}
        )
        # return data from callback endpoint
        return PersonalOnboardingResponseParameters(
            status=callback_response["Status"],
            response_code=callback_response["ResponseCode"],
            message=callback_response["message"],
            request_id=callback_response["request_id"],
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
        confirmation_data = PersonalOnboardingConfirmation(
            merchant_code=self.merchant_code, otp=otp, request_id=request_id
        )

        # Create personal onboarding confirmation payment event
        self.payment_events_publisher.create_event(event_id=request_id)

        # Make complete registration api call
        async with aiohttp.ClientSession() as session:
            await self.post_json_request(
                session=session,
                url=self.personal_onboarding_endpoint,
                data={
                    "MerchantCode": self.merchant_code,
                    "ConfirmationCode": confirmation_data.otp,
                    "RequestId": confirmation_data.request_id,
                },
            )

        # Wait for confirmed registration payment event from callback
        registration_results = await self.payment_events_publisher.wait_for_event(
            event_id=request_id
        )

        if registration_results is None:
            self.logger.critical(
                "Sasapay didn't return a response to complete account registration.",
                extra={"class": "SasapayApiClient", "method": "complete_registration"},
            )
            raise ValueError(
                "Sasapay didn't return a response for account registration."
            )

        # return data from callback endpoint
        return PersonalOnboardingConfirmationResponseParameters(
            status=registration_results["Status"],
            response_code=registration_results["ResponseCode"],
            message=registration_results["Message"],
            data=registration_results["Data"],
        )

    async def transfer_funds(
        self,
        amount: int,
        recepient_phone_number: int,
        external_wallet_id: str,
    ) -> TransferFundsResultsParameters:
        """
        API call to transfer funds from a wallet.

        Args:
            request_parameters (`TransferFundsRequestParameters`): request
                parameters needed to call the transfer funds api endpoint.
        """
        # Create transfered funds payment events
        event_id = uuid4().hex
        self.payment_events_publisher.create_event(event_id=event_id)

        # Make transfer funds api call
        request_parameters = TransferFundsRequestParameters(
            merchant_code=self.merchant_code,
            transaction_reference=event_id,
            currency_code="KES",
            transaction_description="Sending money or withdrawing.",
            sender_number=external_wallet_id,
            amount=amount,
            reason="",
            # `charge_account` identifies which account will be charged the
            # transaction fees
            charge_account="2822",
            transaction_fee=0,
            channel="01",
            receiver_number=str(recepient_phone_number),
            callback_url=self.site_url
            + "/api/v1/callbacks/sasapay/transfer_funds/"
            + event_id,
        )
        async with aiohttp.ClientSession() as session:
            await self.post_json_request(
                session=session,
                url=self.personal_onboarding_endpoint,
                data=request_parameters.to_dict(),
            )

        # Wait for transfered funds payment event from callback
        transfer_funds_results = await self.payment_events_publisher.wait_for_event(
            event_id=event_id, timeout=False
        )

        if transfer_funds_results is None:
            self.logger.critical(
                "Sasapay didn't return any results for transfering funds.",
                extra={"class": "SasapayApiClient", "method": "transfer_funds"},
            )
            raise ValueError("Sasapay didn't return any result for transfering funds.")

        # return data from callback endpoint
        return TransferFundsResultsParameters(
            merchant_request_id=transfer_funds_results["MerchantRequestId"],
            checkout_request_id=transfer_funds_results["CheckoutRequestId"],
            result_code=transfer_funds_results["ResultCode"],
            result_description=transfer_funds_results["ResultDescription"],
            merchant_code=transfer_funds_results["MerchantCode"],
            transaction_amount=transfer_funds_results["TransactionAmount"],
            transaction_charge=transfer_funds_results["TransactionCharge"],
            merchant_fees=transfer_funds_results["MerchantFees"],
            merchant_account_balance=transfer_funds_results["MerchantAccountBalance"],
            merchant_transaction_reference=transfer_funds_results[
                "MerchantTransactionReference"
            ],
            transaction_date=transfer_funds_results["TransactionDate"],
            recepient_account_number=transfer_funds_results["RecepientAccountNumber"],
            destination_channel=transfer_funds_results["DestinationChannel"],
            source_channel=transfer_funds_results["SourceChannel"],
            sasapay_transaction_id=transfer_funds_results["SasapayTransactionId"],
            recepient_name=transfer_funds_results["RecepientName"],
            sender_account_number=transfer_funds_results["SenderAccountNumber"],
        )

    async def request_payment(
        self,
        sender_phone_number: int,
        wallet_external_id: str,
        amount: int,
    ) -> AsyncGenerator[
        RequestPaymentResponseParameters | RequestPaymentCallbackResultsParameters, Any
    ]:
        """
        Requests payment from a phone number.

        Args:
            request_parameters (`RequestPaymentRequestParameters`): request
                parameters needed to call the request payment api endpoint.
        """
        # Create payment requested payment event
        event_id = uuid4().hex
        self.payment_events_publisher.create_event(event_id=event_id)

        # Make request payment api call
        request_payment_request_parameters = RequestPaymentRequestParameters(
            merchant_reference=event_id,
            network_code="63902",
            mobile_number=str(sender_phone_number),
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
            response = await self.post_json_request(
                session=session,
                url=self.personal_onboarding_endpoint,
                data=request_payment_request_parameters.to_dict(),
            )
            request_payment_response_parameters = await response.json()

            yield RequestPaymentResponseParameters(
                status=request_payment_response_parameters["status"],
                response_code=request_payment_response_parameters["responseCode"],
                message=request_payment_response_parameters["message"],
                payment_gateway=request_payment_response_parameters["paymentGateway"],
                checkout_request_id=request_payment_response_parameters[
                    "checkoutRequestId"
                ],
                merchant_reference=request_payment_response_parameters[
                    "merchantReference"
                ],
                customer_message=request_payment_response_parameters["customerMessage"],
            )

        # Wait for payment requested payment event from callback
        request_payment_results = await self.payment_events_publisher.wait_for_event(
            event_id=event_id, timeout=False
        )

        if request_payment_results is None:
            self.logger.critical(
                (
                    "Sasapay didn't return a result after "
                    "requesting payment from phone number."
                ),
                extra={"class": "SasapayApiClient", "method": "request_payment"},
            )
            raise ValueError("Couldn't request payment from customer.")

        # return data from callback endpoint
        results = RequestPaymentCallbackResultsParameters(
            merchant_request_id=request_payment_results["MerchantRequestId"],
            payment_request_id=request_payment_results["PaymentRequestId"],
            result_code=request_payment_results["ResultCode"],
            result_description=request_payment_results["ResultDescription"],
            source_channel=request_payment_results["SourceChannel"],
            transaction_amount=request_payment_results["TransactionAmount"],
            bill_reference_number=request_payment_results["BillReferenceNumber"],
            transaction_date=request_payment_results["TransactionDate"],
            customer_mobile=request_payment_results["CustomerMobile"],
            transaction_code=request_payment_results["TransactionCode"],
            third_party_transaction_id=request_payment_results[
                "ThirdPartyTransactionId"
            ],
            checkout_request_id=request_payment_results["CheckoutRequestId"],
        )

        yield results

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
            response_data = await response.json()

        if response is None:
            self.logger.critical(
                "Sasapay didn't return a response for request payment processing."
            )
            raise ValueError(
                "Sasapay didn't return a response for request payment processing."
            )

        if response_data["responseCode"] == 0:
            return True

        return False


@dataclass
class SasaPayPaymentGatewayAdapter(IRegistrationEventObserver):
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
    send_money_event_publisher: SendMoneyEventsPublisher
    registration_info_queue: Queue
    request_payment_queue: Queue
    otp_queue: Queue
    logger: Logger
    transaction_cost_brackets: Dict = field(
        default_factory=lambda: {
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
    )

    def __init__(
        self,
        merchant_code: str,
        registration_event_publisher: RegistrationEventsPublisher,
        send_money_event_publisher: SendMoneyEventsPublisher,
    ) -> None:
        self.merchant_code = merchant_code
        self.sasapay_api_client = SasapayApiClient()
        self.send_money_event_publisher = send_money_event_publisher
        self.registration_event_publisher = registration_event_publisher
        self.registration_event_publisher.subscribe(self)
        self.registration_info_queue = Queue()
        self.request_payment_queue = Queue()
        self.otp_queue = Queue()

    def calculate_mark_up(self, amount: int, saving_percentage: int) -> int:
        return math.ceil(amount * (saving_percentage * 0.01))

    def calculate_mark_down(self, total_amount: int, saving_percentage: int) -> int:
        percentage_operand = 1 + (saving_percentage * 0.01)

        return math.ceil(total_amount / percentage_operand)

    async def send_money(
        self,
        payment_amount: int,
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
        # Request payment from api client
        request_payment_iterator = self.sasapay_api_client.request_payment(
            sender_phone_number=sending_phone_number,
            wallet_external_id=external_wallet_id,
            amount=payment_amount,
        )

        request_payment_response = await anext(request_payment_iterator)

        await self.registration_event_publisher.notify(
            event=RegistrationInputRequired(
                prompt_recepient=session_id, input_name="otp"
            )
        )

        otp_value = await self.otp_queue.get()

        processing_payment = await self.sasapay_api_client.process_payment(
            otp=otp_value,
            external_wallet_id=external_wallet_id,
            checkout_request_id=request_payment_response.to_dict()["checkoutRequestId"],
        )

        if processing_payment:
            request_payment_callback_results = await anext(request_payment_iterator)
            # TODO Inform user we requested payment successfully.
            self.logger.info(
                "Requested payment successfully",
                extra={
                    "class": "SasaPayPaymentGatewayAdapter",
                    "request_payment_info": request_payment_callback_results,
                    "external_wallet_id": external_wallet_id,
                    "session_id": session_id,
                },
            )

        # Transfer funds using api client

        transfer_funds_result = await self.sasapay_api_client.transfer_funds(
            amount=payment_amount,
            recepient_phone_number=receiving_phone_number,
            external_wallet_id=external_wallet_id,
        )

        if transfer_funds_result.to_dict()["ResultCode"] != "0":
            self.logger.warning(
                "There was an error transfering funds",
                extra={
                    "class": "SasaPayPaymentGatewayAdapter",
                    "error_code": transfer_funds_result.to_dict()["ResultCode"],
                },
            )
            # TODO Inform user that we couldn't transfer funds
            return False

        return True

    def calculate_transaction_cost(self, amount: int) -> int | None:
        """
        Calculates the transaction cost of a given amount
        """
        for (lower, upper), cost in self.transaction_cost_brackets:
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

        staged_registration_result = (
            await self.sasapay_api_client.personal_onboarding_request(
                customer=customer,
                otp_event_id=event_id,
                document_number=document_number,
                document_type=document_type,
            )
        )

        while True:
            # Depending on staged registration result, notify Use Case event
            # publisher of staged result

            await self.registration_event_publisher.notify(
                event=RegistrationInputRequired(
                    prompt_recepient=event_id, input_name="otp"
                )
            )

            otp_value = await self.otp_queue.get()

            otp_value = str(otp_value)

            # Complete registration with api client
            # Get registration status after sending otp which is sent by api client
            registration_status = await self.sasapay_api_client.complete_registration(
                otp=otp_value, request_id=staged_registration_result.request_id
            )

            if registration_status.response_code == 0:
                break

        return registration_status.data["account_number"]

    async def withdraw(
        self, amount: int, external_wallet_id: str, recepient_phone_number: int
    ) -> bool:
        """
        Withdraws money from a sasapay wallet.

        Args:
            amount (`int`): Amount of money to withdraw from wallet.
            external_wallet_id (`str`): Unique identifier that sasapay uses to
                identify wallet to withdraw from.
        """
        results = await self.sasapay_api_client.transfer_funds(
            amount=amount,
            recepient_phone_number=recepient_phone_number,
            external_wallet_id=external_wallet_id,
        )

        if results.result_code != "0":
            self.logger.warning(
                "Couldn't transfer funds for customer",
                extra={
                    "class": "SasaPayPaymentGatewayAdapter",
                    "error_code": results.result_code,
                    "external_wallet_id": external_wallet_id,
                },
            )
            return False

        return True

    async def update(self, event: object) -> None:

        if (
            isinstance(event, RegistrationInputReceived)
            and event.input_name == "registration_otp"
        ):
            await self.otp_queue.put(event.user_input["otp"])

        if (
            isinstance(event, SendMoneyTransactionInputReceived)
            and event.input_name == "send_money_otp"
        ):
            await self.otp_queue.put(event.user_input["otp"])
