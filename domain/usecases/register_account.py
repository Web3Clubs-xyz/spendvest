from domain.entities.services.registration_event_publisher import (
    RegistrationEventsPublisher,
)
from domain.entities.services.session_service import SessionService
from domain.entities.services.user_registration_service import (
    CustomerRegistrationService,
)
from domain.entities.sessions import UserSession
from interface_adapters.ui.presenters.whatsapp_presenters import (
    WhatsappRegistrationPresenter,
)


class RegisterCustomerAccountUseCase:
    active_session: UserSession | None
    session_service: SessionService
    registration_event_publisher: RegistrationEventsPublisher
    user_registration_service: CustomerRegistrationService
    presenter: WhatsappRegistrationPresenter

    def __init__(
        self,
        registration_event_publisher: RegistrationEventsPublisher,
        user_registration_service: CustomerRegistrationService,
        session_service: SessionService,
        presenter: WhatsappRegistrationPresenter,
    ) -> None:
        self.registration_event_publisher = registration_event_publisher
        self.user_registration_service = user_registration_service
        self.session_service = session_service
        self.presenter = presenter

    async def register(self, session: UserSession) -> None:
        """
        Registers a customer onto the platform.

        Args:
            session (`UserSession`): The session we are registering a user on.
        """
        self.active_session = session
        await self.registration_event_publisher.start(session_id=session.id)

    async def delete_session(self) -> None:
        if self.active_session is None:
            return

        await self.session_service.delete_customer_session(
            customer_session=self.active_session
        )
