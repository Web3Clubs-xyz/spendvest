from abc import ABC, abstractmethod
from typing_extensions import Any

from domain.entities.sessions import UserSession


class IRegistrationController(ABC):
    """
    Abstract Registration Controller.

    Interface to be implemented by concrete controllers and be used as
    abstract dependency for views.

    Methods:
        register_user(session_id: `str`) -> None:
            Registers a user
        emit_registration_event(event_id: `str`, event_type: `str`) -> None:
            Emits event to notify registration state machines.
    """

    @abstractmethod
    async def register_user(self, session: UserSession) -> None:
        pass

    @abstractmethod
    async def emit_registration_event(self, session: UserSession, data: Any) -> None:
        pass


class INewSessionController(ABC):
    """
    Abstract new session controller.

    Interface to be implemented by concrete controllers and be used as abstract
    dependency for views.

    Methods:
        create_session(external_id: `str`, session_type: `str`) -> None:
            creates a session for a user
    """

    @abstractmethod
    async def create_session(self, external_id: str, session_type: str) -> None:
        pass


class ISendMoneyController(ABC):
    """
    Abstract 'send money' controller.

    Interface to be implemented by concrete controllers and be used as abstract
    dependency for views.

    Methods:
        send_money(input: `SendMoneyInput`) -> None:
            Sends money to a phone number.
        emit_send_money_event(event_id: `str`, event_type: `str`) -> None:
            Emits event to notify send money observers and update send money
            state machines.
    """

    @abstractmethod
    async def send_money(self) -> None:
        pass

    @abstractmethod
    async def emit_send_money_event(self, session: UserSession, data: Any) -> None:
        pass


class IWithdrawController(ABC):
    """
    Abstract withdraw controller.

    Interface to be implemented by concrete controllers and to be used as
    abstract dependency for views.

    Methods:
        withdraw(input: `WithdrawInput`) -> None:
            Withdraws funds from a user's wallet
        emit_withdraw_event(event_id: str, event_type: str) -> None:
            Emits event to notify withdraw observers and update withdraw state
            machines.
    """

    @abstractmethod
    async def withdraw(self) -> None:
        pass

    @abstractmethod
    async def emit_withdraw_event(self, session: UserSession, data: Any) -> None:
        pass


class IInvalidInputController(ABC):
    """
    Abstract invalid input controller.

    Interface to be implemented by concrete controllers and be used as abstract
    dependency for views.

    Methods:
        reject_input() -> None:
            Rejects the user's input
    """

    @abstractmethod
    async def reject_input(self) -> None:
        pass
