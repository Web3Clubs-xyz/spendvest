from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload

from domain.entities.sessions import SessionType, UserSession

from domain.entities.users import Customer
from drivers.sqlalchemy.models import CustomerSessions, Customers, SessionTypes


@dataclass
class SQLAlchemySessionRepository:
    session: AsyncSession

    async def get_user_session(self, session_id: str) -> UserSession | None:
        result = await self.session.execute(
            select(CustomerSessions)
            .options(selectinload(CustomerSessions.session_type))
            .options(selectinload(CustomerSessions.customer))
            .filter(CustomerSessions.id == session_id)
        )

        db_user_session = result.scalars().one_or_none()

        if db_user_session is None:
            return None

        print(f"{db_user_session}")

        db_session_type = db_user_session.session_type

        session_type: SessionType = SessionType(
            id=db_session_type.id, name=db_session_type.name
        )

        db_customer = db_user_session.customer

        if db_customer is None:
            user_session: UserSession = UserSession(
                id=db_user_session.id,
                user=None,
                session_type=session_type,
                current_step=db_user_session.current_step,
            )

            return user_session

        customer = Customer(
            id=db_customer.id,
            phone_number=db_customer.phone_number,
            first_name=db_customer.first_name,
            middle_name=db_customer.middle_name,
            last_name=db_customer.last_name,
            email=db_customer.email,
            whatsapp=db_customer.whatsapp,
        )

        user_session: UserSession = UserSession(
            id=db_user_session.id,
            user=customer,
            session_type=session_type,
            current_step=db_user_session.current_step,
        )

        return user_session

    async def save_user_session(self, customer_session: UserSession) -> UserSession:
        result = await self.session.execute(
            select(CustomerSessions).filter(CustomerSessions.id == customer_session.id)
        )
        db_user_session = result.scalars().one_or_none()

        if db_user_session is None:
            user_account_results = await self.session.execute(
                select(Customers).where(Customers.whatsapp == customer_session.id)
            )
            db_customer_account = user_account_results.scalars().one_or_none()

            customer_id = None

            if db_customer_account is not None:
                customer_id = db_customer_account.id

            db_user_session = CustomerSessions(
                id=customer_session.id,
                current_step=customer_session.current_step,
                type_id=customer_session.session_type.id,
                customer_id=customer_id,
            )

        db_user_session.current_step = customer_session.current_step
        db_user_session.type_id = customer_session.session_type.id

        self.session.add(db_user_session)
        await self.session.commit()

        return customer_session

    async def get_session_type(self, session_type_id) -> SessionType:
        result = await self.session.execute(
            select(SessionTypes).filter(SessionTypes.id == session_type_id)
        )
        db_session_type = result.scalars().first()

        if db_session_type is None:
            raise ValueError("Session type doesn't exist")

        return SessionType(id=db_session_type.id, name=db_session_type.name)

    async def save_session_type(self, session_type: SessionType) -> SessionType:
        db_session_type = SessionTypes(id=session_type.id, name=session_type.name)

        self.session.add(db_session_type)
        await self.session.commit()

        return session_type

    async def delete_customer_session(self, customer_session: UserSession) -> bool:
        result = await self.session.execute(
            select(CustomerSessions).filter(CustomerSessions.id == customer_session.id)
        )
        db_customer_session = result.scalars().first()

        if db_customer_session is None:
            raise ValueError("Customer's session doesn't exist")

        await self.session.delete(db_customer_session)
        await self.session.commit()

        return True
