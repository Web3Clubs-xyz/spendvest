from abc import ABC, abstractmethod
import asyncio
from typing import Any, Dict, List, Callable


class IPaymentEventsPublisher(ABC):
    """
    Abstract Payment Event publisher.

    Interface to be implemented by concrete payment event publishers and to be used
    as dependency for subscribers and publishers.

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


class PaymentEventsPublisher(IPaymentEventsPublisher):
    """
    Callback Listener for the sasapay payment gateway.
    """

    _events: Dict[str, asyncio.Event] = {}
    _observers: Dict[str, List[Callable]] = {}
    _data: Dict[str, Any] = {}

    def create_event(self, event_id: str):
        """
        Creates callback event that observers will be listening for.

        Args:
            `event_id (str)` Unique identifier of the callback event.
        """

        if event_id not in self._events:
            self._events[event_id] = asyncio.Event()
        else:
            raise ValueError(f"Event with id {event_id} already exists.")

    def subscribe(self, event_type: str, observer: Callable):
        """
        Subscribes observers to callback events.

        Args:
            `event_type (str)`: Unique identifier of callback events.
            `observer (Callable)`: Handler for the event being listened for.
        """

        if event_type not in self._observers:
            self._observers[event_type] = []

        self._observers[event_type].append(observer)

    def notify(self, event_type: str, event_id: str, data: Any):
        """
        Notifies observers of the data from the event they are listening for.

        Args:
            `event_type (str)`: Name of the event type we are listening for.
            `event_id (str)`: Unique identifier of a callback event.
            `data (Any)`: Data of the callback events observers are listening for.
        """
        self._data[event_id] = data

        if event_type in self._observers:
            for observer in self._observers[event_type]:
                asyncio.create_task(observer(event_id, data))

        if event_id in self._events:
            self._events[event_id].set()
        else:
            print(f"Warning: Received callback for unknown event with id {event_id}")

    async def wait_for_event(self, event_id: str, timeout: float | None = None):
        """
        Resolves events that have been handled by observer callbacks.

        Args:
            `event_id (str)`: Unique identifier for events observers are listening for
            `timeout (float | None)`: Time in seconds for the event to time out.
        """
        if event_id not in self._events:
            raise ValueError(f"No event with id {event_id}")

        try:
            await asyncio.wait_for(self._events[event_id].wait(), timeout)
            return self._data.get(event_id)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Event {event_id} timed out.")
