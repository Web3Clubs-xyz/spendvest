from abc import ABC, abstractmethod

from domain.entities.sessions import SessionType, UserSession


class ISessionRepository(ABC):
    """
    Abstract class that `Session` repositories should implement
    """

    @abstractmethod
    async def get_user_session(self, external_id: str) -> UserSession | None:
        pass

    @abstractmethod
    async def save_user_session(self, session: UserSession) -> UserSession:
        pass

    @abstractmethod
    async def get_session_type(self) -> SessionType:
        pass

    @abstractmethod
    async def save_session_type(self, session_type: SessionType) -> SessionType:
        pass
