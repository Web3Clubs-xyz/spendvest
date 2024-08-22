from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from logging import Logger
from typing import Dict, List

from domain.entities.sessions import UserSession
from domain.usecases.interfaces.register_account_interfaces import (
    IRegistrationEventObserver,
)


@dataclass
class SendMoneyTransactionInputRequired:
    input_name: str
    prompt_recepient: str


@dataclass
class SendMoneyTransactionInputReceived:
    input_name: str
    user_input: Dict


@dataclass
class SendMoneyTransactionInfo:
    message: str
    prompt_recepient: str


@dataclass
class SendMoneyTransactionFailed:
    prompt_recepient: str


@dataclass
class SendMoneyTransactionCompleted:
    prompt_recepient: str


class ISendMoneyObserver(ABC):
    @abstractmethod
    def handle_event(self, data: Dict):
        pass


class SendMoneyEventsPublisher:
    """
    Manages communication between components that are communicating during the
    send money process.
    """

    observers: List[IRegistrationEventObserver] = field(default_factory=list)
    logger: Logger

    def subscribe(self, observer: IRegistrationEventObserver) -> None:
        self.observers.append(observer)

    def unsubscribe(self, observer: IRegistrationEventObserver):
        self.observers.remove(observer)

    async def notify(self, event: object):
        for observer in self.observers:
            await observer.update(event)

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
            event=SendMoneyTransactionInputRequired(
                input_name="send_money_info", prompt_recepient=session.id
            )
        )
