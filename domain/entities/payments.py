from dataclasses import field
from domain.entities.users import Customer


class Wallet:
    """
    Represents a customer's wallet entity in the system.

    Attributes:
        savings_percentage (`int`): Percentage markup that will be saved by a
            user on each transaction
        customer (`Customer`): The owner of the wallet
        wallet_id (`str`): Unique identifier of the wallet
        external_id (`str`): Unique identifier used by an external wallet
            provider to identify a wallet on their platform
    """

    _savings_percentage: int = field(init=False)
    _customer: Customer = field(init=False)
    _wallet_id: str = field(init=False)
    _external_id: str = field(init=False)

    def __init__(
        self,
        savings_percentage: int,
        customer: Customer,
        wallet_id: str,
        external_id: str,
    ) -> None:
        self._savings_percentage = savings_percentage
        self._customer = customer
        self._wallet_id = wallet_id
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
