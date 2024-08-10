from dataclasses import dataclass, field
from typing import List
from typing_extensions import Dict, override
from domain.entities.interfaces.payments_interfaces import (
    IWalletPaymentGateway,
)
from domain.entities.services.session_service import ISessionService
from domain.entities.services.user_registration_service import (
    ICustomerRegistrationService,
)
from domain.entities.services.wallet_service import IWalletService
from domain.usecases.interfaces.presenter_interfaces import (
    IRegisterSasapayWalletPresenter,
)
from domain.usecases.interfaces.register_account_interfaces import (
    IRegisterCustomerAccountUseCase,
    IRegisterCustomerAccountStrategy,
    IRegistrationEventObserver,
)
from interface_adapters.ui.controllers.session_event_publisher import (
    IUseCaseEventPublisher,
)


# Sasapay Registration events
@dataclass
class UserInputRequired:
    step_name: str
    prompt_recepient: str


@dataclass
class UserInputReceived:
    step_name: str
    user_input: Dict


@dataclass
class ProcessCompleted:
    pass


@dataclass
class ProcessFailed:
    pass


# This should be in the infrastructure layer
@dataclass
class SasapayRegistrationStrategy(IRegisterCustomerAccountStrategy):
    """
    Strategy for registering a user with a sasapay wallet
    """

    _event_id: str = field(init=False)
    use_case_event_publisher: IUseCaseEventPublisher
    presenter: IRegisterSasapayWalletPresenter
    steps: List[str]
    current_step_index: int

    def __init__(
        self,
        use_case_event_publisher: IUseCaseEventPublisher,
        presenter: IRegisterSasapayWalletPresenter,
        steps: List[str],
    ) -> None:
        self.use_case_event_publisher = use_case_event_publisher
        self.presenter = presenter
        self.steps = steps
        self.current_step_index = 0
        self.observers: List[IRegistrationEventObserver] = []

    @override
    def subscribe(self, observer: IRegistrationEventObserver) -> None:
        self.observers.append(observer)

    @override
    def unsubscribe(self, observer: IRegistrationEventObserver) -> None:
        self.observers.remove(observer)

    @override
    async def notify(self, event: object) -> None:
        for observer in self.observers:
            await observer.update(event)

    @override
    async def start(self, session_id: str) -> None:
        await self.notify(
            UserInputRequired(
                step_name="REGISTRATION_INFO", prompt_recepient=session_id
            )
        )

    @override
    async def process_user_input(self, user_input: Dict) -> None:
        raise NotImplementedError


class RegisterCustomerAccountUseCase(IRegisterCustomerAccountUseCase):
    session_service: ISessionService = field(init=False)
    _use_case_event_publisher: IUseCaseEventPublisher = field(init=False)
    _registration_strategy: IRegisterCustomerAccountStrategy = field(init=False)
    _user_registration_service: ICustomerRegistrationService = field(
        init=False
    )  # Used to persist session input to the database,
    _presenter: IRegisterSasapayWalletPresenter

    def __init__(
        self,
        registration_strategy: IRegisterCustomerAccountStrategy,
        payment_gateway: IWalletPaymentGateway,
        wallet_service: IWalletService,
        user_registration_service: ICustomerRegistrationService,
        session_service: ISessionService,
        presenter: IRegisterSasapayWalletPresenter,
        ui_event_publisher: IUseCaseEventPublisher,
    ) -> None:
        self._registration_strategy = registration_strategy
        self._user_registration_service = user_registration_service
        self.session_service = session_service
        self._presenter = presenter
        self._use_case_event_publisher = ui_event_publisher

    @property
    def registration_strategy(self) -> IRegisterCustomerAccountStrategy:
        return self._registration_strategy

    @registration_strategy.setter
    def registration_strategy(
        self, registration_strategy: IRegisterCustomerAccountStrategy
    ) -> None:
        self._registration_strategy = registration_strategy

    @override
    async def register(self, session_id: str) -> None:
        """
        Registers a customer onto the platform using `CustomerRegistrationService`.

        Args:
            session (`UserSession`): The session we are registering a user on.
        """
        await self.registration_strategy.start(session_id=session_id)

    @override
    async def update(self, event: object) -> None:
        if isinstance(event, UserInputRequired):
            step_name = event.step_name

            match step_name:
                case "REGISTRATION_INFO":
                    # Update session
                    pass
                case "OTP":
                    # update session
                    pass
                case _:
                    pass
