from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing_extensions import Dict

from domain.entities.payments import IWallet
from domain.entities.services.user_registration_service import (
    ICustomerRegistrationService,
)
from domain.entities.sessions import UserSession
from domain.entities.users import Customer
from domain.usecases.interfaces.presenter_interfaces import (
    IRegisterSasapayWalletPresenter,
)
from interface_adapters.ui.controllers.session_event_publisher import (
    IUseCaseEventPublisher,
)


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
    _wallet: IWallet = field(init=False)

    def __init__(self, customer_account: Customer, wallet: IWallet) -> None:
        self._customer_account = customer_account
        self._wallet = wallet

    @property
    def customer_account(self) -> Customer:
        return self._customer_account

    @customer_account.setter
    def customer_account(self, customer_account: Customer) -> None:
        self._customer_account = customer_account

    @property
    def wallet(self) -> IWallet:
        return self._wallet

    @wallet.setter
    def wallet(self, wallet: IWallet) -> None:
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


class IRegisterCustomerAccountStrategy(ABC):
    """
    Abstract class to be implemented by customer account registration
    strategies.

    Methods:
        subscribe(observer: `IRegistrationEventObserver`): Subscribes observers
            to events.
        unsubscribe(observer: `IRegistrationEventObserver`): Unsubscribes
            observers from events.
        notify(event: `object`): Notifies observers of events.
        start(): Starts the registration process.
        process_user_input(): Processes user input to manage the registration
            process state and notifies observers of user input.
    """

    @abstractmethod
    def subscribe(self, observer: IRegistrationEventObserver) -> None:
        """
        Abstract method that should be implemented to subscribe observers to
        published events.

        Args:
            observer (`IRegistrationEventObserver`): Object observing user
                registration events.
        """
        pass

    @abstractmethod
    def unsubscribe(self, observer: IRegistrationEventObserver) -> None:
        """
        Abstract method that should be implemented to unsubscribe observers
        from published events.

        Args:
            observer (`IRegistrationEventObserver`): Observer being unsubscribed
        """
        pass

    @abstractmethod
    async def notify(self, event: object) -> None:
        """
        Abstract method implemented to notify subscribed object of an event
        that has occured.

        Args:
            event (`object`): Event to be processed by observers listening to
                events.
        """
        pass

    @abstractmethod
    async def start(self, session_id: str) -> None:
        """
        Abstract method that should be implemented to start the registration
        process.
        """
        pass

    @abstractmethod
    async def process_user_input(self, user_input: Dict) -> None:
        """
        Abstract method that should be implemented to process user input at
        each step.

        Args:
            user_input (`Dict`): Data collected from the user to be processed
                by an observer listening to an event.
        """
        pass


class IRegisterCustomerAccountUseCase(IRegistrationEventObserver, ABC):
    """
    Abstract use case for registering a customer's account.

    Interface to be implemented by use cases that register customer accounts
    and to be used as dependency by controllers.

    Methods:
        register(session_id: str) -> `None`:
            Registers a user
        update(event: `object`): Updates the registration use case on events it
            has subscribed to.
    """

    @property
    @abstractmethod
    def registration_strategy(self) -> IRegisterCustomerAccountStrategy:
        pass

    @registration_strategy.setter
    @abstractmethod
    def registration_strategy(
        self, registration_strategy: IRegisterCustomerAccountStrategy
    ) -> None:
        pass

    @property
    @abstractmethod
    def user_registration_service(self) -> ICustomerRegistrationService:
        pass

    @user_registration_service.setter
    @abstractmethod
    def user_registration_service(
        self, user_registration_service: ICustomerRegistrationService
    ) -> None:
        pass

    @property
    @abstractmethod
    def presenter(self) -> IRegisterSasapayWalletPresenter:
        pass

    @presenter.setter
    @abstractmethod
    def presenter(self, presenter: IRegisterSasapayWalletPresenter) -> None:
        pass

    @property
    @abstractmethod
    def ui_event_publisher(self) -> IUseCaseEventPublisher:
        pass

    @ui_event_publisher.setter
    @abstractmethod
    def ui_event_publisher(self, ui_event_publisher: IUseCaseEventPublisher) -> None:
        pass

    @abstractmethod
    async def register(self, session_id: str) -> None:
        """
        Abstract method which use cases that register customer accounts must
        override

        Args:
            session_id (`str`): id of the user's session
        """
        pass

    @abstractmethod
    async def update(self, event: object) -> None:
        """
        Abstract method that should be implemented to handle events the
        registration use case has subscribed to.

        Args:
            event (`object`): Event the registration use case has subscribed to.
        """
        pass
