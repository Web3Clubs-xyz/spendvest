from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from domain.entities.payments import Wallet
from domain.entities.users import Customer
from drivers.sqlalchemy.models import CustomerSessions, Customers, Wallets


@dataclass
class SQLAlchemyWalletRepository:
    session: AsyncSession

    async def save_wallet(self, wallet: Wallet) -> Wallet:
        print(f"Repository saving wallet for customer {wallet.customer.id}")
        db_wallet = Wallets(
            id=wallet.id,
            savings_percentage=wallet.savings_percentage,
            customer_id=wallet.customer.id,
            external_id=wallet.external_id,
        )

        self.session.add(db_wallet)
        await self.session.commit()

        return wallet

    async def get_wallet_by_session_id(self, session_id: str) -> Wallet:
        result = await self.session.execute(
            select(CustomerSessions)
            .options(
                selectinload(CustomerSessions.customer).selectinload(Customers.wallets)
            )
            .where(CustomerSessions.id == session_id)
        )
        db_customer_session = result.scalars().one_or_none()

        if db_customer_session is None:
            raise ValueError("WalletRepository Error: Session doesn't exist.")

        if db_customer_session.customer is None:
            raise ValueError(
                "WalletRepository Error: Customer from session doesn't exist."
            )

        db_wallet = db_customer_session.customer.wallets[0]
        db_customer = db_wallet.customer
        customer = Customer(
            id=db_customer.id,
            phone_number=db_customer.phone_number,
            first_name=db_customer.first_name,
            middle_name=db_customer.middle_name,
            last_name=db_customer.last_name,
            email=db_customer.email,
            whatsapp=db_customer.whatsapp,
        )

        return Wallet(
            savings_percentage=db_wallet.savings_percentage,
            customer=customer,
            wallet_id=db_wallet.id,
            external_id=db_wallet.external_id,
        )

    async def get_wallet_by_customer_id(self, customer_id: str) -> Wallet:
        result = await self.session.execute(
            select(Customers)
            .options(selectinload(Customers.wallets))
            .filter(Customers.id == customer_id)
        )
        db_customer = result.scalars().first()

        if db_customer is None:
            raise ValueError("WalletRepository Error: Wallet's Customer doesn't exist")

        wallet = db_customer.wallets[0]

        return Wallet(
            savings_percentage=wallet.savings_percentage,
            customer=Customer(
                id=db_customer.id,
                phone_number=db_customer.phone_number,
                first_name=db_customer.first_name,
                middle_name=db_customer.middle_name,
                last_name=db_customer.last_name,
                email=db_customer.email,
                whatsapp=db_customer.whatsapp,
            ),
            wallet_id=wallet.id,
            external_id=wallet.external_id,
        )

    async def get_wallet_by_id(self, wallet_id: str) -> Wallet:
        result = await self.session.execute(
            select(Wallets)
            .options(selectinload(Wallets.customer))
            .filter(Wallets.id == wallet_id)
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
