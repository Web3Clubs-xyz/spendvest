from abc import ABC, abstractmethod
from configparser import Error
from dataclasses import dataclass
from logging import Logger
import traceback
import uuid

from apscheduler.util import re

from domain.entities.payments import Wallet
from domain.entities.services.registration_event_publisher import (
    RegistrationEventsPublisher,
    RegistrationInputReceived,
    RegistrationUserPrompt,
)
from domain.entities.users import Customer
from domain.usecases.interfaces.register_account_interfaces import (
    IRegistrationEventObserver,
)
from interface_adapters.datastore.registration_repository import (
    SQLAlchemyRegistrationRepository,
)
from interface_adapters.payments.sasapay.sasapay_payment_gateway import (
    SasaPayPaymentGatewayAdapter,
    SasaPayPaymentGatewayAdapterFactory,
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
class CustomerRegistrationService(IRegistrationEventObserver):
    registration_event_publisher: RegistrationEventsPublisher
    payment_gateway: SasaPayPaymentGatewayAdapter
    repository: SQLAlchemyRegistrationRepository
    logger: Logger

    def sanitise_phone_number(self, phone_number: str) -> str | None:
        phone_number = phone_number.replace(" ", "")
        pattern = r"\+?.*?(\d{9})$"
        match = re.search(pattern, phone_number)

        if match:
            rest_of_phone_number = match.group(1)

            return rest_of_phone_number

        return None

    async def create_customer_account(self, customer: Customer) -> Customer:
        sanitised_phone_number = self.sanitise_phone_number(
            phone_number=str(customer.phone_number)
        )

        if sanitised_phone_number is None:
            raise Error("Invalid phone number")

        customer.phone_number = int(sanitised_phone_number)

        self.logger.info(
            f"Sanitised phone number from {customer.phone_number} to {sanitised_phone_number}"
        )

        saved_customer = self.repository.save_customer(customer=customer)

        return saved_customer

    async def create_wallet(
        self,
        customer: Customer,
        saving_percentage: int,
        event_id: str,
        document_type: str,
        document_number: str,
    ) -> Wallet:
        print(f"Creating Wallet for customer {customer.id}")

        try:
            external_id = await self.payment_gateway.register_wallet(
                customer=customer,
                event_id=event_id,
                document_type=document_type,
                document_number=document_number,
            )
            wallet = Wallet(
                savings_percentage=saving_percentage,
                customer=customer,
                wallet_id=uuid.uuid4().hex,
                external_id=external_id,
            )
            wallet = self.repository.save_wallet(wallet=wallet)

            return wallet

        except Exception as e:
            print(f"There was a problem creating a wallet: {str(e)}")
            raise Error("Wallet Creation Error:")

    async def register_user(
        self,
        customer: Customer,
        saving_percentage: int,
        event_id: str,
        document_type: str,
        document_number: str,
    ) -> None:
        customer = await self.create_customer_account(customer=customer)
        print(f"Creating customer {customer.id}")

        # User's wallet is returned but that data isn't used. Consider using
        # it to display initial wallet details
        await self.create_wallet(
            customer=customer,
            saving_percentage=saving_percentage,
            event_id=event_id,
            document_type=document_type,
            document_number=document_number,
        )

        await self.repository.commit()

        await self.registration_event_publisher.notify(
            event=RegistrationUserPrompt(
                prompt_recepient=event_id, event_name="registration_complete"
            )
        )

    async def update(self, event: object) -> None:
        if (
            isinstance(event, RegistrationInputReceived)
            and event.input_name == "registration_info"
        ):
            print((
                "CustomerRegistrationService has received",
                f" registration_info {event.user_input}",
            ))
            user_input = event.user_input
            registration_info = user_input["registration_info"]

            try:
                customer = Customer(
                    id=uuid.uuid4().hex,
                    phone_number=int(registration_info["phone_number"]),
                    first_name=registration_info["first_name"],
                    middle_name=registration_info["middle_name"],
                    last_name=registration_info["last_name"],
                    email=registration_info["email"],
                    whatsapp=registration_info["whatsapp"],
                )

                await self.register_user(
                    customer=customer,
                    saving_percentage=int(registration_info["saving_percentage"]),
                    event_id=registration_info["whatsapp"],
                    document_type=registration_info["document_type"],
                    document_number=registration_info["document_number"],
                )
            except Exception as e:
                print(f"There was an error while registering a customer: {str(e)}")
                traceback.print_exc()


@dataclass
class CustomerRegistrationServiceFactory:
    payment_gateway_factory: SasaPayPaymentGatewayAdapterFactory
    repository: SQLAlchemyRegistrationRepository
    logger: Logger

    def create(self, registration_event_publisher: RegistrationEventsPublisher):
        payment_gateway = self.payment_gateway_factory.create_for_registration(
            registration_event_publisher=registration_event_publisher
        )
        customer_registration_service = CustomerRegistrationService(
            registration_event_publisher=registration_event_publisher,
            payment_gateway=payment_gateway,
            repository=self.repository,
            logger=self.logger,
        )

        registration_event_publisher.subscribe(observer=customer_registration_service)

        return customer_registration_service
