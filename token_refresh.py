import os
import aiohttp
from aiohttp import ClientSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import dotenv_values, load_dotenv, set_key


async def get_fb_token(session: ClientSession, url: str, headers=None):
    async with session.get(url, headers=headers) as response:
        res = await response.json()

        if "access_token" in res:
            return res["access_token"]

        raise ValueError(f"Access token wasn't returned: {res}")


async def refresh_fb_token():
    """
    Refreshes the facebook access token and updates the `.env` file with the
    new whatsapp access token. See documentation
    `[here](https://developers.facebook.com/docs/marketing-api/system-users/install-apps-and-generate-tokens/#refresh-token)`
    """
    app_id = os.getenv("FACEBOOK_APP_ID")
    app_secret = os.getenv("FACEBOOK_APP_SECRET")
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    url = (
        "https://graph.facebook.com/v20.0/oauth/access_token?"
        "grant_type=fb_exchange_token&"
        f"client_id={app_id}&"
        f"client_secret={app_secret}&"
        "set_token_expires_in_60_days=true&"
        f"fb_exchange_token={access_token}"
    )
    headers = {}

    async with aiohttp.ClientSession() as session:
        new_token = await get_fb_token(session, url, headers=headers)

    print(f"New FB token: {new_token}")
    environment = os.getenv("ENVIRONMENT", "development")

    match environment:
        case "production":
            env_file_path = ".env.production"
        case _:
            env_file_path = ".env.development"

    env_vars = dotenv_values(env_file_path)
    set_key(env_file_path, "WHATSAPP_ACCESS_TOKEN", new_token)

    # Write changes back to the .env file
    with open(env_file_path, "w") as env_file:
        for key, value in env_vars.items():
            if key != "WHATSAPP_ACCESS_TOKEN" and value is not None:
                set_key(env_file_path, key, value)

            if key == "MYSQL_DATABASE_PASSWORD":
                env_file.write(f'{key}="{value}"')
                continue

            env_file.write(f"{key}={value}\n")

    # Reload the .env file to update the environment variables in the current
    # process
    load_dotenv(env_file_path, override=True)
    print(f"Facebook token from environment: {os.getenv('WHATSAPP_ACCESS_TOKEN')}")


async def get_sasapay_token(session: aiohttp.ClientSession) -> str:
    url = "https://sandbox.sasapay.app/api/v1/auth/token/"
    params = {"grant_type": "client_credentials"}
    client_id = os.getenv("SASAPAY_CLIENT_ID", "")
    client_secret = os.getenv("SASAPAY_CLIENT_SECRET", "")
    auth = aiohttp.BasicAuth(client_id, client_secret)

    async with session.get(url=url, auth=auth, params=params) as response:
        res = await response.json()
        access_token = res["access_token"]

        return access_token


async def refresh_sasapay_token() -> None:
    async with aiohttp.ClientSession() as session:
        new_token = await get_sasapay_token(session=session)

    print(f"New Sasapay token: {new_token}")
    environment = os.getenv("ENVIRONMENT", "development")

    match environment:
        case "production":
            env_file_path = ".env.production"
        case _:
            env_file_path = ".env.development"

    env_vars = dotenv_values(env_file_path)
    set_key(env_file_path, "SASAPAY_ACCESS_TOKEN", new_token)

    # Write changes back to the .env file
    with open(env_file_path, "w") as env_file:
        for key, value in env_vars.items():
            if key != "SASAPAY_ACCESS_TOKEN" and value is not None:
                set_key(env_file_path, key, value)

            if key == "MYSQL_DATABASE_PASSWORD":
                env_file.write(f'{key}="{value}"')
                continue

            env_file.write(f"{key}={value}\n")

    # Reload the .env file to update the environment variables in the current
    # process
    load_dotenv(env_file_path, override=True)
    print(f"Sasapay token from environment: {os.getenv('SASAPAY_ACCESS_TOKEN')}")


scheduler = AsyncIOScheduler()

# Add a job to the scheduler
scheduler.add_job(refresh_fb_token, IntervalTrigger(days=50))
scheduler.add_job(refresh_sasapay_token, IntervalTrigger(minutes=45))
