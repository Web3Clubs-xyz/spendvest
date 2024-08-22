from abc import ABC, abstractmethod
from dataclasses import dataclass

from domain.entities.payments import Wallet
from domain.entities.services.registration_event_publisher import (
    RegistrationCompleted,
    RegistrationEventsPublisher,
    RegistrationInputReceived,
)
from domain.entities.services.user_services import CustomerService
from domain.entities.services.wallet_service import WalletService
from domain.entities.users import Customer
from domain.usecases.interfaces.register_account_interfaces import (
    IRegistrationEventObserver,
)


@dataclass
class CustomerRegistrationOutput:
    customer: Customer
    wallet: Wallet


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


@dataclass
class CustomerRegistrationService:
    customer_service: CustomerService
    wallet_service: WalletService
    registration_event_publisher: RegistrationEventsPublisher

    async def register_user(
        self,
        customer: Customer,
        saving_percentage: int,
        event_id: str,
        document_type: str,
        document_number: str,
    ) -> None:
        customer = await self.customer_service.create_customer(customer=customer)

        # User's wallet is returned but that data isn't used. Consider using
        # it to display initial wallet details
        await self.wallet_service.create_wallet(
            customer=customer,
            saving_percentage=saving_percentage,
            event_id=event_id,
            document_type=document_type,
            document_number=document_number,
        )

        await self.registration_event_publisher.notify(
            event=RegistrationCompleted(prompt_recepient=event_id)
        )

    async def update(self, event: object) -> None:
        if (
            isinstance(event, RegistrationInputReceived)
            and event.input_name == "registration_info"
        ):

            await self.register_user(
                customer=event.user_input["customer"],
                saving_percentage=event.user_input["saving_percentage"],
                event_id=event.user_input["event_id"],
                document_type=event.user_input["document_type"],
                document_number=event.user_input["document_number"],
            )
