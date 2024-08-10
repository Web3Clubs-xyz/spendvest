from abc import ABC, abstractmethod
from asyncio import Queue
from dataclasses import dataclass, field
import math
from uuid import uuid4
from typing_extensions import override

from domain.entities.interfaces.payments_interfaces import (
    IWalletPaymentGateway,
    IWalletRepository,
)
from domain.entities.payments import IWallet, WalletFactory, WalletType
from domain.entities.users import Customer
from domain.usecases.interfaces.register_account_interfaces import (
    IRegisterCustomerAccountStrategy,
)
from domain.usecases.register_account import ProcessCompleted


class IWalletService(ABC):
    """
    Abstract wallet interface

    Interface for concrete wallet services to implement and for use
    cases to use as dependencies.

    Attributes:
        payment_gateway (`IPaymentGateway`): Payment gateway the wallet uses to
            process transactions.

    Methods:
        get_wallet_by_id(wallet_id: `str`):
            Fetches a wallet by its ID
        get_wallet_by_customer_id(customer_id: `str`):
            Fetches a wallet by its owner's id
        create_wallet(wallet_type_id: `int`, customer: `Customer`): Creates a
            wallet for a user.
        send_money(
            wallet: IWallet,
            amount: int,
            saving_percentage: int,
            recepient_number: int,
        ): Sends money to a beneficiary.
        withdraw(wallet: `IWallet`, amount: `int`): Withdraws money from a
            customer's account.
        calculate_mark_up(amount: `int`, saving_percentage: `int`): Calculates
            markup for a transaction based on a customer's saving percentage.
        calculate_mark_down(amount: `int`, saving_percentage: `int`):
            Calculates calculates the original amount a customer intended to
            send based on their saving percentage and the total amount that is
            going to be charged from their account.
        calculate_transaction_cost(amount: `int`): Calculates the cost of a transaction
            based on the bracket a transaction amount falls under.
        update(event: `object`): Updates wallet service on registration events
            it has subscribed to.
    """

    @property
    @abstractmethod
    def payment_gateway(self) -> IWalletPaymentGateway:
        pass

    @payment_gateway.setter
    @abstractmethod
    def payment_gateway(self, payment_gateway: IWalletPaymentGateway) -> None:
        pass

    @abstractmethod
    async def get_wallet_by_id(self, wallet_id: str) -> IWallet:
        """
        Abstract method that retrieves a `Wallet` by its ID.

        Args:
            wallet_id (str): ID of the wallet being retrieved
        """
        pass

    @abstractmethod
    async def get_wallet_by_customer_id(self, customer_id: str) -> IWallet:
        """
        Abstract method that retrieves a `Wallet` by their owner's id.

        Args:
            customer_id (str): ID that uniquely identifies a customer
        """
        pass

    @abstractmethod
    async def create_wallet(
        self, customer: Customer, saving_percentage: int, event_id: str
    ) -> None:
        """
        Abstract method that creates a `Wallet`

        Args:
            `wallet (IWallet)`: Wallet that is being created
            `customer (Customer)`: Owner of the wallet
        """
        pass

    @abstractmethod
    async def send_money(
        self,
        wallet: IWallet,
        amount: int,
        saving_percentage: int,
        recepient_number: int,
    ) -> int:
        """
        Saves money to the wallet

        Args:
            wallet (`Wallet`): Wallet that is saving money.
            amount (`int`): Amount in cents to be sent to a mobile number.
            saving_percentage (`int`): Percentage of transaction amount to be saved.
            recepient_number (`int`): Mobile number of the recepient of the funds.

        Returns:
            int: The amount, in cents, that has been saved
        """
        pass

    @abstractmethod
    async def withdraw(self, wallet: IWallet, amount: int) -> int:
        """
        Abstract method for withdrawing from a wallet.

        Args:
            wallet (`IWallet`): Wallet the user is withdrawing from
            amount (`int`): Amount in cents that is being withdrawn
        """
        pass

    @abstractmethod
    def calculate_mark_up(self, amount: int, saving_percentage: int) -> int:
        """
        Abstract method that should be implemented to find the mark-up that
        needs to be added to the amount the customer is sending in order to
        meet their savings goals.
        """
        pass

    @abstractmethod
    def calculate_mark_down(self, total_amount: int, saving_percentage: int) -> int:
        """
        Abstract method that should be implemented to find the original amount
        being sent from the total that includes the markup that is being saved
        by the customer.
        """
        pass

    @abstractmethod
    def calculate_transaction_cost(self, amount: int) -> int:
        """
        Abstract method for calculating transaction costs of a given amount of
        money.

        Args:
            amount (`int`): Amount of money we are calculating the transaction
                cost for.
        """
        pass


@dataclass
class WalletService(IWalletService):
    """
    Wallet service that coordinates interaction with user wallets.

    Attributes:
        repository (`IWalletRepository`): Repository that persists and
            retrieves wallet data from the datastore.

    Methods:
        update(event: `object`): Updates the wallet service on registration
            events it has subscribed to.
    """

    _repository: IWalletRepository = field(init=False)
    _wallet_payment_gateway: IWalletPaymentGateway = field(init=False)
    payment_gateway_result_queue: Queue
    use_case_strategy_result_queue: Queue
    register_account_strategy: IRegisterCustomerAccountStrategy

    def __init__(
        self,
        repository: IWalletRepository,
        payment_gateway: IWalletPaymentGateway,
        register_account_strategy: IRegisterCustomerAccountStrategy,
    ) -> None:
        self._repository = repository
        self._wallet_payment_gateway = payment_gateway
        self.register_account_strategy = register_account_strategy

    @property
    def payment_gateway(self) -> IWalletPaymentGateway:
        return self._wallet_payment_gateway

    @payment_gateway.setter
    def payment_gateway(self, payment_gateway: IWalletPaymentGateway) -> None:
        self._wallet_payment_gateway = payment_gateway

    @override
    async def get_wallet_by_id(self, wallet_id: str) -> IWallet:
        return await super().get_wallet_by_id(wallet_id)

    @override
    async def get_wallet_by_customer_id(self, customer_id: str) -> IWallet:
        return await super().get_wallet_by_customer_id(customer_id)

    @override
    async def create_wallet(
        self, customer: Customer, saving_percentage: int, event_id: str
    ) -> None:
        external_id = await self._wallet_payment_gateway.register_wallet(
            customer=customer, event_id=event_id
        )
        wallet = WalletFactory().create_wallet(
            savings_percentage=saving_percentage,
            customer=customer,
            wallet_id=uuid4().hex,
            wallet_type=WalletType(id=1, name="SASAPAY_WALLET"),
            external_id=external_id,
        )
        await self._repository.save_wallet(wallet=wallet)

        await self.register_account_strategy.notify(event=ProcessCompleted())

    @override
    async def send_money(
        self,
        wallet: IWallet,
        amount: int,
        saving_percentage: int,
        recepient_number: int,
    ) -> int:
        # use payment gateway to request payment and transfer funds in two event loops.
        raise NotImplementedError

    @override
    async def withdraw(self, wallet: IWallet, amount: int) -> int:
        # Use payment gateway to transfer funds.
        return await super().withdraw(wallet, amount)

    @override
    def calculate_mark_up(self, amount: int, saving_percentage: int) -> int:
        return math.ceil(amount + (amount * saving_percentage * 0.01))

    @override
    def calculate_mark_down(self, total_amount: int, saving_percentage: int) -> int:
        percentage_operand = 1 + (saving_percentage * 0.01)

        return math.ceil(total_amount / percentage_operand)
