from dataclasses import dataclass
from typing import Dict
from domain.entities.services.registration_event_publisher import (
    RegistrationEventsPublisher,
    RegistrationInputReceived,
    RegistrationInputRequired,
)
from domain.entities.services.send_money_events_publisher import (
    SendMoneyEventsPublisher,
    SendMoneyTransactionInputReceived,
    SendMoneyTransactionInputRequired,
)
from domain.entities.sessions import UserSession
from domain.usecases.invalid_input import InvalidInputUseCase
from domain.usecases.new_session import NewSessionUseCase
from domain.usecases.register_account import (
    RegisterCustomerAccountUseCase,
)
from domain.usecases.send_money import (
    SendMoneyUseCase,
)
from domain.usecases.withdraw import WithdrawUseCase
from interface_adapters.ui.controllers.session_event_publisher import (
    ControllerEventPublisher,
)


@dataclass
class RegistrationController:
    registration_use_case: RegisterCustomerAccountUseCase
    controller_event_publisher: ControllerEventPublisher
    registration_event_publisher: RegistrationEventsPublisher

    async def register_user(self, session: UserSession) -> None:
        await self.registration_use_case.register(session=session)

    async def emit_event(self, session: UserSession, data: Dict) -> None:
        step = session.current_step

        match step:
            case 1:
                # Registration Info received
                await self.registration_event_publisher.notify(
                    event=RegistrationInputReceived(
                        input_name="registration_info", user_input=data
                    )
                )
            case 2:
                # Registration otp received
                await self.registration_event_publisher.notify(
                    event=RegistrationInputReceived(input_name="otp", user_input=data)
                )

    async def update(self, event: object):
        """
        Updates the controller on events that need input in a use case.
        """

        if (
            isinstance(event, RegistrationInputRequired)
            and event.input_name == "registration_info"
        ):
            # We should create an event type for "registration_info" and wait
            # for it. Thie means that the controller event publisher should
            # check the session of the messages coming in and generate a
            # registration_info event type and attach the sender's id so we can
            # receive it here.
            self.controller_event_publisher.create_event(
                event_id=event.prompt_recepient
            )

            registration_info = await self.controller_event_publisher.wait_for_event(
                event_id=event.prompt_recepient
            )

            await self.registration_event_publisher.notify(
                event=RegistrationInputReceived(
                    input_name="registration_info",
                    user_input={"registration_info": registration_info},
                )
            )

        if isinstance(event, RegistrationInputRequired) and (
            event.input_name == "otp" or event.input_name == "otp_failed"
        ):
            # We should create an event type for "otp" or "otp_failed" and wait
            # for it. Thie means that the controller event publisher should
            # check the session of the messages coming in and generate a
            # registration_info event type and attach the sender's id so we can
            # receive it here.
            self.controller_event_publisher.create_event(
                event_id=event.prompt_recepient
            )

            otp = await self.controller_event_publisher.wait_for_event(
                event_id=event.prompt_recepient, timeout=False
            )

            await self.registration_event_publisher.notify(
                event=RegistrationInputReceived(
                    input_name="otp", user_input={"otp": otp}
                )
            )


@dataclass
class SendMoneyController:
    use_case: SendMoneyUseCase
    controller_event_publisher: ControllerEventPublisher
    send_money_event_publisher: SendMoneyEventsPublisher

    async def send_money(self, session: UserSession) -> None:
        await self.use_case.send_money(
            session=session,
        )

    async def update(self, event: object) -> None:
        if isinstance(event, SendMoneyTransactionInputRequired):
            session_id = event.prompt_recepient
            input_name = event.input_name

            match input_name:
                case "send_money_info":
                    self.controller_event_publisher.create_event(event_id=session_id)
                    send_money_input = (
                        await self.controller_event_publisher.wait_for_event(
                            event_id=session_id, timeout=None
                        )
                    )

                    if send_money_input is None:
                        # Prompt user the input wasn't received
                        return

                    await self.send_money_event_publisher.notify(
                        event=SendMoneyTransactionInputReceived(
                            input_name="send_money_info", user_input=send_money_input
                        )
                    )

                case "otp":
                    self.controller_event_publisher.create_event(event_id=session_id)
                    otp = await self.controller_event_publisher.wait_for_event(
                        event_id=session_id, timeout=None
                    )

                    if otp is None:
                        # Prompt user the input wasn't received
                        return

                    await self.send_money_event_publisher.notify(
                        event=SendMoneyTransactionInputReceived(
                            input_name="otp", user_input=otp
                        )
                    )

    async def emit_event(self, session: UserSession, data: Dict) -> None:
        step = session.current_step

        match step:
            case 1:
                # Send money form information
                await self.send_money_event_publisher.notify(
                    event=SendMoneyTransactionInputReceived(
                        input_name="send_money_info", user_input=data
                    )
                )
            case 2:
                # Send money otp
                await self.send_money_event_publisher.notify(
                    event=SendMoneyTransactionInputReceived(
                        input_name="otp", user_input=data
                    )
                )


@dataclass
class InvalidInputController:
    use_case: InvalidInputUseCase

    async def reject_input(self, session: UserSession) -> None:
        await self.use_case.reject_input(session_id=session.id)


@dataclass
class WithdrawController:
    """
    Coordinates the withdrawal process for a customer.

    Methods:
        withdraw(amount: `int`, session: `UserSession`) -> `None`: Withdraws
            funds from a user's wallet.
        prompt_user(session: `UserSession`) -> `None`: Prompts a user to fill in
            information required to withdraw funds.
    """

    use_case: WithdrawUseCase
    controller_event_publisher: ControllerEventPublisher

    async def withdraw(
        self, amount: int, receiving_phone_number: int, session: UserSession
    ) -> None:
        await self.use_case.withdraw_funds(
            amount=amount,
            receiving_phone_number=receiving_phone_number,
            session=session,
        )

    async def prompt_user(self, session: UserSession) -> None:
        self.controller_event_publisher.create_event(event_id=session.id)
        await self.use_case.prompt_user(session=session)
        withdraw_funds_input = await self.controller_event_publisher.wait_for_event(
            event_id=session.id, timeout=None
        )

        if withdraw_funds_input is None:
            # Prompt user the input wasn't received
            return

        await self.withdraw(
            amount=withdraw_funds_input["amount"],
            receiving_phone_number=withdraw_funds_input["receiving_phone_number"],
            session=session,
        )


@dataclass
class NewSessionController:
    """
    Creates a new session for a user

    Methods:
        create_session(external_id: `str`, session_type: `str`) -> `None`:
            creates a session for a customer.
    """

    use_case: NewSessionUseCase

    def __init__(self, use_case: NewSessionUseCase) -> None:
        self.use_case = use_case

    async def create_session(self, external_id: str) -> None:
        await self.use_case.prompt_user(recepient_id=external_id)
