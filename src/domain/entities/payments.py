from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing_extensions import override
from domain.entities.users import Customer


@dataclass
class WalletType:
    """
    Entity representing wallet types.

    Attributes:
        `id (int)`: Unique identifier of the wallet type
        `name (str)`: Name of the wallet type
    """

    _id: int
    _name: str

    def __init__(self, id: int, name: str) -> None:
        self._id = id
        self._name = name

    @property
    def id(self) -> int:
        return self._id

    @id.setter
    def id(self, id: int) -> None:
        self._id = id

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        self._name = name


class IWallet(ABC):
    """
    Abstract class representing the user's wallet entity in the system. We
    don't store balances here since we will be using event sourcing to
    calculate balances

    Attributes:
        `savings_percentage (int)`: Percentage markup that will be saved by a
            user on each transaction
        `customer (Customer)`: The owner of the wallet
        `wallet_id (str)`: Unique identifier of the wallet
        `external_id (str)`: Unique identifier used by the payment gateway
        `wallet_type (WalletType)`: Object identifying what the type of wallet is
    """

    @property
    @abstractmethod
    def savings_percentage(self) -> int:
        pass

    @savings_percentage.setter
    @abstractmethod
    def savings_percentage(self, savings_percentage: int) -> None:
        pass

    @property
    @abstractmethod
    def customer(self) -> Customer:
        pass

    @customer.setter
    @abstractmethod
    def customer(self, customer: Customer) -> None:
        pass

    @property
    @abstractmethod
    def id(self) -> str:
        pass

    @id.setter
    @abstractmethod
    def id(self, id: str) -> None:
        pass

    @property
    @abstractmethod
    def external_id(self) -> str:
        pass

    @external_id.setter
    @abstractmethod
    def external_id(self, external_id: str) -> None:
        pass

    @property
    @abstractmethod
    def wallet_type(self) -> WalletType:
        pass

    @wallet_type.setter
    @abstractmethod
    def wallet_type(self, wallet_type: WalletType) -> None:
        pass


class IWalletFactory(ABC):
    @abstractmethod
    def create_wallet(
        self,
        savings_percentage: int,
        customer: Customer,
        wallet_id: str,
        wallet_type: WalletType,
        external_id: str,
    ) -> IWallet:
        pass


@dataclass
class Wallet(IWallet):
    """
    Represents a customer's wallet entity in the system.

    Attributes:
        savings_percentage (`int`): Percentage markup that will be saved by a
            user on each transaction
        customer (`Customer`): The owner of the wallet
        wallet_id (`str`): Unique identifier of the wallet
        wallet_type (`WalletType`): Object representing the wallet type.
        external_id (`str`): Unique identifier used by an external wallet
            provider to identify a wallet on their platform
    """

    _savings_percentage: int = field(init=False)
    _customer: Customer = field(init=False)
    _wallet_id: str = field(init=False)
    _wallet_type: WalletType = field(init=False)
    _external_id: str = field(init=False)

    def __init__(
        self,
        savings_percentage: int,
        customer: Customer,
        wallet_id: str,
        wallet_type: WalletType,
        external_id: str,
    ) -> None:
        self._savings_percentage = savings_percentage
        self._customer = customer
        self._wallet_id = wallet_id
        self._wallet_type = wallet_type
        self._external_id = external_id

    @property
    def savings_percentage(self) -> int:
        return self._savings_percentage

    @savings_percentage.setter
    def savings_percentage(self, savings_percentage: int) -> None:
        self._savings_percentage = savings_percentage

    @property
    def customer(self) -> Customer:
        return self._customer

    @customer.setter
    def customer(self, customer: Customer) -> None:
        self._customer = customer

    @property
    def wallet_id(self) -> str:
        return self._wallet_id

    @wallet_id.setter
    def id(self, id: str) -> None:
        self._wallet_id = id

    @property
    def external_id(self) -> str:
        return self._external_id

    @external_id.setter
    def external_id(self, external_id: str) -> None:
        self._external_id = external_id

    @property
    def wallet_type(self) -> WalletType:
        return self._wallet_type

    @wallet_type.setter
    def wallet_type(self, wallet_type: WalletType) -> None:
        self._wallet_type = wallet_type


@dataclass
class WalletFactory(IWalletFactory):

    @override
    def create_wallet(
        self,
        savings_percentage: int,
        customer: Customer,
        wallet_id: str,
        wallet_type: WalletType,
        external_id: str,
    ) -> IWallet:
        return Wallet(
            savings_percentage=savings_percentage,
            customer=customer,
            wallet_id=wallet_id,
            wallet_type=wallet_type,
            external_id=external_id,
        )
