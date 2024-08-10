from abc import ABC, abstractmethod
from asyncio import Queue
from dataclasses import dataclass, field
from typing import Dict
from typing_extensions import override
from domain.entities.interfaces.payments_interfaces import (
    IWalletPaymentGateway,
    IWalletPaymentGatewayFactory,
)
from domain.entities.users import Customer
from domain.usecases.interfaces.register_account_interfaces import (
    IRegisterCustomerAccountStrategy,
)
from domain.usecases.register_account import (
    ProcessCompleted,
    UserInputReceived,
    UserInputRequired,
)
from interface_adapters.payments.sasapay.api_data_types import (
    PersonalOnboardingConfirmationResponseParameters,
    PersonalOnboardingRequestParameters,
    PersonalOnboardingResponseParameters,
    RequestPaymentRequestParameters,
    TransferFundsRequestParameters,
)

from interface_adapters.payments.sasapay.payment_events_publisher import (
    IPaymentEventsPublisher,
)
from interface_adapters.ui.controllers.session_event_publisher import (
    IUseCaseEventPublisher,
)


class ISasapayApiClient(ABC):
    @abstractmethod
    async def personal_onboarding_request(
        self, customer: Customer, otp_event_id: str
    ) -> PersonalOnboardingResponseParameters:
        pass

    @abstractmethod
    async def complete_registration(
        self, otp: str, request_id: str
    ) -> PersonalOnboardingConfirmationResponseParameters:
        pass

    @abstractmethod
    async def transfer_funds(self, request_parameters: TransferFundsRequestParameters):
        pass

    @abstractmethod
    async def request_payment(
        self, request_parameters: RequestPaymentRequestParameters
    ) -> bool:
        pass


class SasapayApiClient(ISasapayApiClient):
    personal_onboarding_endpoint: str
    request_payment_endpoint: str
    transfer_funds_endpoint: str
    personal_onboarding_callback_url: str
    request_payment_callback_url: str
    transfer_funds_callback_url: str
    merchant_code: str

    async def personal_onboarding_request(
        self, customer: Customer, otp_event_id: str
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
            document_number=customer.identifying_document_number,
            document_type=customer.identifying_document,
            email=customer.email,
            callback_url=self.personal_onboarding_callback_url + otp_event_id,
        )
        # create personal onboarding response payment event
        # Make personal on boarding request api call
        # Wait for personal onboarding response payment event from callback
        # return data from callback endpoint
        raise NotImplementedError

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
        # Make complete registration api call
        # Wait for confirmed registration payment event from callback
        # return data from callback endpoint
        raise NotImplementedError

    async def transfer_funds(self, request_parameters: TransferFundsRequestParameters):
        """
        API call to transfer funds from a wallet.

        Args:
            request_parameters (`TransferFundsRequestParameters`): request
                parameters needed to call the transfer funds api endpoint.
        """
        # Create transfered funds payment events
        # Make transfer funds api call
        # Wait for transfered funds payment event from callback
        # return data from callback endpoint
        raise NotImplementedError

    async def request_payment(
        self, request_parameters: RequestPaymentRequestParameters
    ) -> bool:
        """
        Requests payment from a phone number.

        Args:
            request_parameters (`RequestPaymentRequestParameters`): request
                parameters needed to call the request payment api endpoint.
        """
        # Create payment requested payment event
        # Make request payment api call
        # Wait for payment requested payment event from callback
        # return data from callback endpoint
        raise NotImplementedError


class ISasapayApiClientFactory(ABC):
    @abstractmethod
    def create(self) -> ISasapayApiClient:
        pass


class SasapayApiClientFactory(ISasapayApiClientFactory):
    @override
    def create(self) -> ISasapayApiClient:
        return SasapayApiClient()


@dataclass
class SasaPayPaymentGatewayAdapter(IWalletPaymentGateway):
    """
    Payment Gateway implementation for SasaPay
    """

    merchant_code: str = field(init=False)
    sasapay_api_client_factory: ISasapayApiClientFactory = field(init=False)
    sasapay_api_client: ISasapayApiClient = field(init=False)
    payment_events_publisher: IPaymentEventsPublisher
    use_case_events_publisher: IUseCaseEventPublisher
    registration_info_queue: Queue
    otp_queue: Queue
    transaction_cost_brackets: Dict = {
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

    def __init__(
        self,
        merchant_code: str,
        sasapay_payment_gateway_factory: ISasapayApiClientFactory,
        payment_events_publisher: IPaymentEventsPublisher,
        register_customer_strategy: IRegisterCustomerAccountStrategy,
    ) -> None:
        self.merchant_code = merchant_code
        self.sasapay_api_client_factory = sasapay_payment_gateway_factory
        self.sasapay_api_client = self.sasapay_api_client_factory.create()
        self.payment_events_publisher = payment_events_publisher
        self.regiister_customer_strategy = register_customer_strategy
        self.regiister_customer_strategy.subscribe(self)
        self.registration_info_queue = Queue()
        self.otp_queue = Queue()

    @override
    async def send_money(
        self,
        payment_amount: int,
        sending_phone_number: int,
        receiving_phone_number: int,
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

        # Transfer funds using api client

        return True

    @override
    def calculate_transaction_cost(self, amount: int) -> int | None:
        """
        Calculates the transaction cost of a given amount
        """
        for (lower, upper), cost in self.transaction_cost_brackets:
            if lower <= amount <= upper:
                return cost

        return None

    @override
    async def register_wallet(
        self,
        customer: Customer,
        event_id: str,
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
                customer=customer, otp_event_id=event_id
            )
        )

        # Depending on staged registration result, notify Use Case event publisher of
        # staged result

        await self.regiister_customer_strategy.notify(
            event=UserInputRequired(step_name="OTP", prompt_recepient=event_id)
        )

        otp_value = await self.otp_queue.get()

        otp_value = str(otp_value)

        # Complete registration with api client
        # Get registration status after sending otp which is sent by api client
        registration_status = await self.sasapay_api_client.complete_registration(
            otp=otp_value, request_id=staged_registration_result.request_id
        )

        await self.regiister_customer_strategy.notify(event=ProcessCompleted())

        return registration_status.data["account_number"]

    @override
    async def withdraw(self, amount: int, external_wallet_id: str) -> bool:
        """
        Withdraws money from a sasapay wallet.

        Args:
            amount (`int`): Amount of money to withdraw from wallet.
            external_wallet_id (`str`): Unique identifier that sasapay uses to
                identify wallet to withdraw from.
        """
        return await super().withdraw(amount, external_wallet_id)

    @override
    async def update(self, event: object) -> None:
        if isinstance(event, UserInputReceived):
            step_name = event.step_name

            match step_name:
                case "OTP":
                    await self.otp_queue.put(event.user_input)
                case _:
                    pass


class SasapayPaymentGatewayAdapterFactory(IWalletPaymentGatewayFactory):
    @override
    def create_wallet_payment_gateway(
        self,
        *,
        merchant_code: str,
        sasapay_payment_gateway_factory: ISasapayApiClientFactory,
        register_customer_strategy: IRegisterCustomerAccountStrategy,
        payment_events_publisher: IPaymentEventsPublisher,
        **kwargs,
    ) -> IWalletPaymentGateway:
        return SasaPayPaymentGatewayAdapter(
            merchant_code=merchant_code,
            sasapay_payment_gateway_factory=sasapay_payment_gateway_factory,
            register_customer_strategy=register_customer_strategy,
            payment_events_publisher=payment_events_publisher,
        )
