from dataclasses import dataclass, field
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession
from typing_extensions import override

from domain.entities.interfaces.user_interfaces import (
    CustomerRepository,
)
from domain.entities.users import Customer

from drivers.sqlalchemy.models import (
    Customers,
)


@dataclass
class SQLAlchemyCustomerRepository(CustomerRepository):
    """
    SQLAlchemy implementation of the Customer Repository

    Attributes:
        retrieval_strategy (UserRetrievalStrategy): The retrieval strategy used
        to get customers from the database using sqlalchemy
        session (Session): The sqlalchemy session used to persist data to the
        database
    """

    _session: AsyncSession = field(init=False)

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @property
    def session(self) -> AsyncSession:
        return self._session

    @session.setter
    def session(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def save_customer(self, customer: Customer) -> Customer:
        """
        Saves a customer entity to the data base using SQLAlchemy

        Args:
            user (User): The instance of the `User` entity that is being
            persisted to the database

        Returns:
            User: The `User` entity that has been saved to the database
        """

        result = await self._session.execute(
            select(Customers).filter(Customers.id == customer.id)
        )
        db_customer = result.scalars().first()

        if db_customer is None:
            raise Exception()

        db_customer.first_name = customer.first_name
        db_customer.middle_name = customer.middle_name
        db_customer.last_name = customer.last_name
        db_customer.phone_number = customer.phone_number
        db_customer.email = customer.email
        db_customer.whatsapp = (
            customer.whatsapp if customer.whatsapp is not None else ""
        )

        return customer

    @override
    async def get_customer(self, identifier: str) -> Customer | None:
        """
        Retrieves a customer from the database using SQLAlchemy.

        Args:
            identifier (str): identifier used to get customers from the database
        """

        result = await self._session.execute(
            select(Customers).filter(Customers.id == identifier)
        )

        db_customer = result.scalars().first()

        if db_customer is None:
            return None

        customer = Customer(
            id=db_customer.id,
            phone_number=db_customer.phone_number,
            first_name=db_customer.first_name,
            middle_name=db_customer.middle_name,
            last_name=db_customer.last_name,
            email=db_customer.email,
            whatsapp=db_customer.whatsapp,
        )

        return customer

    @override
    async def get_customer_by_whatsapp_id(self, whatsapp_id: str) -> Customer | None:
        """
        Retrieves a customer from the database based on their whatsapp account
        """
        result = await self._session.execute(
            select(Customers).filter(Customers.whatsapp == whatsapp_id)
        )

        customer = result.scalars().first()

        if customer is None:
            return None

        return Customer(
            id=customer.id,
            first_name=customer.first_name,
            middle_name=customer.middle_name,
            last_name=customer.last_name,
            email=customer.email,
            phone_number=customer.phone_number,
            whatsapp=customer.whatsapp,
        )

    @override
    async def create_customer(
        self,
        customer: Customer,
    ) -> Customer:
        """
        Adds the `User` entity and the `Customer` entity to the database and
        calls `create_wallet` to create a default wallet for them.
        """

        # User account
        db_customer = Customers(
            id=str(uuid4().hex),
            first_name=customer.first_name,
            middle_name=customer.middle_name,
            last_name=customer.last_name,
        )

        self._session.add(db_customer)
        await self.session.commit()

        return customer
