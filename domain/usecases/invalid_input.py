from dataclasses import dataclass
from domain.entities.services.session_service import SessionService
from interface_adapters.ui.presenters.whatsapp_presenters import (
    WhatsappInvalidInputPresenter,
)


@dataclass
class InvalidInputUseCase:
    """
    Coordinates invalid input received from a customer.
    """

    session_service: SessionService
    presenter: WhatsappInvalidInputPresenter

    async def reject_input(self, session_id: str):
        await self.presenter.render_rejected_input(recepient=session_id)
