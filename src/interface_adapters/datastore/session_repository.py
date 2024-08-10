from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession
from typing_extensions import override
from domain.entities.interfaces.session_interfaces import ISessionRepository

from domain.entities.sessions import SessionType, UserSession

from domain.entities.users import Customer
from drivers.sqlalchemy.models import (
    Customers,
    UserAccounts,
    UserSessions as UserSessionsModel,
    Users,
)


class SQLAlchemySessionRepository(ISessionRepository):
    _session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @property
    def session(self) -> AsyncSession:
        return self._session

    @session.setter
    def session(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def get_user_session(self, external_id: str) -> UserSession | None:
        result = await self._session.execute(
            select(UserSessionsModel).filter(
                UserSessionsModel.external_id == external_id
            )
        )
        db_user_session = result.scalars().first()

        if db_user_session is None:
            return None

        db_session_type = db_user_session.session_type

        session_type: SessionType = SessionType(
            id=db_session_type.id, name=db_session_type.name
        )

        db_customer_result = await self._session.execute(
            select(Customers)
            .join(UserAccounts, Customers.account_id == UserAccounts.id)
            .join(Users, UserAccounts.user_id == Users.id)
            .where(Users.id == db_user_session.user_id)
        )

        db_customer = db_customer_result.scalars().first()

        if db_customer is None:
            user_session: UserSession = UserSession(
                id=db_user_session.id,
                user=None,
                session_type=session_type,
                current_step=db_user_session.current_step,
                external_id=db_user_session.external_id,
            )

            return user_session

        customer = Customer(
            customer_id=db_customer.user_account.id,
            phone_number=db_customer.phone_number,
            first_name=db_customer.user_account.user.first_name,
            middle_name=db_customer.user_account.user.middle_name,
            last_name=db_customer.user_account.user.last_name,
        )

        user_session: UserSession = UserSession(
            id=db_user_session.id,
            user=customer,
            session_type=session_type,
            current_step=db_user_session.current_step,
            external_id=db_user_session.external_id,
        )

        return user_session

    @override
    async def save_user_session(self, session: UserSession) -> UserSession:
        result = await self._session.execute(
            select(UserSessionsModel).filter(UserSessionsModel.id == session.id)
        )
        db_user_session = result.scalars().first()

        if db_user_session is None:
            raise Exception

        db_user_session.current_step = session.current_step

        self._session.add(db_user_session)
        await self._session.commit()

        return session

    @override
    async def get_session_type(self) -> SessionType:
        raise NotImplementedError

    @override
    async def save_session_type(self, session_type: SessionType) -> SessionType:
        raise NotImplementedError
