from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing_extensions import override
from domain.entities.interfaces.user_interfaces import CustomerRepository
from domain.entities.users import Customer
from interface_adapters.datastore.customer_repository import (
    SQLAlchemyCustomerRepository,
)


class ICustomerService(ABC):
    @property
    @abstractmethod
    def repository(self) -> CustomerRepository:
        pass

    @repository.setter
    @abstractmethod
    def repository(self, repository: CustomerRepository) -> None:
        pass

    @abstractmethod
    async def save_customer(self, customer: Customer) -> Customer:
        pass

    @abstractmethod
    async def get_customer(self, id: str) -> Customer | None:
        pass

    @abstractmethod
    async def create_customer(
        self,
        customer: Customer,
    ) -> Customer:
        pass

    @abstractmethod
    async def get_customer_by_whatsapp_id(self, whatsapp_id: str) -> Customer | None:
        pass


@dataclass
class CustomerService:
    repository: SQLAlchemyCustomerRepository = field(init=False)

    async def save_customer(self, customer: Customer) -> Customer:
        return await self.repository.save_customer(customer)

    async def get_customer(self, id: str) -> Customer | None:
        customer: Customer | None = await self.repository.get_customer(id)

        return customer

    async def get_customer_by_whatsapp_id(self, whatsapp_id: str) -> Customer | None:
        customer = await self.repository.get_customer_by_whatsapp_id(
            whatsapp_id=whatsapp_id
        )

        return customer

    async def create_customer(
        self,
        customer: Customer,
    ) -> Customer:
        return await self.repository.create_customer(
            customer=customer,
        )
