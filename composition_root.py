from dependency_injector import containers, providers

from container_config import SpendvestConfig
from domain.entities.services.session_service import (
    SessionService,
    SessionServiceFactory,
)
from domain.entities.services.user_registration_service import (
    CustomerRegistrationService,
    CustomerRegistrationServiceFactory,
)
from domain.entities.services.user_services import (
    CustomerService,
    CustomerServiceFactory,
)
from domain.entities.services.wallet_service import WalletService, WalletServiceFactory
from domain.entities.services.withdraw_event_publisher import WithdrawEventsPublisher
from domain.usecases.invalid_input import InvalidInputUseCase
from domain.usecases.new_session import NewSessionUseCase
from domain.usecases.register_account import (
    RegisterCustomerAccountUseCase,
    RegisterCustomerAccountUseCaseFactory,
    RegistrationEventsPublisher,
)
from domain.usecases.send_money import (
    SendMoneyEventsPublisher,
    SendMoneyUseCase,
    SendMoneyUseCaseFactory,
)
from domain.usecases.withdraw import WithdrawUseCase, WithdrawUseCaseFactory
from interface_adapters.datastore.customer_repository import (
    SQLAlchemyCustomerRepository,
)
from interface_adapters.datastore.registration_repository import (
    SQLAlchemyRegistrationRepository,
)
from interface_adapters.datastore.session_repository import SQLAlchemySessionRepository
from interface_adapters.datastore.wallet_repository import SQLAlchemyWalletRepository
from interface_adapters.payments.sasapay.sasapay_payment_gateway import (
    SasaPayPaymentGatewayAdapter,
    SasaPayPaymentGatewayAdapterFactory,
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
    WhatsappRegistrationPresenterFactory,
    WhatsappSendMoneyPresenter,
    WhatsappSendMoneyPresenterFactory,
    WhatsappWithdrawPresenter,
    WhatsappWithdrawPresenterFactory,
)
import spendvest_logging

from drivers.sqlalchemy.config import get_session, setup_db
from interface_adapters.payments.sasapay.payment_events_publisher import (
    PaymentEventsPublisher,
)
from interface_adapters.views.router import WhatsappRouter


