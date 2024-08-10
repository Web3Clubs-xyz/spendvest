from dataclasses import dataclass
from typing_extensions import Any, override
from domain.entities.sessions import UserSession
from domain.usecases.interfaces.register_account_interfaces import (
    IRegisterCustomerAccountUseCase,
)
from domain.usecases.interfaces.send_money_interface import ISendMoney
from interface_adapters.ui.controllers.controller_interfaces import (
    IInvalidInputController,
    INewSessionController,
    IRegistrationController,
    ISendMoneyController,
    IWithdrawController,
)
from interface_adapters.ui.controllers.session_event_publisher import (
    IUseCaseEventPublisher,
)


@dataclass
class RegistrationController(IRegistrationController):
    registration_use_case: IRegisterCustomerAccountUseCase
    use_case_event_publisher: IUseCaseEventPublisher

    @override
    async def register_user(self, session: UserSession) -> None:
        await self.registration_use_case.register(session_id=session.id)

    @override
    async def emit_registration_event(self, session: UserSession, data: Any) -> None:
        match session.current_step:
            case 1:
                event_type = "registration_info_required"
            case 2:
                event_type = "registration_otp_required"
            case _:
                event_type = ""

        self.use_case_event_publisher.notify(
            event_id=session.external_id, event_type=event_type, data=data
        )


class SendMoneyController(ISendMoneyController):
    send_money_use_case: ISendMoney
    use_case_event_publisher: IUseCaseEventPublisher

    @override
    async def send_money(self) -> None:
        raise NotImplementedError

    @override
    async def emit_send_money_event(self, session: UserSession, data: Any) -> None:
        raise NotImplementedError


class InvalidInputController(IInvalidInputController):
    @override
    async def reject_input(self) -> None:
        raise NotImplementedError


class WithdrawController(IWithdrawController):
    @override
    async def withdraw(self) -> None:
        raise NotImplementedError

    @override
    async def emit_withdraw_event(self, session: UserSession, data: Any) -> None:
        raise NotImplementedError


class NewSessionController(INewSessionController):
    @override
    async def create_session(self, external_id: str, session_type: str) -> None:
        raise NotImplementedError
