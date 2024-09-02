from abc import ABC, abstractmethod
from typing_extensions import Generic, TypeVar

T = TypeVar("T")


class ResponseChannel(ABC, Generic[T]):
    """
    Abstract interface to be implemented by response channels
    """

    @abstractmethod
    async def send(self, message: T):
        pass


class UIContext(ABC):
    """
    Abstract context that should be implemented context objects.
    """

    @property
    @abstractmethod
    def user_id(self) -> str:
        pass

    @user_id.setter
    @abstractmethod
    def user_id(self, user_id: str) -> None:
        pass

    @property
    @abstractmethod
    def response_channel(self) -> ResponseChannel:
        pass

    @response_channel.setter
    @abstractmethod
    def response_channel(self, response_channel: ResponseChannel) -> None:
        pass
