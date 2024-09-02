from abc import ABC, abstractmethod

from domain.usecases.interfaces.register_account_interfaces import (
    IRegistrationEventObserver,
)


class IHomeInterfacePresenter(ABC):
    """
    Abstract home interface presenter.

    Interface for a presenter that shows a user the actions that they can take
    depending on their registration status.

    Methods:
        render_registered_home_view(recepient: `str`): Renders the home view of
            customers that have registered on the platform.
        render_unregistered_home_view(recepient: `str`): Renders the home view
            of customers that have not registered on the platform yet.
    """

    @abstractmethod
    async def render_registered_home_view(self, recepient: str) -> None:
        pass

    @abstractmethod
    async def render_unregistered_home_view(self, recepient: str) -> None:
        pass


class IRegisterSasapayWalletPresenter(IRegistrationEventObserver, ABC):
    """
    Abstract wallet registration presenter

    Interface of a presenter that takes the user through the process of
    registering a sasapay wallet.

    Methods:
        render_form(): Renders the registration that captures the information
            needed to register a sasapay wallet.
        render_invalid_form(): Prompts the user that they have entered
            incorrect values for for the registration form.
        render_otp: Prompts the user to enter the OTP they received on their
            phone.
        render_failed_otp: Informs the user that they entered the wrong OTP.
        render_successful_registration: Informs the user that the registration
            process went through successfully.
        update(event: `object`): Updates the presenter on registration events
            that it has subscribed to.
    """

    @abstractmethod
    async def render_form(self, recepient: str) -> None:
        pass

    @abstractmethod
    async def render_invalid_form(self, recepient: str) -> None:
        pass

    @abstractmethod
    async def render_otp(self, recepient: str) -> None:
        pass

    @abstractmethod
    async def render_failed_otp(self, recepient: str) -> None:
        pass

    @abstractmethod
    async def render_successful_registration(self, recepient: str) -> None:
        pass


class ISasapaySendMoneyPresenter(ABC):
    pass


class ISasapayWithdrawPresenter(ABC):
    pass
