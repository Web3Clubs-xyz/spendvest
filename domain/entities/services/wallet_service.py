from asyncio import Queue
from dataclasses import dataclass
from logging import Logger
from uuid import uuid4

from domain.entities.payments import Wallet
from domain.entities.services.registration_event_publisher import (
    RegistrationCompleted,
    RegistrationEventsPublisher,
)
from domain.entities.services.send_money_events_publisher import (
    SendMoneyEventsPublisher,
    SendMoneyTransactionInputReceived,
)
from domain.entities.sessions import UserSession
from domain.entities.users import Customer
from interface_adapters.datastore.wallet_repository import SQLAlchemyWalletRepository
from interface_adapters.payments.sasapay.sasapay_payment_gateway import (
    SasaPayPaymentGatewayAdapter,
)


@dataclass
class WalletService:
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
    registration_event_publisher: RegistrationEventsPublisher
    send_money_event_publisher: SendMoneyEventsPublisher
    payment_gateway_result_queue: Queue
    use_case_strategy_result_queue: Queue
    logger: Logger

    async def get_wallet_by_id(self, wallet_id: str) -> Wallet:
        return await self.repository.get_wallet_by_id(wallet_id=wallet_id)

    async def get_wallet_by_customer_id(self, customer_id: str) -> Wallet:
        return await self.repository.get_wallet_by_customer_id(customer_id=customer_id)

    async def create_wallet(
        self,
        customer: Customer,
        saving_percentage: int,
        event_id: str,
        document_type: str,
        document_number: str,
    ) -> Wallet:
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
        await self.registration_event_publisher.notify(
            event=RegistrationCompleted(prompt_recepient=event_id)
        )

        return wallet

    async def send_money(
        self,
        amount: int,
        recepient_number: int,
        session: UserSession,
    ) -> int:
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

        # use payment gateway to request payment and transfer funds in two event loops.
        await self.wallet_payment_gateway.send_money(
            payment_amount=amount,
            sending_phone_number=customer.phone_number,
            receiving_phone_number=recepient_number,
            external_wallet_id=wallet.external_id,
            session_id=session.id,
        )

        return amount

    async def withdraw(
        self, wallet: Wallet, amount: int, receiving_phone_number: int
    ) -> int:
        # Use payment gateway to transfer funds.
        await self.wallet_payment_gateway.withdraw(
            amount=amount,
            external_wallet_id=wallet.external_id,
            recepient_phone_number=receiving_phone_number,
        )

        return amount

    async def update(self, event: object):
        if (
            isinstance(event, SendMoneyTransactionInputReceived)
            and event.input_name == "send_money_info"
        ):
            send_money_info = event.user_input["send_money_info"]
            await self.send_money(
                amount=send_money_info["payment_amount"],
                recepient_number=send_money_info["receiving_phone_number"],
                session=send_money_info["session"],
            )
