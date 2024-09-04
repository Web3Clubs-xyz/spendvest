# Spendvest 💰

Spenvest enables mobile money users to save money while spending.

---

## Third Party Setup 🔗.

Spendvest currently uses [Whatsapp](https://business.whatsapp.com/) as its
frontend and [Sasapay](https://sasapay.co.ke/) as the payment gateway and
e-wallet provider. You need to set up an app on both platforms in order to get
the neccessary environment variables that Spendvest uses to communicate with
the platform.

### Whatsapp

Since Spendvest uses [Interactive Flow
Messages](https://developers.facebook.com/docs/whatsapp/cloud-api/messages/interactive-flow-messages),
the business account tied to the whatsapp application should be verified. Once
verified, you can now create flows and communicate with users in a user
friendly way.

You can follow the guide on [Facebook's Developer
Website](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started)
on how to set up a whatsapp application on your facebook developer account.

Once the whatsapp application is created, you can use the temporary access
token as the value for `$WHATSAPP_ACCESS_TOKEN`. For a production setup, you
need to set up a permanent access token. You can learn how to set this up on
Facebook's documentation
[here](https://developers.facebook.com/docs/whatsapp/business-management-api/get-started#system-users)

### Sasapay

Getting set up with sasapay is straight forward. Just go through their
[documentation](https://docs.sasapay.app/docs/introduction/) on how to create a
sandbox and production app.

## Deployment 🚢

This section will walk you through the steps needed to get Spendvest up and
running 🏃.

### Cloning The Repo 📂

The first thing to do is clone the repo

**Https**
```bash
git clone https://github.com/Web3Clubs-xyz/spendvest.git
```

### Logging

Spendvest is set up to send logs as json to files in src/logs. Ensure this
`logs` folder is created. You can run this at the root of the project.

```
mkdir src/logs
```

### Installing Dependencies 🚸

change directory to the cloned repo folder

```bash
cd /path/to/spendvest
```

install dependencies

```bash
pipx install poetry
poetry install
```

### Environment Variables 🔑

First we need to export the `ENVIRONMENT` variable. This will help Spendvest
identify what environment it is running in.

```bash
export ENVIRONMENT=<DEPLOYMENT_ENVIRONMENT>
```

The default value is `development`. If you just need to deploy Spendvest on your
production machine, you can just set `ENVIRONMENT` to `production`.

```bash
export ENVIRONMENT="production"
```

and copy the `.env` template file to `.env.production`

```bash
cp .env .env.production
```

If you are contributing to Spendvest, you should set `ENVIRONMENT` to
`development` and define your development environment variables in
`/src/.env.development`.

```bash
export ENVIRONMENT="development"
```

and copy the `.env` template file to `.env.development`

These are the environment variables you need to set up for spendvest

|Name|Description|Example|Datatype|
|---|---|---|---|
|FACEBOOK_ENDPOINT_BASE_URL|This is the base url for communicating with facebook apis|`https://graph.facebook.com/v17.0/106540352242922/messages`|`string`|
|FACEBOOK_APP_ID|The ID identifying the facebook application our code is communicating with|ica*********bvube|`string`|
|FACEBOOK_APP_SECRET|Facebook app's secret|Ipe******oinvep|`string`|
|WHATSAPP_ACCESS_TOKEN|User access token that us used to authorise communication with facebook APIs|KpI********veoin|`string`|
|WHATSAPP_WEBHOOK_VERIFICATION_TOKEN|This token is used to complete a handshake that is necessary to prove that the endpoint we provide an application is an endpoint that we own|123456|`alpha-numeric`|
|WHATSAPP_BUSINESS_ACCOUNT_ID|Business account ID attached to the phone number being used|3876418763413|`numeric`|
|WHATSAPP_PHONE_NUMBER_ID|ID of the whatsapp phone number that will be communicating with users|739873459|`numeric`|
|SASAPAY_PERSONAL_ONBOARDING_ENDPOINT|Endpoint that we call so that sasapay can enable us to onboard users with a wallet|`https://sandbox.sasapay.app/api/v2/waas/personal-onboarding/`|`string`|
|SASAPAY_PERSONAL_ONBOARDING_CONFIRMATION_ENDPOINT|Endpoint we call so that sasapay can confirm a user's wallet was registered|`https://sandbox.sasapay.app/api/v2/waas/personal-onboarding/confirmation/`|`string`|
|SASAPAY_REQUEST_PAYMENT_ENDPOINT|Endpoint we call so that sasapay can request payments from users|`https://sandbox.sasapay.app/api/v2/waas/payments/request-payment/`|`string`|
|SASAPAY_TRANSFER_FUNDS_ENDPOINT|Endpoint we call so that we can transfer funds from a user's wallet to other beneficiaries|`https://sandbox.sasapay.app/api/v2/waas/payments/send-money/`|`string`|
|SASAPAY_CLIENT_ID|Sasapay application ID|IhJg*******jluef|`string`|
|SASAPAY_CLIENT_SECRET|Sasapay application secret|Ljeg*******kugUoE|`string`|
|SASAPAY_ACCESS_TOKEN|Access token used to authenticate our API requests on sasapay's platform|SsEgu*******lkjgfe|`string`|
|SASAPAY_MERCHANT_CODE|Merchant code provided by Viewtech that will be attached to the wallets being created on spendvest|876345|`numeric`|
|MYSQL_DATABASE_USER|Database user in our MYSQL database|db_user|`string`|
|MYSQL_DATABASE_PASSWORD|Database user's password used for authentication in the database|db_user_password|`string`|
|MYSQL_DATABASE_HOST|The database's hostname or ip address|127.0.0.1|`string`|
|MYSQL_DATABASE_NAME|The name of the database we are connecting to|spendvest|`string`|
|SPENDVEST_SITE_URL|The site url where our spendvest api is hosted|`https://spendvest.xyz`|`string`|
|LOG_DIR|Directory where logs are stored|/home/&lt;username&gt;/logs|`string`|

For niche or advanced use cases, you can modify the `/src/composition_root.py`
file and define where Spendvest will look for your custom environment
variables.

### Running 🚀🚀

Once your environment variables are set up, you can now run the main script
directly using poetry.

```bash
poetry run spendvest
```

For production, you should use uvicorn

```
uvicorn src.main:app --host 0.0.0.0 --port 80 --reload --workers 4
```

or you can run the convenient `run_server.py` module after activating the
virtual environment with the `$ poetry shell` command

```bash
pyenv install 3.10
pyenv local 3.10
poetry shell
python run_server.py
```

## Development

If you are actively contributing to spendvest, please ensure you are familiar
with working with:
1. Language servers
2. Linters
3. Formatters
4. Debuggers

This ensures there's consistent code formatting among contributors and a
similar workflow for the team. The following is the list of tools used and the
settings.

|Tool|Purpose|Settings|
|---|---|---|
|[pyright](https://github.com/microsoft/pyright)|Type Checker|`default`|
|[black](https://github.com/psf/black)|Code Formatter|`default`|
|[flake8](https://github.com/PyCQA/flake8)|Linter|`./.flake8`|
|[debugpy](https://github.com/microsoft/debugpy)|Debugger|Customise debugger settings to fit your environment.|

Ensure you set up either your IDE to work with these tools or use the tools
directly to format and lint your code.
