from dataclasses import dataclass, field
from logging import Logger
from typing_extensions import override
from domain.entities.services.send_money_events_publisher import (
    ISendMoneyObserver,
    SendMoneyError,
    SendMoneyEventsPublisher,
    SendMoneyTransactionCompleted,
    SendMoneyTransactionFailed,
    SendMoneyUserPrompt,
)
from domain.entities.services.session_service import (
    SessionService,
    SessionServiceFactory,
)
from domain.entities.services.user_services import (
    CustomerService,
    CustomerServiceFactory,
)
from domain.entities.services.wallet_service import WalletService, WalletServiceFactory
from domain.entities.sessions import UserSession
from interface_adapters.ui.presenters.whatsapp_presenters import (
    WhatsappSendMoneyPresenter,
    WhatsappSendMoneyPresenterFactory,
)


@dataclass
class SendMoneyUseCase(ISendMoneyObserver):
    """
    Use case that coordinates sending money to another phone number and enables
    customers to save.
    """

    presenter: WhatsappSendMoneyPresenter
    wallet_service_factory: WalletServiceFactory
    wallet_service: WalletService = field(init=False)
    customer_service: CustomerService
    session_service: SessionService
    send_money_event_publisher: SendMoneyEventsPublisher
    logger: Logger
    active_session: UserSession | None = None

    async def send_money(self, session: UserSession):
        """
        Starts the process of sending money to a user.

        Args:
            session (`UserSession`): User's session information that is used to
                identify a user that is trying to send money.
        """
        # Use case just starts the process, the rest of the communication
        # between objects will be done through the event publisher.
        self.active_session = session
        self.initialise()
        await self.send_money_event_publisher.start(session=session)

    async def delete_session(self) -> None:
        if self.active_session is None:
            return

        await self.session_service.delete_customer_session(
            customer_session=self.active_session
        )
        self.active_session = None

    def initialise(self) -> None:
        self.wallet_service = self.wallet_service_factory.create_for_send_money(
            send_money_events_publisher=self.send_money_event_publisher
        )

    @override
    async def update(self, event: object) -> None:
        if self.active_session is not None and (
            isinstance(event, SendMoneyTransactionCompleted)
            or isinstance(event, SendMoneyTransactionFailed)
        ):
            await self.delete_session()

        if isinstance(event, SendMoneyError) and self.active_session is not None:
            await self.send_money_event_publisher.notify(
                event=SendMoneyUserPrompt(
                    event_name="error", prompt_recepient=self.active_session.id
                )
            )
            await self.delete_session()


@dataclass
class SendMoneyUseCaseFactory:
    presenter_factory: WhatsappSendMoneyPresenterFactory
    wallet_service_factory: WalletServiceFactory
    customer_service_factory: CustomerServiceFactory
    session_Service_factory: SessionServiceFactory
    logger: Logger

    def create(
        self, send_money_events_publisher: SendMoneyEventsPublisher
    ) -> SendMoneyUseCase:
        session_service = self.session_Service_factory.create()
        customer_service = self.customer_service_factory.create()
        presenter = self.presenter_factory.create(
            send_money_events_publisher=send_money_events_publisher
        )
        use_case = SendMoneyUseCase(
            presenter=presenter,
            wallet_service_factory=self.wallet_service_factory,
            customer_service=customer_service,
            session_service=session_service,
            send_money_event_publisher=send_money_events_publisher,
            logger=self.logger,
        )

        send_money_events_publisher.subscribe(observer=use_case)

        return use_case
