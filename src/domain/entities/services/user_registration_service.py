from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing_extensions import override

from domain.entities.payments import IWallet
from domain.entities.services.user_services import ICustomerService
from domain.entities.services.wallet_service import IWalletService
from domain.entities.users import Customer
from domain.usecases.interfaces.register_account_interfaces import (
    IRegistrationEventObserver,
)
from domain.usecases.register_account import (
    UserInputReceived,
)


@dataclass
class CustomerRegistrationOutput:
    customer: Customer
    wallet: IWallet


class ICustomerRegistrationService(IRegistrationEventObserver, ABC):
    @abstractmethod
    async def register_user(
        self, customer: Customer, saving_percentage: int, event_id: str
    ) -> None:
        """
        Abstract method for registering a user. Parameters for this function
        are left to the concrete implementation to define.
        """
        pass

    @abstractmethod
    async def update(self, event: object) -> None:
        """
        Abstract method implemented to update the customer registration service
        on events it has subscribed to.

        Args:
            event (`object`): The event that has been broadcast to all
                subscriged observers.
        """
        pass


class CustomerRegistrationService(ICustomerRegistrationService):
    _customer_service: ICustomerService
    _wallet_service: IWalletService

    def __init__(
        self, customer_service: ICustomerService, wallet_service: IWalletService
    ) -> None:
        self._customer_service = customer_service
        self._wallet_service = wallet_service

    @override
    async def register_user(
        self, customer: Customer, saving_percentage: int, event_id: str
    ) -> None:
        customer = await self._customer_service.create_customer(customer=customer)
        await self._wallet_service.create_wallet(
            customer=customer, saving_percentage=saving_percentage, event_id=event_id
        )

    @override
    async def update(self, event: object) -> None:
        if isinstance(event, UserInputReceived):
            event_name = event.step_name

            match event_name:
                case "REGISTRATION_INFO":
                    await self.register_user(
                        customer=event.user_input["customer"],
                        saving_percentage=event.user_input["saving_percentage"],
                        event_id=event.user_input["event_id"],
                    )
                case _:
                    pass
