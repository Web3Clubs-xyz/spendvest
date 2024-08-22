from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from domain.entities.payments import Wallet
from domain.entities.users import Customer


@dataclass
class RegisterCustomerAccountInput:
    """
    This is the interface data structure that will be the contract for
    communication between controllers and the user registration use case

    Attributes:
        `phone_number (int)`: Country-Code-Prefixed phone number of user
        registering the account
        `first_name (str)`: First name of the account holder
        `middle_name (str)`: Middle name of the account holder
        `last_name (str)`: Last name of the account holder
    """

    _phone_number: int = field(init=False)
    _first_name: str = field(init=False)
    _middle_name: str = field(init=False)
    _last_name: str = field(init=False)
    _wallet_type_id: int = field(init=False)

    def __init__(
        self,
        phone_number: int,
        first_name: str,
        middle_name: str,
        last_name: str,
        wallet_type_id: int,
    ) -> None:
        self._phone_number = phone_number
        self._first_name = first_name
        self._middle_name = middle_name
        self._last_name = last_name
        self._wallet_type_id = wallet_type_id

    @property
    def phone_number(self) -> int:
        return self._phone_number

    @phone_number.setter
    def phone_number(self, phone_number: int) -> None:
        self._phone_number = phone_number

    @property
    def first_name(self) -> str:
        return self._name

    @first_name.setter
    def first_name(self, name: str) -> None:
        self._name = name

    @property
    def middle_name(self) -> str:
        return self._name

    @middle_name.setter
    def middle_name(self, name: str) -> None:
        self._name = name

    @property
    def last_name(self) -> str:
        return self._name

    @last_name.setter
    def last_name(self, name: str) -> None:
        self._name = name

    @property
    def wallet_type_id(self) -> int:
        return self._wallet_type_id

    @wallet_type_id.setter
    def wallet_type_id(self, wallet_type_id: int) -> None:
        self._wallet_type_id = wallet_type_id


@dataclass
class RegisterCustomerAccountOutput:
    """
    This is the interface output data structure that will be the contract for
    communication between the registration use case and the presenters

    Attributes:
        `customer_account (Customer)`: The recently created customer account
        `wallet (IWallet)`: The customer's wallet
    """

    _customer_account: Customer = field(init=False)
    _wallet: Wallet = field(init=False)

    def __init__(self, customer_account: Customer, wallet: Wallet) -> None:
        self._customer_account = customer_account
        self._wallet = wallet

    @property
    def customer_account(self) -> Customer:
        return self._customer_account

    @customer_account.setter
    def customer_account(self, customer_account: Customer) -> None:
        self._customer_account = customer_account

    @property
    def wallet(self) -> Wallet:
        return self._wallet

    @wallet.setter
    def wallet(self, wallet: Wallet) -> None:
        self._wallet = wallet


class IRegistrationEventObserver(ABC):
    """
    Abstract registration event observer.

    Interface to be implemented by registration event observers.

    Methods:
        update(event: `object`): Updates the observer on events that it has
            subscribed to.
    """

    @abstractmethod
    async def update(self, event: object) -> None:
        pass
