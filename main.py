from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from logging import Logger
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import ValidationError
from composition_root import SpendvestContainer
from interface_adapters.payments.sasapay.api_data_types import (
    PersonalOnboardingResponseParameters,
    RequestPaymentCallbackResultsParameters,
    TransferFundsResultsParameters,
)
from dependency_injector.wiring import Provide, inject
from interface_adapters.payments.sasapay.payment_events_publisher import (
    PaymentEventsPublisher,
)
from interface_adapters.views.router import WhatsappRouter, WhatsappWebhook
from token_refresh import refresh_fb_token, refresh_sasapay_token, scheduler

container = SpendvestContainer()

app: FastAPI = FastAPI()

webhook_router = APIRouter(prefix="/webhooks")
sasapay_callbacks_router = APIRouter(prefix="/sasapay")
callback_router = APIRouter(prefix="/callbacks")
main_router = APIRouter(prefix="/api/v1")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Get token at startup
    await refresh_fb_token()
    await refresh_sasapay_token()

    # Start the scheduler
    scheduler.start()
    await container.db_session_factory()
    container.wire(modules=[__name__])
    container.init_resources()

    # Yield control back to the application
    yield

    # Shut down the scheduler
    scheduler.shutdown()
    container.shutdown_resources()


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
@inject
async def request_payment_response(
    event_id: str,
    request: Request,
    logger: Logger = Depends(Provide[SpendvestContainer.fastapi_logger]),
    payment_event_publisher: PaymentEventsPublisher = Depends(
        Provide[SpendvestContainer.payment_event_publisher]
    ),
):
    """
    Notifies payments event publisher of a request payment response event.
    """
    try:
        data = await request.json()
        results = RequestPaymentCallbackResultsParameters(
            merchant_request_id=data["MerchantRequestID"],
            checkout_request_id=data["CheckoutRequestID"],
            payment_request_id=data["PaymentRequestID"],
            result_code=data["ResultCode"],
            result_description=data["ResultDesc"],
            source_channel=data["SourceChannel"],
            transaction_amount=data["TransAmount"],
            bill_reference_number=data["BillRefNumber"],
            transaction_date=data["TransactionDate"],
            customer_mobile=data["CustomerMobile"],
            transaction_code=data["TransactionCode"],
            third_party_transaction_id=data["ThirdPartyTransID"],
        )
        logger.info(f"Received request payment callback payload: {data}")
        payment_event_publisher.notify(
            event_type="request_payment_response", event_id=event_id, data=results
        )
    except ValidationError as e:
        logger.error(f"ValidationError: {e.json}")
        raise HTTPException(status_code=400, detail=e.errors())

    except Exception as e:
        logger.error(f"Error: {str(e)}")


@sasapay_callbacks_router.post("/transfer_funds/{event_id}")
@inject
async def transfer_funds_response(
    event_id: str,
    request: Request,
    logger: Logger = Depends(Provide[SpendvestContainer.fastapi_logger]),
    payment_event_publisher: PaymentEventsPublisher = Depends(
        Provide[SpendvestContainer.payment_event_publisher]
    ),
):
    """
    Notifies payments event publisher of a transfer funds response event.
    """
    try:
        results = await request.json()
        data = TransferFundsResultsParameters(
            merchant_request_id=results["MerchantRequestID"],
            checkout_request_id=results["CheckoutRequestID"],
            result_code=results["ResultCode"],
            result_description=results["ResultDesc"],
            merchant_code=results["MerchantCode"],
            transaction_amount=results["TransactionAmount"],
            transaction_charge=results["TransactionCharge"],
            merchant_fees=results["MerchantFees"],
            merchant_account_balance=results["MerchantAccountBalance"],
            merchant_transaction_reference=results["MerchantTransactionReference"],
            transaction_date=results["TransactionDate"],
            recepient_account_number=results["RecipientAccountNumber"],
            destination_channel=results["DestinationChannel"],
            source_channel=results["SourceChannel"],
            sasapay_transaction_id=results["SasaPayTransactionID"],
            recepient_name=results["RecipientName"],
            sender_account_number=results["SenderAccountNumber"],
        )
        payment_event_publisher.notify(
            event_type="transfer_funds_response", event_id=event_id, data=data
        )
    except ValidationError as e:
        logger.error(f"ValidationError: {e.json}")
        raise HTTPException(status_code=400, detail=e.errors())

    except Exception as e:
        logger.error(f"Error: {str(e)}")


@webhook_router.post("/whatsapp")
@inject
async def whatsapp_webhook(
    request: Request,
    logger: Logger = Depends(Provide[SpendvestContainer.fastapi_logger]),
    router: WhatsappRouter = Depends(Provide[SpendvestContainer.whatsapp_router]),
):
    try:
        data = await request.json()
        notification = WhatsappWebhook(**data)
        # fastapi_logger.info(f"Got message: {notification}")
        await router.handle_whatsapp_webhook(data=notification)

        return JSONResponse(content={"message": "200 OK"})
    except ValidationError as e:
        logger.error(f"ValidationError: {e.json()}")
        raise HTTPException(status_code=400, detail=e.errors())

    except Exception as e:
        # logger.error(f"Unexpected Error: {str(e)}")
        print(str(e))
        raise HTTPException(status_code=500, detail="Internal server error.")


@webhook_router.get("/whatsapp")
async def verify_callback(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    # Check the mode and token sent are correct
    if (
        mode == "subscribe"
        and token == container.config.whatsapp.webhook_verification_token()
    ):
        # Respond with 200 OK and challenge token from the request
        print("Webhook verified successfully!")
        return PlainTextResponse(content=challenge, status_code=200)
    else:
        # Respond with '403 Forbidden' if verify tokens do not match
        raise HTTPException(status_code=403, detail="Forbidden")


@app.post("/")
@inject
async def test(
    req: Request, logger: Logger = Depends(Provide[SpendvestContainer.fastapi_logger])
):
    body = await req.body()
    logger.info(f"Got request {body.decode()}")
    return {"message": "200 OK"}


# compose routes
callback_router.include_router(sasapay_callbacks_router)
main_router.include_router(callback_router)
main_router.include_router(webhook_router)

app.include_router(main_router)
