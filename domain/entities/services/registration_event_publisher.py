from dataclasses import dataclass, field
from typing import Dict, List

from domain.usecases.interfaces.register_account_interfaces import (
    IRegistrationEventObserver,
)


@dataclass
class RegistrationInputRequired:
    input_name: str
    prompt_recepient: str


@dataclass
class RegistrationInputReceived:
    input_name: str
    user_input: Dict


@dataclass
class RegistrationCompleted:
    prompt_recepient: str


@dataclass
class RegistrationFailed:
    prompt_recepient: str


# This should be in the infrastructure layer
@dataclass
class RegistrationEventsPublisher:
    """
    Strategy for registering a user with a sasapay wallet
    """

    observers: List[IRegistrationEventObserver] = field(default_factory=list)

    def subscribe(self, observer: IRegistrationEventObserver) -> None:
        self.observers.append(observer)

    def unsubscribe(self, observer: IRegistrationEventObserver) -> None:
        self.observers.remove(observer)

    async def notify(self, event: object) -> None:
        for observer in self.observers:
            await observer.update(event)

    async def start(self, session_id: str) -> None:
        await self.notify(
            RegistrationInputRequired(
                input_name="registration_info", prompt_recepient=session_id
            )
        )
