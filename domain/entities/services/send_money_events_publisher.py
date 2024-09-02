from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from logging import Logger
from typing import Dict, List, Optional

from domain.entities.sessions import UserSession


@dataclass
class SendMoneyTransactionInputRequired:
    input_name: str
    prompt_recepient: str


@dataclass
class SendMoneyTransactionInputReceived:
    input_name: str
    user_input: Dict


@dataclass
class SendMoneyUserPrompt:
    event_name: str
    prompt_recepient: str
    data: Optional[Dict] = None


@dataclass
class SendMoneyTransactionFailed:
    prompt_recepient: str
    reason: str


@dataclass
class SendMoneyError:
    error: Exception


@dataclass
class SendMoneyTransactionCompleted:
    pass


class ISendMoneyObserver(ABC):
    @abstractmethod
    async def update(self, event: object) -> None:
        pass


@dataclass
class SendMoneyEventsPublisher:
    """
    Manages communication between components that are communicating during the
    send money process.
    """

    logger: Logger
    observers: List[ISendMoneyObserver] = field(default_factory=list)

    def subscribe(self, observer: ISendMoneyObserver) -> None:
        self.observers.append(observer)

    def unsubscribe(self, observer: ISendMoneyObserver):
        self.observers.remove(observer)

    async def notify(self, event: object):
        self.logger.info(f"Notifying {len(self.observers)}")

        try:
            for observer in self.observers:
                await observer.update(event)
        except Exception as e:
            self.logger.error(f"There was an error while sending money {str(e)}")
            await self.notify(event=SendMoneyError(error=e))

    async def start(self, session: UserSession) -> None:
        if session.user is None:
            self.logger.warning("Unregistered user sending money.")
            raise ValueError("Unregistered user sending money.")

        username = session.user.first_name + " " + session.user.last_name
        self.logger.info(
            "Starting send money process.",
            extra={
                "class": "SendMoneyEventsPublisher",
                "session": session.id,
                "user": username,
            },
        )
        await self.notify(
            event=SendMoneyUserPrompt(
                event_name="send_money_info", prompt_recepient=session.id
            )
        )
