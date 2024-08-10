from abc import ABC, abstractmethod
from typing_extensions import Dict, Generic, TypeVar

from domain.entities.users import Customer

T = TypeVar("T")


class iExternalAccountRepository(ABC, Generic[T]):
    @abstractmethod
    async def get_account_by_user(self, user_id: str) -> T:
        pass

    @abstractmethod
    async def get_owner(self, external_account_id: str) -> Customer:
        pass

    @abstractmethod
    async def save_account(self, user_id: str, account_information: Dict) -> T:
        pass
