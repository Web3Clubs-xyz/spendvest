from dataclasses import dataclass, field
from logging import Logger
from typing import Dict, List

from domain.usecases.interfaces.register_account_interfaces import (
    IRegistrationEventObserver,
)


@dataclass
class RegistrationUserPrompt:
    event_name: str
    prompt_recepient: str


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
    pass


@dataclass
class RegistrationError:
    error: Exception


@dataclass
class RegistrationFailed:
    prompt_recepient: str


# This should be in the infrastructure layer
@dataclass
class RegistrationEventsPublisher:
    """
    Strategy for registering a user with a sasapay wallet
    """

    logger: Logger
    observers: List[IRegistrationEventObserver] = field(default_factory=list)

    def subscribe(self, observer: IRegistrationEventObserver) -> None:
        if observer not in self.observers:
            self.observers.append(observer)

    def unsubscribe(self, observer: IRegistrationEventObserver) -> None:
        self.observers.remove(observer)

    async def notify(self, event: object) -> None:
        try:
            for observer in self.observers:
                await observer.update(event)
        except Exception as e:
            self.logger.error(f"There was an error while registering a user: {(e)}")
            await self.notify(event=RegistrationError(error=e))

    async def start(self, session_id: str) -> None:
        print("Starting registration")
        await self.notify(
            RegistrationUserPrompt(
                event_name="registration_info", prompt_recepient=session_id
            )
        )
