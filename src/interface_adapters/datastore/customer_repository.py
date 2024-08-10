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
    AccountTypes,
    Customers,
    UserAccounts,
    Users,
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
            select(Customers).filter(Customers.user_account.user_id == customer.id)
        )
        db_customer = result.scalars().first()

        if db_customer is None:
            raise Exception()

        user = db_customer.user_account.user

        user.first_name = customer.first_name
        user.middle_name = customer.middle_name
        user.last_name = customer.last_name
        db_customer.phone_number = customer.phone_number

        return customer

    @override
    async def get_customer(self, identifier: str) -> Customer | None:
        """
        Retrieves a customer from the database using SQLAlchemy.

        Args:
            identifier (str): identifier used to get customers from the database
        """

        result = await self._session.execute(
            select(Customers).filter(Customers.account_id == identifier)
        )

        db_customer = result.scalars().first()

        if db_customer is None:
            return None

        user = db_customer.user_account.user

        customer = Customer(
            customer_id=db_customer.account_id,
            phone_number=db_customer.phone_number,
            first_name=user.first_name,
            middle_name=user.middle_name,
            last_name=user.last_name,
        )

        return customer

    @override
    async def create_customer(
        self,
        customer: Customer,
    ) -> Customer:
        """
        Adds the `User` entity and the `Customer` entity to the database and
        calls `create_wallet` to create a default wallet for them.
        """

        result = await self._session.execute(
            select(AccountTypes).filter(AccountTypes.id == 1)
        )
        account_type: AccountTypes | None = result.scalars().first()

        if account_type is None:
            account_type = AccountTypes(id=1, name="CUSTOMER")

        # User account
        db_customer = Customers()
        user = Users(
            id=str(uuid4().hex),
            first_name=customer.first_name,
            middle_name=customer.middle_name,
            last_name=customer.last_name,
        )
        db_customer.user_account = UserAccounts(
            id=str(uuid4().hex), user_id=user.id, type_id=account_type.id, user=user
        )
        db_customer.user_account.account_type = account_type

        self._session.add(db_customer)
        await self.session.commit()

        return customer
