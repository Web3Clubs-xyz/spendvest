from dataclasses import dataclass
from domain.entities.users import User


@dataclass
class SessionType:
    """
    Entity used to identify the type of session.

    Attributes:
        `id (int)`: Unique identifier for a session type
        `name (str)`: Name of the session type
        `steps (List[SessionStep])`: Linked list of all the steps in a session.
    """

    id: int
    name: str


@dataclass
class UserSession:
    """
    Entity representing a user's session while they are interacting with the
    system.

    Attributes:
        `id (str)`: Unique identifier for a user's session
        `user (User)`: The owner of the session
        `session_type (SessionType)`: The type of session the user is in
        `current_step (int)`: The current step in the session that the user is in
        `external_id (str)`: Unique identifier used to tie interactions with
            external systems to a session.
    """

    id: str
    user: User | None  # Nullable because of registration.
    session_type: SessionType
    current_step: int
    external_id: str

    def increment_step(self):
        self.current_step += 1
