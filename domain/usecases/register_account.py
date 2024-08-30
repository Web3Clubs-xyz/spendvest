from dataclasses import dataclass, field
from typing_extensions import Optional
from domain.entities.services.registration_event_publisher import (
    RegistrationCompleted,
    RegistrationError,
    RegistrationEventsPublisher,
    RegistrationFailed,
    RegistrationUserPrompt,
)
from domain.entities.services.session_service import (
    SessionService,
    SessionServiceFactory,
)
from domain.entities.services.user_registration_service import (
    CustomerRegistrationService,
    CustomerRegistrationServiceFactory,
)
from domain.entities.sessions import UserSession
from domain.usecases.interfaces.register_account_interfaces import (
    IRegistrationEventObserver,
)
from interface_adapters.ui.presenters.whatsapp_presenters import (
    WhatsappRegistrationPresenter,
    WhatsappRegistrationPresenterFactory,
)


@dataclass
class RegisterCustomerAccountUseCase(IRegistrationEventObserver):
    active_session: Optional[UserSession] = field(init=False, default=None)
    session_service: SessionService
    registration_event_publisher: RegistrationEventsPublisher
    user_registration_service: CustomerRegistrationService
    presenter: WhatsappRegistrationPresenter

    async def register(self, session: UserSession) -> None:
        """
        Registers a customer onto the platform.

        Args:
            session (`UserSession`): The session we are registering a user on.
        """
        print("Register use case")
        self.active_session = session
        await self.registration_event_publisher.start(session_id=session.id)

    async def delete_session(self) -> None:
        if self.active_session is None:
            return

        await self.session_service.delete_customer_session(
            customer_session=self.active_session
        )

    async def update(self, event: object) -> None:
        if isinstance(event, RegistrationCompleted) or isinstance(
            event, RegistrationFailed
        ):
            await self.delete_session()

        if isinstance(event, RegistrationError) and self.active_session is not None:
            await self.registration_event_publisher.notify(
                event=RegistrationUserPrompt(
                    event_name="error", prompt_recepient=self.active_session.id
                )
            )


@dataclass
class RegisterCustomerAccountUseCaseFactory:
    session_service_factory: SessionServiceFactory
    user_registration_service_factory: CustomerRegistrationServiceFactory
    presenter_factory: WhatsappRegistrationPresenterFactory

    def create(self, registration_event_publisher: RegistrationEventsPublisher):
        session_service = self.session_service_factory.create()
        user_registration_service = self.user_registration_service_factory.create(
            registration_event_publisher=registration_event_publisher
        )
        presenter = self.presenter_factory.create(
            registration_event_publisher=registration_event_publisher
        )

        use_case = RegisterCustomerAccountUseCase(
            session_service=session_service,
            registration_event_publisher=registration_event_publisher,
            user_registration_service=user_registration_service,
            presenter=presenter,
        )

        registration_event_publisher.subscribe(observer=presenter)
        registration_event_publisher.subscribe(observer=use_case)

        return use_case
