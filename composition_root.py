from dependency_injector import containers, providers

from container_config import SpendvestConfig
from domain.entities.services.session_service import SessionService
from domain.entities.services.user_registration_service import (
    CustomerRegistrationService,
)
from domain.entities.services.user_services import CustomerService
from domain.entities.services.wallet_service import WalletService
from domain.usecases.invalid_input import InvalidInputUseCase
from domain.usecases.new_session import NewSessionUseCase
from domain.usecases.register_account import (
    RegisterCustomerAccountUseCase,
    RegistrationEventsPublisher,
)
from domain.usecases.send_money import SendMoneyEventsPublisher, SendMoneyUseCase
from domain.usecases.withdraw import WithdrawUseCase
from interface_adapters.datastore.customer_repository import (
    SQLAlchemyCustomerRepository,
)
from interface_adapters.datastore.session_repository import SQLAlchemySessionRepository
from interface_adapters.datastore.wallet_repository import SQLAlchemyWalletRepository
from interface_adapters.payments.sasapay.sasapay_payment_gateway import (
    SasaPayPaymentGatewayAdapter,
    SasapayApiClient,
)
from interface_adapters.ui.controllers.controllers import (
    InvalidInputController,
    NewSessionController,
    RegistrationController,
    SendMoneyController,
    WithdrawController,
)
from interface_adapters.ui.controllers.session_event_publisher import (
    ControllerEventPublisher,
)
from interface_adapters.ui.presenters.whatsapp_presenters import (
    WhatsappHomeInterfacePresenter,
    WhatsappInvalidInputPresenter,
    WhatsappRegistrationPresenter,
    WhatsappSendMoneyPresenter,
    WhatsappWithdrawPresenter,
)
import spendvest_logging

from drivers.sqlalchemy.config import DbSession
from interface_adapters.payments.sasapay.payment_events_publisher import (
    PaymentEventsPublisher,
)
from interface_adapters.views.router import WhatsappRouter


