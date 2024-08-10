from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing_extensions import Dict, Generic, TypeVar, override

from domain.entities.interfaces.external_accounts_interfaces import (
    iExternalAccountRepository,
)
from domain.entities.users import Customer

T = TypeVar("T")


class IExternalAccountService(ABC, Generic[T]):
    @abstractmethod
    async def fetch_account(self, user_id: str) -> T:
        pass

    @abstractmethod
    async def fetch_owner(self, external_account_id: str) -> Customer | None:
        pass

    @abstractmethod
    async def update_account(self, user_id: str, account_data: Dict) -> T:
        pass


@dataclass
class WhatsappAccountInformation:
    pass


@dataclass
class WhatsappAccountService(IExternalAccountService[WhatsappAccountInformation]):
    repository: iExternalAccountRepository

    @override
    async def fetch_account(self, user_id: str) -> WhatsappAccountInformation:
        account = await self.repository.get_account_by_user(user_id=user_id)

        return account

    @override
    async def fetch_owner(self, external_account_id: str) -> Customer | None:
        customer = await self.repository.get_owner(
            external_account_id=external_account_id
        )

        return customer

    @override
    async def update_account(
        self, user_id: str, account_data: Dict
    ) -> WhatsappAccountInformation:
        account = await self.repository.save_account(
            user_id=user_id, account_information=account_data
        )

        return account
