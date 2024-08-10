from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import override
from domain.entities.interfaces.payments_interfaces import IWalletRepository
from domain.entities.payments import IWallet, WalletFactory, WalletType
from domain.entities.users import Customer
from drivers.sqlalchemy.models import Customers, SasapayWallets, Wallets


class IWalletCreationStrategy(ABC):
    @abstractmethod
    async def create(self, session: AsyncSession, customer: Customer) -> IWallet:
        pass


class SasapayWalletCreationStrategy(IWalletCreationStrategy):
    _wallet_id: str
    _savings_percentage: int
    _type_id: int
    _customer_id: str
    _external_id: str
    _wallet_id: str
    _mobile_number: int
    _mobile_country_code: int
    _document_type: str
    _document_number: str

    def __init__(
        self,
        savings_percentage: int,
        type_id: int,
        customer_id: str,
        external_id: str,
        wallet_id: str,
        mobile_number: int,
        mobile_country_code: int,
        document_type: str,
        document_number: str,
    ) -> None:
        self._wallet_id = str(uuid4().hex)
        self._savings_percentage = savings_percentage
        self._type_id = type_id
        self._customer_id = customer_id
        self._external_id = external_id
        self._wallet_id = wallet_id
        self._mobile_number = mobile_number
        self._mobile_country_code = mobile_country_code
        self._document_type = document_type
        self._document_number = document_number

    @override
    async def create(self, session: AsyncSession, customer: Customer) -> IWallet:
        db_wallet = Wallets(
            id=self._wallet_id,
            savings_percentage=self._savings_percentage,
            type_id=self._type_id,
            customer_id=self._customer_id,
        )
        db_sasapay_wallet = SasapayWallets(
            external_id=self._external_id,
            wallet_id=self._wallet_id,
            mobile_number=self._mobile_number,
            mobile_country_code=self._mobile_country_code,
            document_type=self._document_type,
            document_number=self._document_number,
        )
        db_sasapay_wallet.wallet = db_wallet

        session.add(db_sasapay_wallet)
        await session.commit()

        wallet_type = WalletType(id=1, name="SASAPAY")
        wallet = WalletFactory().create_wallet(
            savings_percentage=db_wallet.savings_percentage,
            customer=customer,
            wallet_id=db_wallet.id,
            wallet_type=wallet_type,
            external_id=db_sasapay_wallet.external_id,
        )

        return wallet


@dataclass
class SQLAlchemyWalletRepository(IWalletRepository):
    _session: AsyncSession = field(init=False)

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def save_wallet(self, wallet: IWallet) -> IWallet:
        return await super().save_wallet(wallet)
