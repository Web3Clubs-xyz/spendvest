from dataclasses import field
from typing_extensions import Optional


class Customer:
    """
    Customer entity

    Attributes:
        id (`str`): ID that uniquely identifies a user in the system
        phone_number (`int`): The User's phone number
        first_name (`str`): Customer's first name as seen on their ID document
        middle_name (`str`): Customer's middle name as seen on their ID document
        last_name (`str`): Customers's last name as seen on their ID document
        email (`str`): Customer's email
    """

    id: str = field(init=False)
    phone_number: int = field(init=False)
    first_name: str = field(init=False)
    middle_name: str = field(init=False)
    last_name: str = field(init=False)
    email: str = field(init=False)
    whatsapp: Optional[str]

    def __init__(
        self,
        id: str,
        phone_number: int,
        first_name: str,
        middle_name: str,
        last_name: str,
        email: str,
        whatsapp: str,
    ) -> None:
        self.id = id
        self._phone_number = phone_number
        self._first_name = first_name
        self._middle_name = middle_name
        self._last_name = last_name
        self.email = email
        self.whatsapp = whatsapp


class CustomerUserFactory:
    """
    Factory class that contains factory method for creating a customer instance.
    """

    def create_customer(
        self,
        id: str,
        phone_number: int,
        first_name: str,
        middle_name: str,
        last_name: str,
        email: str,
        whatsapp_id: str,
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
            id=id,
            phone_number=phone_number,
            first_name=first_name,
            middle_name=middle_name,
            last_name=last_name,
            email=email,
            whatsapp=whatsapp_id,
        )
