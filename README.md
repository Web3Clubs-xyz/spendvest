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

**SSH**
```
git clone gh repo clone Web3Clubs-xyz/spendvest
```

**Github CLI**
```bash
gh repo clone Web3Clubs-xyz/spendvest
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

The default value is `development`. If you just need to run Spendvest on your
machine, you can just set `ENVIRONMENT` to `production`.

```bash
export ENVIRONMENT="production"
```

and copy the `.env` template file to `.env.production`

```bash
cp .env .env.local
```

If you are contributing to Spendvest, you should set `ENVIRONMENT` to
`development` and define your development environment variables in
`/src/.env.development`.

```bash
export ENVIRONMENT="development"
```

and copy the `.env` template file to `.env.development`

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

## Development

If you are actively contributing to spendvest, please ensure you are familiar
with working with language servers, linters and formatters. This ensures
there's consistent code formatting among contributors. The following is the
list of tools used and the settings.

|Tool|Purpose|Settings|
|===|===|===|
|[pyright](https://github.com/microsoft/pyright)|Type Checker|`default`|
|[black](https://github.com/psf/black)|Code Formatter|`default`|
|[flake8](https://github.com/PyCQA/flake8)|Linter|`./.flake8`|

Ensure you set up either your IDE to work with these tools or use the tools
directly to format and lint your code.
