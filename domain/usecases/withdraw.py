from dataclasses import dataclass, field
from logging import Logger
from domain.entities.services.session_service import SessionService
from domain.entities.services.user_services import CustomerService
from domain.entities.services.wallet_service import WalletService, WalletServiceFactory
from domain.entities.services.withdraw_event_publisher import (
    IWithdrawObserver,
    WithdrawCompleted,
    WithdrawError,
    WithdrawEventsPublisher,
    WithdrawFailed,
    WithdrawUserPrompt,
)
from domain.entities.sessions import UserSession
from interface_adapters.ui.presenters.whatsapp_presenters import (
    WhatsappWithdrawPresenter,
    WhatsappWithdrawPresenterFactory,
)


@dataclass
class WithdrawUseCase(IWithdrawObserver):
    """
    Use case that coordinates the withdrawal process for customers.
    """

    presenter: WhatsappWithdrawPresenter
    wallet_service: WalletService
    customer_service: CustomerService
    withdraw_event_publisher: WithdrawEventsPublisher
    session_service: SessionService
    logger: Logger
    active_session: UserSession | None = field(init=False, default=None)

    async def withdraw_funds(self, session: UserSession) -> None:
        self.active_session = session

        await self.withdraw_event_publisher.start(session=session)

    async def delete_session(self) -> None:
        if self.active_session is None:
            return

        status = await self.session_service.delete_customer_session(
            customer_session=self.active_session
        )
        self.active_session = None

        if not status:
            self.logger.critical("Could not delete the session.")

            return

    async def update(self, event: object) -> None:
        if isinstance(event, WithdrawCompleted) or isinstance(event, WithdrawFailed):
            await self.delete_session()

        if isinstance(event, WithdrawError) and self.active_session is not None:
            await self.withdraw_event_publisher.notify(
                event=WithdrawUserPrompt(
                    event_name="error", prompt_recepient=self.active_session.id
                )
            )
            await self.delete_session()


@dataclass
class WithdrawUseCaseFactory:
    presenter_factory: WhatsappWithdrawPresenterFactory
    wallet_service_factory: WalletServiceFactory
    customer_service: CustomerService
    session_service: SessionService
    logger: Logger

    def create(
        self, withdraw_event_publisher: WithdrawEventsPublisher
    ) -> WithdrawUseCase:
        wallet_service = self.wallet_service_factory.create_for_withdraw(
            withdraw_events_publisher=withdraw_event_publisher
        )
        presenter = self.presenter_factory.create(
            withdraw_event_publisher=withdraw_event_publisher
        )
        use_case = WithdrawUseCase(
            presenter=presenter,
            wallet_service=wallet_service,
            customer_service=self.customer_service,
            withdraw_event_publisher=withdraw_event_publisher,
            session_service=self.session_service,
            logger=self.logger,
        )

        withdraw_event_publisher.subscribe(observer=use_case)

        return use_case
