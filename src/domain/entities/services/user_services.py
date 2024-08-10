from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing_extensions import override
from domain.entities.interfaces.user_interfaces import CustomerRepository
from domain.entities.users import Customer


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


@dataclass
class CustomerService(ICustomerService):
    _repository: CustomerRepository = field(init=False)

    def __init__(self, repository: CustomerRepository) -> None:
        self._repository = repository

    @property
    def repository(self) -> CustomerRepository:
        return self._repository

    @repository.setter
    def repository(self, repository: CustomerRepository) -> None:
        self._repository = repository

    @override
    async def save_customer(self, customer: Customer) -> Customer:
        return await self.repository.save_customer(customer)

    @override
    async def get_customer(self, id: str) -> Customer | None:
        customer: Customer | None = await self.repository.get_customer(id)

        if customer is None:
            return None

        return customer

    @override
    async def create_customer(
        self,
        customer: Customer,
    ) -> Customer:
        return await self.repository.create_customer(
            customer=customer,
        )