class SpendvestContainer(containers.DeclarativeContainer):
    """
    Inversion of control container for objects used in production.
    """

    config = providers.Container(SpendvestConfig).provided.config()

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
    fastapi_logger = providers.Singleton(lambda: spendvest_logging.fastapi_logger)
    router_logger = providers.Singleton(lambda: spendvest_logging.router_logger)

    # SQLAlchemy Session
    db_session_factory = providers.Callable(setup_db)
    sqlalchemy_session = providers.Resource(get_session)

    # Event Publishers
    controller_event_publisher = providers.Singleton(ControllerEventPublisher)
    payment_event_publisher = providers.Singleton(PaymentEventsPublisher)
    registration_event_publisher = providers.Factory(RegistrationEventsPublisher)
    send_money_event_publisher = providers.Factory(
        SendMoneyEventsPublisher, logger=send_money_logger
    )
    withdraw_event_publisher = providers.Factory(
        WithdrawEventsPublisher, logger=withdraw_logger
    )

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
    sqlalchemy_customer_registration_repository = providers.Factory(
        SQLAlchemyRegistrationRepository, session=sqlalchemy_session
    )

    # Payment Gateway
    sasapay_api_client = providers.Factory(
        SasapayApiClient,
        access_token=config.sasapay.access_token,
        request_payment_endpoint=(config.sasapay.wallet.request_payment_endpoint),
        transfer_funds_endpoint=config.sasapay.wallet.transfer_funds_endpoint,
        personal_onboarding_endpoint=(
            config.sasapay.wallet.personal_onboarding_endpoint
        ),
        personal_onboarding_confirmation_endpoint=(
            config.sasapay.wallet.personal_onboarding_confirmation_endpoint
        ),
        site_url=config.spendvest_site_url,
        merchant_code=config.sasapay.merchant_code,
        sasapay_headers={},
        payment_events_publisher=payment_event_publisher,
        logger=payment_gateway_logger,
    )
    sasapay_payment_gateway = providers.Factory(
        SasaPayPaymentGatewayAdapter,
        merchant_code=config.sasapay.merchant_code,
        registration_event_publisher=registration_event_publisher,
        send_money_event_publisher=send_money_event_publisher,
        logger=payment_gateway_logger,
        sasapay_api_client=sasapay_api_client,
        payment_events_publisher=payment_event_publisher,
    )
    sasapay_payment_gateway_factory = providers.Factory(
        SasaPayPaymentGatewayAdapterFactory,
        merchant_code=config.sasapay.merchant_code,
        logger=payment_gateway_logger,
        sasapay_api_client=sasapay_api_client,
        payment_events_publisher=payment_event_publisher,
    )

    # Services
    wallet_service = providers.Factory(
        WalletService,
        repository=sqlalchemy_wallet_repository,
        wallet_payment_gateway=sasapay_payment_gateway,
        logger=wallet_service_logger,
    )
    wallet_service_factory = providers.Factory(
        WalletServiceFactory,
        repository=sqlalchemy_wallet_repository,
        wallet_payment_gateway_factory=sasapay_payment_gateway_factory,
        logger=wallet_service_logger,
    )
    session_service = providers.Factory(
        SessionService, repository=sqlalchemy_session_repository
    )
    session_service_factory = providers.Factory(
        SessionServiceFactory, repository=sqlalchemy_session_repository
    )
    customer_service = providers.Factory(
        CustomerService, repository=sqlalchemy_customer_repository
    )
    customer_service_factory = providers.Factory(
        CustomerServiceFactory, repository=sqlalchemy_customer_repository
    )
    user_registration_service = providers.Factory(
        CustomerRegistrationService,
        payment_gateway=sasapay_payment_gateway,
        registration_event_publisher=registration_event_publisher,
        repository=sqlalchemy_customer_registration_repository,
    )
    user_registration_service_factory = providers.Factory(
        CustomerRegistrationServiceFactory,
        payment_gateway_factory=sasapay_payment_gateway_factory,
        repository=sqlalchemy_customer_registration_repository,
        logger=registration_logger,
    )

    # New session
    new_session_presenter = providers.Factory(
        WhatsappHomeInterfacePresenter,
        facebook_endpoint_base_url=config.facebook.endpoint_base_url,
        whatsapp_access_token=config.whatsapp.access_token,
        whatsapp_phone_number_id=config.whatsapp.phone_number_id,
        whatsapp_business_account_id=config.whatsapp.business_account_id,
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
        registration_event_publisher=registration_event_publisher,
        facebook_endpoint_base_url=config.facebook.endpoint_base_url,
        whatsapp_access_token=config.whatsapp.access_token,
        whatsapp_phone_number_id=config.whatsapp.phone_number_id,
        whatsapp_business_account_id=config.whatsapp.business_account_id,
    )
    registration_presenter_factory = providers.Factory(
        WhatsappRegistrationPresenterFactory,
        facebook_endpoint_base_url=config.facebook.endpoint_base_url,
        whatsapp_access_token=config.whatsapp.access_token,
        whatsapp_phone_number_id=config.whatsapp.phone_number_id,
        whatsapp_business_account_id=config.whatsapp.business_account_id,
    )
    registration_use_case = providers.Factory(
        RegisterCustomerAccountUseCase,
        user_registration_service=user_registration_service,
        registration_event_publisher=registration_event_publisher,
        session_service=session_service,
        presenter=registration_presenter,
    )
    registration_use_case_factory = providers.Factory(
        RegisterCustomerAccountUseCaseFactory,
        session_service_factory=session_service_factory,
        user_registration_service_factory=user_registration_service_factory,
        presenter_factory=registration_presenter_factory,
    )
    registration_controller = providers.Factory(
        RegistrationController,
        registration_use_case_factory=registration_use_case_factory,
        controller_event_publisher=controller_event_publisher,
        registration_event_publisher=registration_event_publisher,
    )

    # Send Money
    send_money_presenter = providers.Factory(
        WhatsappSendMoneyPresenter,
        send_money_events_publisher=send_money_event_publisher,
        facebook_endpoint_base_url=config.facebook.endpoint_base_url,
        whatsapp_access_token=config.whatsapp.access_token,
        whatsapp_phone_number_id=config.whatsapp.phone_number_id,
        whatsapp_business_account_id=config.whatsapp.business_account_id,
    )
    send_money_presenter_factory = providers.Factory(
        WhatsappSendMoneyPresenterFactory,
        facebook_endpoint_base_url=config.facebook.endpoint_base_url,
        whatsapp_access_token=config.whatsapp.access_token,
        whatsapp_phone_number_id=config.whatsapp.phone_number_id,
        whatsapp_business_account_id=config.whatsapp.business_account_id,
    )
    send_money_use_case = providers.Factory(
        SendMoneyUseCase,
        presenter=send_money_presenter,
        wallet_service_factory=wallet_service_factory,
        customer_service=customer_service,
        session_service=session_service,
        send_money_event_publisher=send_money_event_publisher,
        logger=send_money_logger,
        active_session=None,
    )
    send_money_use_case_factory = providers.Factory(
        SendMoneyUseCaseFactory,
        presenter_factory=send_money_presenter_factory,
        wallet_service_factory=wallet_service_factory,
        customer_service_factory=customer_service_factory,
        session_Service_factory=session_service_factory,
        logger=send_money_logger,
    )
    send_money_controller = providers.Factory(
        SendMoneyController,
        use_case_factory=send_money_use_case_factory,
        controller_event_publisher=controller_event_publisher,
        send_money_event_publisher=send_money_event_publisher,
    )

    # Withdraw
    withdraw_presenter = providers.Factory(
        WhatsappWithdrawPresenter,
        facebook_endpoint_base_url=config.facebook.endpoint_base_url,
        whatsapp_access_token=config.whatsapp.access_token,
        whatsapp_phone_number_id=config.whatsapp.phone_number_id,
        whatsapp_business_account_id=config.whatsapp.business_account_id,
        withdraw_event_publisher=withdraw_event_publisher,
    )
    withdraw_presenter_factory = providers.Factory(
        WhatsappWithdrawPresenterFactory,
        facebook_endpoint_base_url=config.facebook.endpoint_base_url,
        whatsapp_access_token=config.whatsapp.access_token,
        whatsapp_phone_number_id=config.whatsapp.phone_number_id,
        whatsapp_business_account_id=config.whatsapp.business_account_id,
    )
    withdraw_use_case = providers.Factory(
        WithdrawUseCase,
        presenter=withdraw_presenter,
        wallet_service=wallet_service,
        customer_service=customer_service,
        session_service=session_service,
        withdraw_event_publisher=withdraw_event_publisher,
        logger=withdraw_logger,
    )
    withdraw_use_case_factory = providers.Factory(
        WithdrawUseCaseFactory,
        presenter_factory=withdraw_presenter_factory,
        wallet_service_factory=wallet_service_factory,
        customer_service=customer_service,
        session_service=session_service,
        logger=withdraw_logger,
    )
    withdraw_controller = providers.Factory(
        WithdrawController,
        use_case_factory=withdraw_use_case_factory,
        controller_event_publisher=controller_event_publisher,
        withdraw_event_publisher=withdraw_event_publisher,
    )

    # Invalid input
    invalid_input_presenter = providers.Factory(
        WhatsappInvalidInputPresenter,
        facebook_endpoint_base_url=config.facebook.endpoint_base_url,
        whatsapp_access_token=config.whatsapp.access_token,
        whatsapp_phone_number_id=config.whatsapp.phone_number_id,
        whatsapp_business_account_id=config.whatsapp.business_account_id,
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
        logger=router_logger,
    )
