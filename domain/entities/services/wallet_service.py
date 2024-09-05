from asyncio import Queue
from configparser import Error
from dataclasses import dataclass
from logging import Logger
import math
from uuid import uuid4

from apscheduler.util import re

from domain.entities.payments import Wallet
from domain.entities.services.registration_event_publisher import (
    RegistrationEventsPublisher,
)
from domain.entities.services.send_money_events_publisher import (
    ISendMoneyObserver,
    SendMoneyEventsPublisher,
    SendMoneyTransactionCompleted,
    SendMoneyTransactionFailed,
    SendMoneyTransactionInputReceived,
)
from domain.entities.services.withdraw_event_publisher import (
    IWithdrawObserver,
    WithdrawEventsPublisher,
    WithdrawFailed,
    WithdrawInputReceived,
    WithdrawUserPrompt,
)
from domain.entities.sessions import UserSession
from domain.entities.users import Customer
from domain.usecases.interfaces.register_account_interfaces import (
    IRegistrationEventObserver,
)
from interface_adapters.datastore.wallet_repository import SQLAlchemyWalletRepository
from interface_adapters.payments.sasapay.sasapay_payment_gateway import (
    SasaPayPaymentGatewayAdapter,
    SasaPayPaymentGatewayAdapterFactory,
)


@dataclass
class WalletService(IRegistrationEventObserver, ISendMoneyObserver, IWithdrawObserver):
    """
    Wallet service that coordinates interaction with user wallets.

    Attributes:
        repository (`WalletRepository`): Repository that persists and
            retrieves wallet data from the datastore.

    Methods:
        update(event: `object`): Updates the wallet service on registration
            events it has subscribed to.
    """

    repository: SQLAlchemyWalletRepository
    wallet_payment_gateway: SasaPayPaymentGatewayAdapter
    registration_event_publisher: RegistrationEventsPublisher | None
    send_money_events_publisher: SendMoneyEventsPublisher | None
    withdraw_events_publisher: WithdrawEventsPublisher | None
    payment_gateway_result_queue: Queue
    use_case_strategy_result_queue: Queue
    logger: Logger

    def __init__(
        self,
        repository: SQLAlchemyWalletRepository,
        wallet_payment_gateway: SasaPayPaymentGatewayAdapter,
        logger: Logger,
        registration_event_publisher: RegistrationEventsPublisher | None = None,
        send_money_events_publisher: SendMoneyEventsPublisher | None = None,
        withdraw_events_publisher: WithdrawEventsPublisher | None = None,
        payment_gateway_result_queue: Queue = Queue(),
        use_case_strategy_result_queue: Queue = Queue(),
    ) -> None:
        self.repository = repository
        self.wallet_payment_gateway = wallet_payment_gateway
        self.registration_event_publisher = registration_event_publisher
        self.send_money_events_publisher = send_money_events_publisher
        self.withdraw_events_publisher = withdraw_events_publisher
        self.payment_gateway_result_queue = payment_gateway_result_queue
        self.use_case_strategy_result_queue = use_case_strategy_result_queue
        self.logger = logger

    async def get_wallet_by_id(self, wallet_id: str) -> Wallet:
        return await self.repository.get_wallet_by_id(wallet_id=wallet_id)

    async def get_wallet_by_customer_id(self, customer_id: str) -> Wallet:
        return await self.repository.get_wallet_by_customer_id(customer_id=customer_id)

    async def get_wallet_by_session_id(self, session_id: str) -> Wallet:
        return await self.repository.get_wallet_by_session_id(session_id=session_id)

    async def create_wallet(
        self,
        customer: Customer,
        saving_percentage: int,
        event_id: str,
        document_type: str,
        document_number: str,
    ) -> Wallet:
        print(f"Creating Wallet for customer {customer.id}")

        try:
            external_id = await self.wallet_payment_gateway.register_wallet(
                customer=customer,
                event_id=event_id,
                document_type=document_type,
                document_number=document_number,
            )
            wallet = Wallet(
                savings_percentage=saving_percentage,
                customer=customer,
                wallet_id=uuid4().hex,
                external_id=external_id,
            )
            wallet = await self.repository.save_wallet(wallet=wallet)

            return wallet

        except Exception as e:
            print(f"There was a problem creating a wallet: {str(e)}")
            raise Error("Wallet Creation Error:")

    def sanitise_phone_number(self, phone_number: str) -> str | None:
        phone_number = phone_number.replace(" ", "")
        pattern = r"\+?.*?(\d{9})$"
        match = re.search(pattern, phone_number)

        if match:
            rest_of_phone_number = match.group(1)

            return rest_of_phone_number

        return None

    async def send_money(
        self,
        amount: int,
        recepient_number: int,
        session: UserSession,
    ) -> int | None:
        self.logger.info("Sending money in wallet.")
        customer = session.user

        if customer is None:
            self.logger.warning(
                "Customer doesn't exist in session", extra={"class": "WalletService"}
            )
            raise ValueError("Customer is not registered")

        # Get customer's wallet from repository
        wallet = await self.repository.get_wallet_by_customer_id(
            customer_id=customer.id
        )
        self.logger.info(f"Fetched registered user wallet {wallet}")

        # Marked up amount
        markup = math.ceil(amount * (wallet.savings_percentage * 0.01))
        transaction_cost = self.wallet_payment_gateway.calculate_transaction_cost(
            amount=amount
        )

        self.logger.info(f"Transaction cost: {transaction_cost}")

        if self.send_money_events_publisher is None:
            raise Error("Send money events publisher is not defined")

        if transaction_cost is None:
            await self.send_money_events_publisher.notify(
                event=SendMoneyTransactionFailed(
                    prompt_recepient=session.id,
                    reason="You can only send a maximum of KES 150,000/=",
                )
            )
            self.logger.warning(
                "Customer trying to send more money than sasapay allows."
            )

            raise Error("Transaction amount exceeds sasapay limit.")

        amount_to_request = amount + markup + transaction_cost

        # use payment gateway to request payment and transfer funds in two
        # event loops.
        self.logger.info("Calling send_money method.")
        status = await self.wallet_payment_gateway.send_money(
            total_requested_amount=amount_to_request,
            original_amount=amount,
            sending_phone_number=customer.phone_number,
            receiving_phone_number=recepient_number,
            external_wallet_id=wallet.external_id,
            session_id=session.id,
        )

        if status:
            await self.send_money_events_publisher.notify(
                event=SendMoneyTransactionCompleted()
            )

        return amount

    async def withdraw(
        self, amount: int, receiving_phone_number: int, session_id: str
    ) -> int:
        self.logger.info("Withdrawing from wallet service.")
        wallet = await self.get_wallet_by_session_id(session_id=session_id)

        # Use payment gateway to transfer funds.
        status = await self.wallet_payment_gateway.withdraw(
            amount=amount,
            external_wallet_id=wallet.external_id,
            recepient_phone_number=receiving_phone_number,
            session_id=session_id,
        )

        if self.withdraw_events_publisher is None:
            raise Error("Withdraw events publisher is not defined.")

        if not status:
            await self.withdraw_events_publisher.notify(
                event=WithdrawFailed(prompt_recepient=session_id)
            )

            return amount

        await self.withdraw_events_publisher.notify(
            event=WithdrawUserPrompt(
                event_name="successful_withdraw",
                prompt_recepient=session_id,
                data={"amount": amount},
            )
        )

        return amount

    async def update(self, event: object):
        if (
            isinstance(event, SendMoneyTransactionInputReceived)
            and event.input_name == "send_money_info"
        ):
            phone_number = self.sanitise_phone_number(
                phone_number=event.user_input["receiving_phone_number"]
            )

            if phone_number is None:
                raise ValueError("Phone number is invalid")

            await self.send_money(
                amount=event.user_input["payment_amount"],
                recepient_number=int(phone_number),
                session=event.user_input["session"],
            )

        if (
            isinstance(event, WithdrawInputReceived)
            and event.input_name == "withdraw_info"
        ):
            self.logger.info("Received withdraw input from event bus")
            phone_number = self.sanitise_phone_number(
                phone_number=event.user_input["receiving_phone_number"]
            )

            if phone_number is None:
                raise ValueError("Phone number is invalid")

            await self.withdraw(
                amount=event.user_input["amount"],
                receiving_phone_number=int(phone_number),
                session_id=event.user_input["session_id"],
            )


