from abc import ABC, abstractmethod
from dataclasses import dataclass

from domain.entities.sessions import UserSession
from interface_adapters.datastore.session_repository import SQLAlchemySessionRepository


class ISessionService(ABC):
    """
    Abstract Session service.

    Interface to be implemented by concrete session services and be used as
    dependency for controllers and use cases.

    Methods:
        get_customer_session(external_id: `str`) -> UserSession | None:
            Fetches a user's current session.
        save_customer_session(customer_session: `UserSession`) -> UserSession:
            Saves a user's session.
    """

    @abstractmethod
    async def get_customer_session(self, external_id: str) -> UserSession | None:
        pass

    @abstractmethod
    async def save_customer_session(self, customer_session: UserSession) -> UserSession:
        pass


@dataclass
class SessionService:
    """
    Domain level service that maintains a user's transaction sessions. For
    example a `Send Money` session or `Withdraw` session.

    Attributes:
        `repository (ISessionRepository)`: Repository that persists session
            data in the data store
    """

    repository: SQLAlchemySessionRepository

    async def get_customer_session(self, external_id: str) -> UserSession | None:
        user_session = await self.repository.get_user_session(session_id=external_id)

        return user_session

    async def save_customer_session(self, customer_session: UserSession) -> UserSession:
        user_session = await self.repository.save_user_session(
            customer_session=customer_session
        )

        return user_session

    async def delete_customer_session(self, customer_session: UserSession) -> bool:
        deleted = await self.repository.delete_customer_session(
            customer_session=customer_session
        )

        return deleted
