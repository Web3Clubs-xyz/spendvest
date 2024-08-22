from dataclasses import dataclass
from domain.entities.services.session_service import SessionService
from domain.entities.services.user_services import CustomerService
from domain.entities.sessions import SessionType, UserSession
from interface_adapters.ui.presenters.whatsapp_presenters import (
    WhatsappHomeInterfacePresenter,
)


@dataclass
class NewSessionUseCase:
    """
    Use case for creating new sessions for customers.
    """

    session_service: SessionService
    presenter: WhatsappHomeInterfacePresenter
    customer_service: CustomerService

    async def prompt_user(self, recepient_id: str):

        customer = await self.customer_service.get_customer_by_whatsapp_id(
            whatsapp_id=recepient_id
        )

        if customer is None:
            session_type = SessionType(id=2, name="Registration")
            session = UserSession(
                id=recepient_id, user=None, session_type=session_type, current_step=0
            )
            await self.session_service.save_customer_session(customer_session=session)
            await self.presenter.render_unregistered_home_view(recepient=recepient_id)

        session_type = SessionType(id=1, name="NewSession")
        session = UserSession(
            id=recepient_id, user=customer, session_type=session_type, current_step=0
        )
        await self.session_service.save_customer_session(customer_session=session)
        await self.presenter.render_registered_home_view(recepient=recepient_id)