@dataclass
class WalletServiceFactory:
    repository: SQLAlchemyWalletRepository
    wallet_payment_gateway_factory: SasaPayPaymentGatewayAdapterFactory
    logger: Logger

    def create_for_registration(
        self, registration_event_publisher: RegistrationEventsPublisher
    ) -> WalletService:
        payment_gateway = self.wallet_payment_gateway_factory.create_for_registration(
            registration_event_publisher=registration_event_publisher
        )
        wallet_service = WalletService(
            repository=self.repository,
            wallet_payment_gateway=payment_gateway,
            registration_event_publisher=registration_event_publisher,
            logger=self.logger,
        )

        self.logger.debug("Subscribing wallet service")
        registration_event_publisher.subscribe(wallet_service)

        return wallet_service

    def create_for_send_money(
        self, send_money_events_publisher: SendMoneyEventsPublisher
    ) -> WalletService:
        payment_gateway = self.wallet_payment_gateway_factory.create_for_send_money(
            send_money_events_publisher=send_money_events_publisher
        )
        wallet_service = WalletService(
            repository=self.repository,
            wallet_payment_gateway=payment_gateway,
            send_money_events_publisher=send_money_events_publisher,
            logger=self.logger,
        )

        send_money_events_publisher.subscribe(observer=wallet_service)

        return wallet_service

    def create_for_withdraw(
        self, withdraw_events_publisher: WithdrawEventsPublisher
    ) -> WalletService:
        payment_gateway = self.wallet_payment_gateway_factory.create_for_withdraw(
            withdraw_events_publisher=withdraw_events_publisher
        )
        wallet_service = WalletService(
            repository=self.repository,
            wallet_payment_gateway=payment_gateway,
            withdraw_events_publisher=withdraw_events_publisher,
            logger=self.logger,
        )

        self.logger.debug("Subscribing wallet service")
        withdraw_events_publisher.subscribe(wallet_service)

        return wallet_service
