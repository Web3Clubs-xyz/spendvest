from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse
from apscheduler.triggers.interval import IntervalTrigger

from composition_root import SpendvestContainer
from interface_adapters.payments.sasapay.api_data_types import (
    PersonalOnboardingResponseParameters,
    RequestPaymentResponseParameters,
    TransferFundsResponseParameters,
)
from interface_adapters.views.router import WhatsappWebhook
from token_refresh import refresh_sasapay_token, scheduler, refresh_fb_token

container = SpendvestContainer()

app: FastAPI = FastAPI()

webhook_router = APIRouter(prefix="/webhooks")
sasapay_callbacks_router = APIRouter(prefix="/sasapay")
callback_router = APIRouter(prefix="/callbacks")
main_router = APIRouter(prefix="/api/v1")

# Add a job to the scheduler
scheduler.add_job(refresh_fb_token, IntervalTrigger(days=50))
scheduler.add_job(refresh_sasapay_token, IntervalTrigger(minutes=45))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Start the scheduler
    scheduler.start()
    await container.sqlalchemy_session_manager().setup()

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


@sasapay_callbacks_router.post("/personal_onboarding/{event_id}")
def personal_onboarding_response(
    event_id: str, data: PersonalOnboardingResponseParameters
):
    """
    Notifies payments event publisher of a personal onboarding response event.
    """
    container.payment_event_publisher().notify(
        event_type="personal_onboarding_response", event_id=event_id, data=data
    )


@sasapay_callbacks_router.post("/request_payment/{event_id}")
def request_payment_response(event_id: str, data: RequestPaymentResponseParameters):
    """
    Notifies payments event publisher of a request payment response event.
    """
    container.payment_event_publisher().notify(
        event_type="request_payment_response", event_id=event_id, data=data
    )


@sasapay_callbacks_router.post("/transfer_funds/{event_id}")
def transfer_funds_response(event_id: str, data: TransferFundsResponseParameters):
    """
    Notifies payments event publisher of a transfer funds response event.
    """
    container.payment_event_publisher().notify(
        event_type="transfer_funds_response", event_id=event_id, data=data
    )


@webhook_router.post("/whatsapp")
async def whatsapp_webhook(notification: WhatsappWebhook):
    await container.whatsapp_router().handle_whatsapp_webhook(data=notification)

    return JSONResponse(content={"message": "200 OK"})


# compose routes
callback_router.include_router(sasapay_callbacks_router)
main_router.include_router(callback_router)
main_router.include_router(webhook_router)

app.include_router(main_router)
