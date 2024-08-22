import os

from dependency_injector import containers, providers
from dotenv import load_dotenv


environment = os.getenv("ENVIRONMENT", "development").lower()

if environment == "development":
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env.development")
    load_dotenv(dotenv_path=dotenv_path)
elif environment == "production":
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env.production")
    load_dotenv(dotenv_path=dotenv_path)


class SpendvestConfig(containers.DeclarativeContainer):
    """
    Inversion of control container for config.
    """

    config = providers.Configuration()
    config.facebook.endpoint_base_url.from_env("FACEBOOK_ENDPOINT_BASE_URL")
    config.facebook.app_id.from_env("FACEBOOK_APP_ID")
    config.facebook.app_secret.from_env("FACEBOOK_APP_SECRET")
    config.whatsapp.access_token.from_env("WHATSAPP_ACCESS_TOKEN")
    config.whatsapp.phone_number_id.from_env("WHATSAPP_PHONE_NUMBER_ID")
    config.whatsapp.business_account_id.from_env("WHATSAPP_BUSINESS_ACCOUNT_ID")
    config.sasapay.client_id.from_env("SASAPAY_CLIENT_ID")
    config.sasapay.client_secret.from_env("SASAPAY_CLIENT_SECRET")
    config.sasapay.merchant_code.from_env("SASAPAY_MERCHANT_CODE")
    config.sasapay.wallet.personal_onboarding_endpoint.from_env(
        "SASAPAY_PERSONAL_ONBOARDING_ENDPOINT"
    )
    config.sasapay.wallet.transfer_funds_endpoint.from_env(
        "SASAPAY_TRANSFER_FUNDS_ENDPOINT"
    )
    config.sasapay.wallet.request_payment_endpoint.from_env(
        "SASAPAY_REQUEST_PAYMENT_ENDPOINT"
    )
    config.sasapay.access_token.from_env("SASAPAY_ACCESS_TOKEN")
    config.mysql.database_user.from_env("MYSQL_DATABASE_USER")
    config.mysql.database_password.from_env("MYSQL_DATABASE_PASSWORD")
    config.mysql.database_host.from_env("MYSQL_DATABASE_HOST")
    config.mysql.database_name.from_env("MYSQL_DATABASE_NAME")
    config.spendvest_site_url.from_env("SPENDVEST_SITE_URL")
    config.log_dir.from_env("LOG_DIR")
