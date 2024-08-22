from dataclasses import dataclass
from logging import Logger
from domain.entities.services.send_money_events_publisher import (
    SendMoneyEventsPublisher,
)
from domain.entities.services.session_service import SessionService
from domain.entities.services.user_services import CustomerService
from domain.entities.services.wallet_service import WalletService
from domain.entities.sessions import UserSession
from interface_adapters.ui.controllers.session_event_publisher import (
    ControllerEventPublisher,
)
from interface_adapters.ui.presenters.whatsapp_presenters import (
    WhatsappSendMoneyPresenter,
)


@dataclass
class SendMoneyUseCase:
    """
    Use case that coordinates sending money to another phone number and enables
    customers to save.
    """

    presenter: WhatsappSendMoneyPresenter
    wallet_service: WalletService
    customer_service: CustomerService
    session_service: SessionService
    controller_event_publisher: ControllerEventPublisher
    send_money_event_publisher: SendMoneyEventsPublisher
    logger: Logger
    active_session: UserSession | None

    async def send_money(self, session: UserSession):
        """
        Starts the process of sending money to a user.

        Args:
            session (`UserSession`): User's session information that is used to
                identify a user that is trying to send money.
        """
        self.active_session = session
        # Use case just starts the process, the rest of the communication
        # between objects will be done through the event publisher.
        await self.send_money_event_publisher.start(session=session)

    async def delete_session(self) -> None:
        if self.active_session is None:
            return

        await self.session_service.delete_customer_session(
            customer_session=self.active_session
        )
