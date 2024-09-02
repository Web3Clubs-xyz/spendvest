from dataclasses import dataclass
from sqlalchemy.ext.asyncio.session import AsyncSession

from domain.entities.payments import Wallet
from domain.entities.users import Customer
from drivers.sqlalchemy.models import Customers, Wallets


@dataclass
class SQLAlchemyRegistrationRepository:
    session: AsyncSession

    def save_customer(self, customer: Customer) -> Customer:
        db_customer = Customers(
            id=customer.id,
            first_name=customer.first_name,
            middle_name=customer.middle_name,
            last_name=customer.last_name,
            phone_number=customer.phone_number,
            email=customer.email,
            whatsapp=customer.whatsapp,
        )

        self.session.add(db_customer)

        return customer

    def save_wallet(self, wallet: Wallet) -> Wallet:
        db_wallet = Wallets(
            id=wallet.id,
            savings_percentage=wallet.savings_percentage,
            customer_id=wallet.customer.id,
            external_id=wallet.external_id,
        )

        self.session.add(db_wallet)

        return wallet

    async def commit(self) -> None:
        await self.session.commit()
