from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import os
from fastapi import APIRouter, FastAPI
from apscheduler.triggers.interval import IntervalTrigger

from composition_root import SpendvestContainer
from interface_adapters.payments.sasapay.api_data_types import (
    PersonalOnboardingResponseParameters,
    RequestPaymentResponseParameters,
    TransferFundsResponseParameters,
)
from interface_adapters.views.router import WhatsappWebhook
from token_refresh import scheduler, refresh_token

container = SpendvestContainer()

app: FastAPI = FastAPI()

webhook_router = APIRouter(prefix="/webhooks")
sasapay_callbacks_router = APIRouter(prefix="/sasapay")
callback_router = APIRouter(prefix="/callbacks")
callback_router.include_router(sasapay_callbacks_router)
main_router = APIRouter(prefix="/api/v1")
main_router.include_router(callback_router)
main_router.include_router(webhook_router)

# Add a job to the scheduler
scheduler.add_job(refresh_token, IntervalTrigger(days=50))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Start the scheduler
    scheduler.start()

    # Yield control back to the application
    yield

    # Shut down the scheduler
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)


@webhook_router.post("/sasapay")
async def sasapay_webhook():
    """
    Sasapay app callback url used to send IPNs.
    """
    pass


@sasapay_callbacks_router.post(
    os.getenv(
        "SASAPAY_PERSONAL_ONBOARDING_CALLBACK_URL",
        "/wallet/registration/personal_onboarding/{event_id}",
    )
)
def personal_onboarding_response(
    event_id: str, data: PersonalOnboardingResponseParameters
):
    """
    Notifies payments event publisher of a personal onboarding response event.
    """
    container.payment_events_publisher().notify(
        event_type="personal_onboarding_response", event_id=event_id, data=data
    )


@sasapay_callbacks_router.post(
    os.getenv(
        "SASAPAY_REQUEST_PAYMENT_CALLBACK_URL",
        "/wallet/registration/request_payment/{event_id}",
    )
)
def request_payment_response(event_id: str, data: RequestPaymentResponseParameters):
    """
    Notifies payments event publisher of a request payment response event.
    """
    container.payment_events_publisher().notify(
        event_type="request_payment_response", event_id=event_id, data=data
    )


@sasapay_callbacks_router.post(
    os.getenv(
        "SASAPAY_TRANSFER_FUNDS_CALLBACK_URL",
        "/wallet/registration/transfer_funds/{event_id}",
    )
)
def transfer_funds_response(event_id: str, data: TransferFundsResponseParameters):
    """
    Notifies payments event publisher of a transfer funds response event.
    """
    container.payment_events_publisher().notify(
        event_type="transfer_funds_response", event_id=event_id, data=data
    )


@webhook_router.post("/whatsapp")
async def whatsapp_webhook(notification: WhatsappWebhook):
    await container.whatsapp_router().handle_whatsapp_webhook(data=notification)
