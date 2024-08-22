from dataclasses import dataclass
from domain.entities.services.user_services import CustomerService
from domain.entities.services.wallet_service import WalletService
from domain.entities.sessions import UserSession
from interface_adapters.ui.presenters.whatsapp_presenters import (
    WhatsappWithdrawPresenter,
)


@dataclass
class WithdrawUseCase:
    """
    Use case that coordinates the withdrawal process for customers.
    """

    presenter: WhatsappWithdrawPresenter
    wallet_service: WalletService
    customer_service: CustomerService

    async def withdraw_funds(
        self, amount: int, receiving_phone_number: int, session: UserSession
    ) -> None:
        customer = await self.customer_service.get_customer_by_whatsapp_id(
            whatsapp_id=session.id
        )

        if customer is None:
            # prompt user that the account doesn't exist.
            return

        wallet = await self.wallet_service.get_wallet_by_customer_id(
            customer_id=customer.id
        )

        withdrawal_amount = await self.wallet_service.withdraw(
            wallet=wallet, amount=amount, receiving_phone_number=receiving_phone_number
        )

        await self.presenter.render_successful_withdrawal(
            recepient=session.id, amount=withdrawal_amount
        )

    async def prompt_user(self, session: UserSession) -> None:
        await self.presenter.prompt_user(recepient=session.id)
        # TODO
        # Update session
        await self.presenter.prompt_user(recepient=session.id)
