import os
import aiohttp
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import dotenv_values


async def get_token(session, url, headers=None):
    async with session.get(url, headers=headers) as response:
        return response["access_token"]


async def refresh_token():
    """
    Refreshes the facebook access token and updates the `.env` file with the
    new whatsapp access token. See documentation
    `[here](https://developers.facebook.com/docs/marketing-api/system-users/install-apps-and-generate-tokens/#refresh-token)`
    """
    app_id = os.getenv("FACEBOOK_APP_ID")
    app_secret = os.getenv("FACEBOOK_APP_SECRET")
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    url = (
        "https://graph.facebook.com/18.0/oauth/access_token?"
        "grant_type=fb_exchange_token&"
        f"client_id={app_id}&"
        f"client_secret={app_secret}&"
        "set_token_expires_in_60_days=true&"
        f"fb_exchange_token={access_token}"
    )
    headers = {""}

    async with aiohttp.ClientSession() as session:
        new_token = await get_token(session, url, headers=headers)

    environment = os.getenv("ENVIRONMENT", "development")

    match environment:
        case "production":
            env_file_path = ".env.production"
        case _:
            env_file_path = ".env.development"

    env_vars = dotenv_values(env_file_path)
    env_vars["WHATSAPP_ACCESS_TOKEN"] = new_token

    # Write changes back to the .env file
    with open(env_file_path, "w") as env_file:
        for key, value in env_vars.items():
            env_file.write(f"{key}={value}\n")


scheduler = BackgroundScheduler()
