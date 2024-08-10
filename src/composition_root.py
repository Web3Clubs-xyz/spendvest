import os
from dependency_injector import containers, providers
from dotenv import load_dotenv

from domain.entities.users import Customer, CustomerUserFactory
from domain.usecases.register_account import RegisterCustomerAccountUseCase
from interface_adapters.datastore.customer_repository import (
    SQLAlchemyCustomerRepository,
)

from drivers.sqlalchemy.config import get_session
from interface_adapters.payments.sasapay.payment_events_publisher import (
    PaymentEventsPublisher,
)
from interface_adapters.views.router import WhatsappRouter

environment = os.getenv("ENVIRONMENT", "development").lower()

if environment == "development":
    load_dotenv(dotenv_path=".env.development")
elif environment == "production":
    load_dotenv(dotenv_path=".env.production")


class SpendvestConfig(containers.DeclarativeContainer):
    """
    Inversion of control container for config.
    """

    config = providers.Configuration()
    config.whatsapp.access_token.from_env("WHATSAPP_ACCESS_TOKEN")
    config.sasapay.client_id.from_env("SASAPAY_CLIENT_ID")
    config.sasapay.client_secret.from_env("SASAPAY_CLIENT_SECRET")
    config.sasapay.merchant_code.from_env("SASAPAY_MERCHANT_CODE")
    config.sasapay.wallet.personal_onboarding_callback_url.from_env(
        "SASAPAY_PERSONAL_ONBOARDING_CALLBACK_URL"
    )
    config.sasapay.wallet.transfer_funds_callback_url.from_env(
        "SASAPAY_TRANSFER_FUNDS_CALLBACK_URL"
    )
    config.sasapay.wallet.request_payment_callback_url.from_env(
        "SASAPAY_REQUEST_PAYMENT_CALLBACK_URL"
    )
    config.mysql.database_url.from_env("MYSQL_DATABASE_URL")


class SpendvestContainer(containers.DeclarativeContainer):
    """
    Inversion of control container for objects used in production.
    """

    config = providers.Container(SpendvestConfig)

    # SQLAlchemy Session
    sqlalchemy_session = providers.Callable(get_session)

    # User Repositories
    sqlalchemy_customer_repository = providers.Factory(
        SQLAlchemyCustomerRepository,
        session=sqlalchemy_session,
    )

    # Entity Factories
    customer_factory = providers.Factory(CustomerUserFactory)

    # Entities
    customer = providers.Factory(Customer)

    # Registration Use Case
    registration_use_case = providers.Factory(
        RegisterCustomerAccountUseCase,
        customer_factory=customer_factory,
        repository=sqlalchemy_customer_repository,
    )

    # Payment event publisher
    payment_events_publisher = providers.Factory(PaymentEventsPublisher)

    # Whatsapp router
    whatsapp_router = providers.Factory(WhatsappRouter)
