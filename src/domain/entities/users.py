from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class User(ABC):
    """
    User Entity.

    Attributes:
        id (`str`): Unique identifier of a user in the system.
        first_name (`str`): User's first name.
        middle_name ('str'): User's middle name.
        last_name (`str`): User's last name.
    """

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
    def first_name(self) -> str:
        pass

    @first_name.setter
    @abstractmethod
    def first_name(self, first_name: str) -> None:
        pass

    @property
    @abstractmethod
    def middle_name(self) -> str:
        pass

    @middle_name.setter
    @abstractmethod
    def middle_name(self, middle_name: str) -> None:
        pass

    @property
    @abstractmethod
    def last_name(self) -> str:
        pass

    @last_name.setter
    @abstractmethod
    def last_name(self, last_name: str) -> None:
        pass


@dataclass
class Customer(User):
    """
    Customer entity

    Attributes:
        `customer_id (str)`: ID that uniquely identifies a user in the system
        `phone_number (int)`: The User's phone number
        `first_name (str)`: Customer's first name as seen on their ID document
        `middle_name (str)`: Customer's middle name as seen on their ID document
        `last_name (str)`: Customers's last name as seen on their ID document
        email (`str`): Customer's email
        identifying_document (`str`): Customer's identifying document
        identifying_document_number (`str`): Number on customer's identifying document
    """

    _customer_id: str = field(init=False)
    _phone_number: int = field(init=False)
    _first_name: str = field(init=False)
    _middle_name: str = field(init=False)
    _last_name: str = field(init=False)
    _email: str = field(init=False)
    _identifying_document: str = field(init=False)
    _identifying_document_number: str = field(init=False)

    def __init__(
        self,
        customer_id: str,
        phone_number: int,
        first_name: str,
        middle_name: str,
        last_name: str,
        email: str,
        identifying_document: str,
        identifying_document_number: str,
    ) -> None:
        self._customer_id = customer_id
        self._phone_number = phone_number
        self._first_name = first_name
        self._middle_name = middle_name
        self._last_name = last_name
        self.email = email
        self._identifying_document = identifying_document
        self._identifying_document_number = identifying_document_number

    @property
    def id(self) -> str:
        return self._id

    @id.setter
    def id(self, id: str) -> None:
        self._id = id

    @property
    def first_name(self) -> str:
        return self._first_name

    @first_name.setter
    def first_name(self, first_name: str) -> None:
        self._first_name = first_name

    @property
    def middle_name(self) -> str:
        return self._middle_name

    @middle_name.setter
    def middle_name(self, middle_name: str) -> None:
        self._middle_name = middle_name

    @property
    def last_name(self) -> str:
        return self._last_name

    @last_name.setter
    def last_name(self, last_name: str) -> None:
        self._last_name = last_name

    @property
    def phone_number(self) -> int:
        return self._phone_number

    @phone_number.setter
    def phone_number(self, phone_number: int) -> None:
        self._phone_number = phone_number

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, email: str) -> None:
        self._email = email

    @property
    def identifying_document(self) -> str:
        return self._identifying_document

    @identifying_document.setter
    def identifying_document(self, identifying_document: str) -> None:
        self._identifying_document = identifying_document

    @property
    def identifying_document_number(self) -> str:
        return self._identifying_document_number

    @identifying_document_number.setter
    def identifying_document_number(self, identifying_document_number: str) -> None:
        self._identifying_document_number = identifying_document_number


class CustomerUserFactory:
    """
    Factory class that contains factory method for creating a customer instance.
    """

    def create_customer(
        self,
        customer_id: str,
        phone_number: int,
        first_name: str,
        middle_name: str,
        last_name: str,
        email: str,
        identifying_document: str,
        identifying_document_number: str,
    ) -> Customer:
        """
        Abstract method that should be overriden by concrete implementations to
        create a `Customer` object

        Args:
            `id (str)`: The unique identifier for a customer in the system
            `phone_name (int)`: The customer's phone_number
            `first_name (str)`: First name of the customer as it appears on
                their identification document
            `last_name (str)`: Last name of the customer as it appears on their
                identification document
            `middle_name (str)`: Middle name of the customer as it appears on
                their identification document
        """
        return Customer(
            customer_id=customer_id,
            phone_number=phone_number,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            email=email,
            identifying_document=identifying_document,
            identifying_document_number=identifying_document_number,
        )
