from abc import ABC, abstractmethod
import asyncio
from typing_extensions import Any, Callable, Dict, List

"""
We need to set up an observer pattern to moniter user input during
multi-step processes. The `use case` will be the `observer` of ui events. input
from users should be checked against their `session` status to know what use
case (observer) will respond to the event.
"""


class IUseCaseEventPublisher(ABC):
    """
    Abstract UI Event publisher.

    Interface to be implemented by concrete ui event publishers and to be used
    as dependency for controllers.

    Method:
        subscribe(event_type: `str`, observer: `Callable`) -> `None`:
            Subscribes observers to events.
        create_event(event_id: `str`) -> `None`:
            Creates an event observers will subscribe to.
        notify(event_type: `str`, event_id: `str`, data: `Any`) -> `None`:
            Notifies observers about an event they are observing.
        wait_for_event(event_id: `str`, timeout: `int` | `None`) -> `Any` | `None`:
    """

    @abstractmethod
    def subscribe(self, event_type: str, observer: Callable) -> None:
        pass

    @abstractmethod
    def create_event(self, event_id: str) -> None:
        pass

    @abstractmethod
    def notify(self, event_type: str, event_id: str, data: Any) -> None:
        pass

    @abstractmethod
    async def wait_for_event(self, event_id: str, timeout: int | None) -> Any | None:
        pass


class ControllerEventPublisher(IUseCaseEventPublisher):
    """
    Event publisher for controllers to wait for user input based on use case
    state.
    """

    _events: Dict[str, asyncio.Event] = {}
    _observers: Dict[str, List[Callable]] = {}
    _inputs: Dict[str, Any] = {}

    def subscribe(self, event_type: str, observer: Callable) -> None:
        """
        Subscribes observers to UI events.

        Args:
            `event_type (str)`: Name of the event type that is subscribing.
            `observer (Callable)`: Observer subscribing to events.
        """
        if event_type not in self._observers:
            self._observers[event_type] = []

        self._observers[event_type].append(observer)

    def create_event(self, event_id: str) -> None:
        """
        Creates an event to be monitored by the observers.

        Args:
            `event_id (str)`: Unique identifier of a UI event.
        """
        if event_id not in self._events:
            self._events[event_id] = asyncio.Event()
        else:
            raise ValueError(f"Event with id {event_id} already exists")

    def notify(self, event_type: str, event_id: str, data: Any) -> None:
        """
        Notifies observers that ther has been an event from the UI
        webhook

        Args:
            `event_type (str)`: Name of the event type.
            `event_id (str)`: Unique identifier for a UI event.
            `data (Any)`: Data from the UI event we are observing.
        """
        print(f"Notifying {len(self._observers)} controller observers")
        self._inputs[event_id] = data
        if event_type in self._observers:
            for observer in self._observers[event_type]:
                asyncio.create_task(observer(event_id, data))
        if event_id in self._events:
            self._events[event_id].set()
            del self._events[event_id]
        else:
            print(
                (
                    f"Warning: Received callback for unknown event {event_id}."
                    f"Events included are: {self._observers}"
                )
            )

    async def wait_for_event(
        self, event_id: str, timeout: float | None = None
    ) -> Any | None:
        """
        Resolves events handled by observer callbacks.

        Args:
            `event_id (str)`: Unique identifier for an event.
            `timeout (float)`: Time in seconds we should wait for the user's
                input before timing out
        """
        if event_id not in self._events:
            raise ValueError(f"No event with id {event_id}")

        try:
            await asyncio.wait_for(self._events[event_id].wait(), timeout)
            print(f"Sending data to observer {self._inputs.get(event_id)}")
            return self._inputs.get(event_id)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Event {event_id} timed out.")