class SpendvestContainer(containers.DeclarativeContainer):
    """
    Inversion of control container for objects used in production.
    """

    config = providers.Container(SpendvestConfig)

    # Logging
    registration_logger = providers.Singleton(
        lambda: spendvest_logging.registration_logger
    )
    send_money_logger = providers.Singleton(lambda: spendvest_logging.send_money_logger)
    withdraw_logger = providers.Singleton(lambda: spendvest_logging.withdraw_logger)
    payment_gateway_logger = providers.Singleton(
        lambda: spendvest_logging.payment_gateway_logger
    )
    wallet_service_logger = providers.Singleton(
        lambda: spendvest_logging.wallet_service_logger
    )

    # SQLAlchemy Session
    sqlalchemy_session_manager = providers.Factory(DbSession)
    sqlalchemy_session = providers.Callable(sqlalchemy_session_manager().get_session)

    # Event Publishers
    controller_event_publisher = providers.Factory(ControllerEventPublisher)
    payment_event_publisher = providers.Factory(PaymentEventsPublisher)
    registration_event_publisher = providers.Factory(RegistrationEventsPublisher)
    send_money_event_publisher = providers.Factory(SendMoneyEventsPublisher)

    # Repositories
    sqlalchemy_wallet_repository = providers.Factory(
        SQLAlchemyWalletRepository, session=sqlalchemy_session
    )
    sqlalchemy_session_repository = providers.Factory(
        SQLAlchemySessionRepository, session=sqlalchemy_session
    )
    sqlalchemy_customer_repository = providers.Factory(
        SQLAlchemyCustomerRepository,
        session=sqlalchemy_session,
    )

    # Payment Gateway
    sasapay_api_client = providers.Factory(
        SasapayApiClient,
        access_token=config.provided.sasapay.access_token,
        request_payment_endpoint=(
            config.provided.sasapay.wallet.request_payment_endpoint
        ),
        transfer_funds_endpoint=config.provided.sasapay.wallet.transfer_funds_endpoint,
        personal_onboarding_endpoint=(
            config.provided.sasapay.wallet.personal_onboarding_endpoint
        ),
        site_url=config.provided.spendvest_site_url,
        merchant_code=config.provided.sasapay.merchant_code,
        sasapay_headers={},
        payment_events_publisher=payment_event_publisher,
        logger=payment_gateway_logger,
    )
    sasapay_payment_gateway = providers.Factory(
        SasaPayPaymentGatewayAdapter,
        merchant_code=config.provided.sasapay.merchant_code,
        sasapay_api_client=sasapay_api_client,
        send_money_event_publisher=send_money_event_publisher,
        logger=payment_gateway_logger,
    )

    # Services
    wallet_service = providers.Factory(
        WalletService,
        repository=sqlalchemy_wallet_repository,
        wallet_payment_gateway=sasapay_payment_gateway,
        registration_event_publisher=registration_event_publisher,
        send_money_event_publisher=send_money_event_publisher,
        logger=wallet_service_logger,
    )
    session_service = providers.Factory(
        SessionService, repository=sqlalchemy_session_repository
    )
    customer_service = providers.Factory(
        CustomerService, repository=sqlalchemy_customer_repository
    )
    user_registration_service = providers.Factory(
        CustomerRegistrationService,
        customer_service=customer_service,
        wallet_service=wallet_service,
        registration_event_publisher=registration_event_publisher,
    )

    # New session
    new_session_presenter = providers.Factory(
        WhatsappHomeInterfacePresenter,
        facebook_endpoint_base_url=config.provided.facebook.endpoint_base_url,
        whatsapp_access_token=config.provided.whatsapp.access_token,
        whatsapp_phone_number_id=config.provided.whatsapp.phone_number_id,
        whatsapp_business_account_id=config.provided.whatsapp.business_account_id,
    )
    new_session_use_case = providers.Factory(
        NewSessionUseCase,
        session_service=session_service,
        presenter=new_session_presenter,
        customer_service=customer_service,
    )
    new_session_controller = providers.Factory(
        NewSessionController, use_case=new_session_use_case
    )

    # Registration
    registration_presenter = providers.Factory(
        WhatsappRegistrationPresenter,
        facebook_endpoint_base_url=config.provided.facebook.endpoint_base_url,
        whatsapp_access_token=config.provided.whatsapp.access_token,
        whatsapp_phone_number_id=config.provided.whatsapp.phone_number_id,
        whatsapp_business_account_id=config.provided.whatsapp.business_account_id,
    )
    registration_use_case = providers.Factory(
        RegisterCustomerAccountUseCase,
        registration_event_publisher=registration_event_publisher,
        user_registration_service=user_registration_service,
        session_service=session_service,
        presenter=registration_presenter,
    )
    registration_controller = providers.Factory(
        RegistrationController,
        registration_use_case=registration_use_case,
        controller_event_publisher=controller_event_publisher,
        registration_event_publisher=registration_event_publisher,
    )

    # Send Money
    send_money_presenter = providers.Factory(
        WhatsappSendMoneyPresenter,
        facebook_endpoint_base_url=config.provided.facebook.endpoint_base_url,
        whatsapp_access_token=config.provided.whatsapp.access_token,
        whatsapp_phone_number_id=config.provided.whatsapp.phone_number_id,
        whatsapp_business_account_id=config.provided.whatsapp.business_account_id,
    )
    send_money_use_case = providers.Factory(
        SendMoneyUseCase,
        presenter=send_money_presenter,
        wallet_service=wallet_service,
        customer_service=customer_service,
        session_service=session_service,
        controller_event_publisher=controller_event_publisher,
        send_money_event_publisher=send_money_event_publisher,
        logger=send_money_logger,
        active_session=None,
    )
    send_money_controller = providers.Factory(
        SendMoneyController,
        use_case=send_money_use_case,
        controller_event_publisher=controller_event_publisher,
        send_money_event_publisher=send_money_event_publisher,
    )

    # Withdraw
    withdraw_presenter = providers.Factory(
        WhatsappWithdrawPresenter,
        facebook_endpoint_base_url=config.provided.facebook.endpoint_base_url,
        whatsapp_access_token=config.provided.whatsapp.access_token,
        whatsapp_phone_number_id=config.provided.whatsapp.phone_number_id,
        whatsapp_business_account_id=config.provided.whatsapp.business_account_id,
    )
    withdraw_use_case = providers.Factory(
        WithdrawUseCase,
        presenter=withdraw_presenter,
        wallet_service=wallet_service,
        customer_service=customer_service,
    )
    withdraw_controller = providers.Factory(
        WithdrawController,
        use_case=withdraw_use_case,
        controller_event_publisher=controller_event_publisher,
    )

    # Invalid input
    invalid_input_presenter = providers.Factory(
        WhatsappInvalidInputPresenter,
        facebook_endpoint_base_url=config.provided.facebook.endpoint_base_url,
        whatsapp_access_token=config.provided.whatsapp.access_token,
        whatsapp_phone_number_id=config.provided.whatsapp.phone_number_id,
        whatsapp_business_account_id=config.provided.whatsapp.business_account_id,
    )
    invalid_input_use_case = providers.Factory(
        InvalidInputUseCase,
        session_service=session_service,
        presenter=invalid_input_presenter,
    )
    invalid_input_controller = providers.Factory(
        InvalidInputController, use_case=invalid_input_use_case
    )

    # Whatsapp router
    whatsapp_router = providers.Factory(
        WhatsappRouter,
        session_service=session_service,
        new_session_controller=new_session_controller,
        registration_controller=registration_controller,
        send_money_controller=send_money_controller,
        withdraw_controller=withdraw_controller,
        invalid_input_controller=invalid_input_controller,
        controller_event_publisher=controller_event_publisher,
    )
