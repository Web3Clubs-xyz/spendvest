from typing import List
from typing_extensions import Optional
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class SessionTypes(Base):
    """
    Session Types' metadata table.

    Attributes:
        id (`int`): Unique identifier for the session type
        name (`str`): Name of the session type
    """

    __tablename__ = "session_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)

    user_session: Mapped["CustomerSessions"] = relationship(
        "SessionTypes", back_populates="session_type"
    )


class CustomerSessions(Base):
    """
    Users' sessions metadata table.

    Attributes:
        id (`str`): Unique identifier for a session
        current_step (`int`): The current step in the session the user is in
        type_id (`int`): Foreign key identifying the session's type
        customer_id (`str`): ID of the owner of the session
        session_type (`Sessiontypes`): Type of session.
        customer (`Customers`): The owner of the session.
    """

    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(primary_key=True)
    current_step: Mapped[int] = mapped_column(Integer)
    type_id: Mapped[int] = mapped_column(Integer, ForeignKey("session_types.id"))
    customer_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("customers.id"), nullable=True
    )

    session_type: Mapped["SessionTypes"] = relationship(
        "SessionType", back_populates="user_session"
    )
    customer: Mapped[Optional["Customers"]] = relationship(
        "Customers", back_populates="customer_sessions"
    )


class Customers(Base):
    """
    Customers' metadata table.

    Attributes:
        id (`str`): ID used to uniquely identify a customer account
        first_name (`str`): The user's first name as it appears on their ID
        middle_name (`str`): The user's middle name as it appears on their ID
        last_name (`str`): The user's last name as it appears on their ID
        phone_number (`int`): Phone number linked to a customer
        wallets (`Wallets`): The customer's wallets
        customer_sessions (`CustomerSessions`): The customer's sessions
        user_account (`UserAccounts`): The customer's user account
    """

    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(256))
    middle_name: Mapped[str] = mapped_column(String(256))
    last_name: Mapped[str] = mapped_column(String(256))
    phone_number: Mapped[int] = mapped_column(Integer)
    email: Mapped[str] = mapped_column(String)
    whatsapp: Mapped[str] = mapped_column(String)
    identifying_document: Mapped[str] = mapped_column(String)
    document_number: Mapped[str] = mapped_column(String)

    wallets: Mapped[List["Wallets"]] = relationship(
        "Wallets", back_populates="customer"
    )
    customer_sessions: Mapped[List["CustomerSessions"]] = relationship(
        "CustomerSessions", back_populates="customer"
    )


class Wallets(Base):
    """
    Metadata for `Users` `Wallets` on the system

    Attributes:
        id (`str`): ID used to uniquely identify a wallet
        savings_percentage (`int`): Percentage the user wants to save on each
            transacton
        customer_id (`str`): ID used to identify the owner of the wallet
        customer (`Customers`): Instance of the wallet owner
        wallet_type (`WalletTypes`): Instance of the wallet type
    """

    __tablename__ = "wallets"

    id: Mapped[str] = mapped_column(primary_key=True)
    savings_percentage: Mapped[int] = mapped_column(Integer)
    customer_id: Mapped[str] = mapped_column(String, ForeignKey("customers.account_id"))
    external_id: Mapped[str] = mapped_column(String)

    customer: Mapped["Customers"] = relationship("Customers", back_populates="wallets")


class Transactions(Base):
    """
    Metadata for all transactions in the system. These are only the
    transactions that take place when a user sends money.

    Attributes:
        id (`str`): ID that uniquely identifies transactions in the system
        transaction_amount (`int`): An integer representation of the
            transaction amount in cents
        wallet_id (`str`): ID for the wallet that is involved in the transaction.
        debited (`str`): Flag identifying whether the wallet is being debited
            or credited
        phone_number (`int`): Phone number involved in the transaction.
    """

    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(primary_key=True)
    transaction_amount: Mapped[int] = mapped_column(Integer)
    wallet_id: Mapped[str] = mapped_column(String, ForeignKey("wallets.id"))
    phone_number: Mapped[int] = mapped_column(Integer)
