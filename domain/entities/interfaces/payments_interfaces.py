from abc import ABC, abstractmethod

from domain.entities.users import Customer
from domain.usecases.interfaces.register_account_interfaces import (
    IRegistrationEventObserver,
)


class IPaymentGateway(ABC):
    """
    Abstract payment gateway.

    Payment gateway interface that entities can interact with.

    Methods:
        send_money(
            payment_amount: `int`,
            sending_phone_number: `int`,
            receiving_phone_number: `int`,
        ):
            Sends Money.
        request_payment(amount: `int`):
            Requests payment from a mobile phone number.
        calculate_transaction_cost(amount: `int`):
            Calculates payment gateway transaction costs for a given amount of money.
    """

    @abstractmethod
    async def send_money(
        self,
        payment_amount: int,
        sending_phone_number: int,
        receiving_phone_number: int,
    ) -> bool:
        """
        Abstract method that sends a payment to a payment gateway
        implementation

        Args:
            payment_amount (`int`): Amount of money, in cents, being paid out
            sending_phone_number (`int`): Sender's phone number
            receiver_phone_number (`int`): Receiver's phone number

        Returns:
            bool: The status of the transaction
        """
        pass

    @abstractmethod
    def calculate_transaction_cost(self, amount: int) -> int | None:
        """
        Abstract method for calculating transaction costs.

        Args:
            amount (`int`): Amount of money we are calculating the transaction
                cost for.
        """
        pass


class IWalletPaymentGateway(IPaymentGateway, IRegistrationEventObserver):
    """
    Abstract wallet payment gateway.

    Interface for payment gateways that support wallet creation.

    Methods:
        register_wallet(registration_information: `Dict`): Registers a payment
            gateway wallet.
        withdraw(amount: `int`, external_wallet_id: `str`): Withdraws from wallet
        wallet_callback(event_type: `str`, data: `Any`): receives data from the
            wallet service asynchronously.
        update(event: `object`): Updates payment gateway on events it has
            subscribed to.
    """

    @abstractmethod
    async def register_wallet(self, customer: Customer, event_id: str) -> str:
        """
        Abstract method that should be overriden to register a wallet with the
        payment gateway.
        """
        pass

    @abstractmethod
    async def withdraw(self, amount: int, external_wallet_id: str) -> bool:
        """
        Abstract method for withdrawing from a wallet.

        Args:
            amount (`int`): Amount to withdraw from wallet.
            external_wallet_id (`str`): Unique identifier that the external
                payment provider will use to identify the wallet to withdraw from.
        """
        pass


class IPaymentGatewayFactory(ABC):
    @abstractmethod
    def create_payment_gateway(self, **kwargs) -> IPaymentGateway:
        pass


class IWalletPaymentGatewayFactory(ABC):
    @abstractmethod
    def create_wallet_payment_gateway(self, **kwargs) -> IWalletPaymentGateway:
        pass
