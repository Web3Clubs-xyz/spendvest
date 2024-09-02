from abc import ABC, abstractmethod
from domain.entities.users import Customer


class CustomerRepository(ABC):
    """
    Abstract interface for creating repositories for `Customer` entities
    """

    @abstractmethod
    async def create_customer(
        self,
        customer: Customer,
    ) -> Customer:
        pass

    @abstractmethod
    async def save_customer(self, customer: Customer) -> Customer:
        pass

    @abstractmethod
    async def get_customer(self, identifier: str) -> Customer | None:
        pass

    @abstractmethod
    async def get_customer_by_whatsapp_id(self, whatsapp_id: str) -> Customer | None:
        pass
