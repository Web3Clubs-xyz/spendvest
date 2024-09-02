from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from logging import Logger
from typing import Dict, List, Optional

from domain.entities.sessions import UserSession


@dataclass
class WithdrawInputRequired:
    input_name: str
    prompt_recepient: str


@dataclass
class WithdrawInputReceived:
    input_name: str
    user_input: Dict


@dataclass
class WithdrawUserPrompt:
    event_name: str
    prompt_recepient: str
    data: Optional[Dict] = None


@dataclass
class WithdrawFailed:
    prompt_recepient: str


@dataclass
class WithdrawError:
    error: Exception


@dataclass
class WithdrawCompleted:
    pass


class IWithdrawObserver(ABC):
    @abstractmethod
    async def update(self, event: object) -> None:
        pass


@dataclass
class WithdrawEventsPublisher:
    """
    Manages communication between components that are communicating during the
    withdrawal process.
    """

    logger: Logger
    observers: List[IWithdrawObserver] = field(default_factory=list)

    def subscribe(self, observer: IWithdrawObserver) -> None:
        self.observers.append(observer)

    def unsubscribe(self, observer: IWithdrawObserver):
        self.observers.remove(observer)

    async def notify(self, event: object):
        try:
            for observer in self.observers:
                await observer.update(event)
        except Exception as e:
            self.logger.error(f"There was an error while sending money {str(e)}")
            await self.notify(event=WithdrawError(error=e))

    async def start(self, session: UserSession) -> None:
        if session.user is None:
            self.logger.warning("Unregistered user withdrawing money.")
            raise ValueError("Unregistered user withdrawing money.")

        username = session.user.first_name + " " + session.user.last_name
        self.logger.info(
            "Starting withdraw process.",
            extra={
                "class": "WithdrawEventsPublisher",
                "session": session.id,
                "user": username,
            },
        )
        await self.notify(
            event=WithdrawUserPrompt(
                event_name="withdraw_info", prompt_recepient=session.id
            )
        )
