from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from domain.entities.payments import Wallet
from domain.entities.users import Customer
from drivers.sqlalchemy.models import Customers, Wallets


@dataclass
class SQLAlchemyWalletRepository:
    session: AsyncSession

    async def save_wallet(self, wallet: Wallet) -> Wallet:
        db_wallet = Wallets(
            id=wallet.id,
            saving_percentage=wallet.savings_percentage,
            customer_id=wallet.customer.id,
        )

        self.session.add(db_wallet)
        await self.session.commit()

        return wallet

    async def get_wallet_by_customer_id(self, customer_id: str) -> Wallet:
        result = await self.session.execute(
            select(Customers).filter(Customers.id == customer_id)
        )
        db_customer = result.scalars().first()

        if db_customer is None:
            raise ValueError("Customer doesn't exist")

        wallet = db_customer.wallets[0]

        return Wallet(
            savings_percentage=wallet.savings_percentage,
            customer=Customer(
                id=wallet.customer.id,
                phone_number=wallet.customer.phone_number,
                first_name=wallet.customer.first_name,
                middle_name=wallet.customer.middle_name,
                last_name=wallet.customer.last_name,
                email=wallet.customer.email,
                whatsapp=wallet.customer.whatsapp,
            ),
            wallet_id=wallet.id,
            external_id=wallet.external_id,
        )

    async def get_wallet_by_id(self, wallet_id: str) -> Wallet:
        result = await self.session.execute(
            select(Wallets).filter(Wallets.id == wallet_id)
        )
        db_wallet = result.scalars().first()

        if db_wallet is None:
            raise ValueError("Wallet doesn't exist")

        return Wallet(
            savings_percentage=db_wallet.savings_percentage,
            customer=Customer(
                id=db_wallet.customer.id,
                phone_number=db_wallet.customer.phone_number,
                first_name=db_wallet.customer.first_name,
                middle_name=db_wallet.customer.middle_name,
                last_name=db_wallet.customer.last_name,
                email=db_wallet.customer.email,
                whatsapp=db_wallet.customer.whatsapp,
            ),
            wallet_id=db_wallet.id,
            external_id=db_wallet.external_id,
        )
