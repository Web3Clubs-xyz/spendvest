from dataclasses import dataclass
from typing import Dict
from typing_extensions import override
from domain.entities.services.registration_event_publisher import (
    RegistrationEventsPublisher,
    RegistrationInputReceived,
    RegistrationInputRequired,
)
from domain.entities.services.send_money_events_publisher import (
    ISendMoneyObserver,
    SendMoneyEventsPublisher,
    SendMoneyTransactionInputReceived,
    SendMoneyTransactionInputRequired,
)
from domain.entities.services.withdraw_event_publisher import (
    IWithdrawObserver,
    WithdrawEventsPublisher,
    WithdrawInputReceived,
    WithdrawInputRequired,
)
from domain.entities.sessions import UserSession
from domain.usecases.interfaces.register_account_interfaces import (
    IRegistrationEventObserver,
)
from domain.usecases.invalid_input import InvalidInputUseCase
from domain.usecases.new_session import NewSessionUseCase
from domain.usecases.register_account import (
    RegisterCustomerAccountUseCaseFactory,
)
from domain.usecases.send_money import (
    SendMoneyUseCaseFactory,
)
from domain.usecases.withdraw import WithdrawUseCaseFactory
from interface_adapters.ui.controllers.session_event_publisher import (
    ControllerEventPublisher,
)


@dataclass
class RegistrationController(IRegistrationEventObserver):
    registration_use_case_factory: RegisterCustomerAccountUseCaseFactory
    controller_event_publisher: ControllerEventPublisher
    registration_event_publisher: RegistrationEventsPublisher

    def __init__(
        self,
        registration_use_case_factory: RegisterCustomerAccountUseCaseFactory,
        controller_event_publisher: ControllerEventPublisher,
        registration_event_publisher: RegistrationEventsPublisher,
    ):
        self.registration_use_case_factory = registration_use_case_factory
        self.controller_event_publisher = controller_event_publisher
        self.registration_event_publisher = registration_event_publisher

    async def register_user(self, session: UserSession) -> None:
        self.registration_event_publisher.subscribe(self)
        use_case = self.registration_use_case_factory.create(
            registration_event_publisher=self.registration_event_publisher
        )
        await use_case.register(session=session)

    async def emit_event(self, session: UserSession, data: Dict) -> None:
        print("Emitting information in controller")
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
            self.controller_event_publisher.create_event(
                event_id=event.prompt_recepient
            )

            print("Waiting for registration info")
            registration_info = await self.controller_event_publisher.wait_for_event(
                event_id=event.prompt_recepient
            )

            print("Controller sending registration_info")
            await self.registration_event_publisher.notify(
                event=RegistrationInputReceived(
                    input_name="registration_info",
                    user_input={"registration_info": registration_info},
                )
            )

        if isinstance(event, RegistrationInputRequired) and (
            event.input_name == "otp" or event.input_name == "otp_failed"
        ):
            self.controller_event_publisher.create_event(
                event_id=event.prompt_recepient
            )

            otp = await self.controller_event_publisher.wait_for_event(
                event_id=event.prompt_recepient
            )

            await self.registration_event_publisher.notify(
                event=RegistrationInputReceived(
                    input_name="otp", user_input={"otp": otp}
                )
            )


@dataclass
class SendMoneyController(ISendMoneyObserver):
    use_case_factory: SendMoneyUseCaseFactory
    controller_event_publisher: ControllerEventPublisher
    send_money_event_publisher: SendMoneyEventsPublisher

    async def send_money(self, session: UserSession) -> None:
        use_case = self.use_case_factory.create(
            send_money_events_publisher=self.send_money_event_publisher
        )
        self.send_money_event_publisher.subscribe(observer=self)
        await use_case.send_money(
            session=session,
        )

    async def update(self, event: object) -> None:
        if isinstance(event, SendMoneyTransactionInputRequired):
            print("Requiring transaction input.")
            session_id = event.prompt_recepient
            input_name = event.input_name

            match input_name:
                case "send_money_info":
                    self.controller_event_publisher.create_event(event_id=session_id)
                    send_money_input = (
                        await self.controller_event_publisher.wait_for_event(
                            event_id=session_id
                        )
                    )
                    print(f"Got send money input {send_money_input}")

                    if send_money_input is None:
                        # Prompt user the input wasn't received
                        return

                    try:
                        await self.send_money_event_publisher.notify(
                            event=SendMoneyTransactionInputReceived(
                                input_name="send_money_info",
                                user_input=send_money_input,
                            )
                        )
                    except Exception as e:
                        print(
                            f"Error while notifying send money event observers {str(e)}"
                        )
                        return

                case "otp":
                    self.controller_event_publisher.create_event(event_id=session_id)
                    otp = await self.controller_event_publisher.wait_for_event(
                        event_id=session_id
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
                data["session"] = session
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
class WithdrawController(IWithdrawObserver):
    """
    Coordinates the withdrawal process for a customer.

    Methods:
        withdraw(amount: `int`, session: `UserSession`) -> `None`: Withdraws
            funds from a user's wallet.
        prompt_user(session: `UserSession`) -> `None`: Prompts a user to fill in
            information required to withdraw funds.
    """

    use_case_factory: WithdrawUseCaseFactory
    controller_event_publisher: ControllerEventPublisher
    withdraw_event_publisher: WithdrawEventsPublisher

    async def withdraw(self, session: UserSession) -> None:
        use_case = self.use_case_factory.create(
            withdraw_event_publisher=self.withdraw_event_publisher
        )

        self.withdraw_event_publisher.subscribe(observer=self)

        await use_case.withdraw_funds(
            session=session,
        )

    @override
    async def update(self, event: object) -> None:
        if isinstance(event, WithdrawInputRequired):
            input_name = event.input_name

            match input_name:
                case "withdraw_info":
                    self.controller_event_publisher.create_event(
                        event_id=event.prompt_recepient
                    )
                    data = await self.controller_event_publisher.wait_for_event(
                        event_id=event.prompt_recepient
                    )

                    if data is None:
                        return

                    print(f"User input from whatsapp: {data}")
                    input = {
                        "amount": data["amount"],
                        "receiving_phone_number": data["receiving_phone_number"],
                        "session_id": event.prompt_recepient,
                    }
                    await self.withdraw_event_publisher.notify(
                        event=WithdrawInputReceived(
                            input_name="withdraw_info", user_input=input
                        )
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
