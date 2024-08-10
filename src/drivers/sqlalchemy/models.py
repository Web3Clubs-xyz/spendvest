from typing import List
from typing_extensions import Optional
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AccountTypes(Base):
    """
    User types metadata table.

    Attributes:
        `id (int)`: Unique identifier for a user type
        `name (str)`: Name of the user type
    """

    __tablename__ = "account_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256))

    user_accounts: Mapped[List["UserAccounts"]] = relationship(
        "UserAccounts", back_populates="account_type"
    )


class Users(Base):
    """
    Users' metadata table.

    Attributes:
        `id (str)`: Unique identifier for a user
        `first_name (str)`: The user's first name as it appears on their ID
        `middle_name (str)`: The user's middle name as it appears on their ID
        `last_name (str)`: The user's last name as it appears on their ID
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(256))
    middle_name: Mapped[str] = mapped_column(String(256))
    last_name: Mapped[str] = mapped_column(String(256))

    accounts: Mapped[List["UserAccounts"]] = relationship(
        "UserAccounts", back_populates="user"
    )
    sessions: Mapped[List["UserSessions"]] = relationship(
        "UserSessions", back_populates="user"
    )


class UserAccounts(Base):
    """
    Accounts' metadata table for different accounts

    Attributes:
        `id (str)`: Unique identifier of a user account
        `user_id (str)`: ID of the owner of the user account
        `type_id (int)`: ID of the type of user account
        `user (Users)`: User relationship
    """

    __tablename__ = "user_accounts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    type_id: Mapped[int] = mapped_column(String, ForeignKey(""))

    user: Mapped["Users"] = relationship("Users", back_populates="accounts")
    account_type: Mapped["AccountTypes"] = relationship(
        "AccountTypes", back_populates="user_accounts"
    )


class SessionTypes(Base):
    """
    Session Types' metadata table.

    Attributes:
        `id (int)`: Unique identifier for the session type
        `name (str)`: Name of the session type
    """

    __tablename__ = "session_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)

    user_session: Mapped["UserSessions"] = relationship(
        "SessionTypes", back_populates="session_type"
    )


class UserSessions(Base):
    """
    Users' sessions metadata table.

    Attributes:
        `id (str)`: Unique identifier for a session
        `current_step (int)`: The current step in the session the user is in
        `type_id (int)`: Foreign key identifying the session's type
        `user_id (str)`: ID of the owner of the session
        `session_type (Sessiontypes)`: Type of session.
        `user (Users)`: The owner of the session.
    """

    __tablename__ = "user_sessions"

    id: Mapped[str] = mapped_column(primary_key=True)
    current_step: Mapped[int] = mapped_column(Integer)
    external_id: Mapped[str] = mapped_column(String, unique=True)
    type_id: Mapped[int] = mapped_column(Integer, ForeignKey("session_types.id"))
    user_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("users.id"), nullable=True
    )

    session_type: Mapped["SessionTypes"] = relationship(
        "SessionType", back_populates="user_session"
    )
    user: Mapped[Optional["Users"]] = relationship("Users", back_populates="sessions")


class Customers(Base):
    """
    Customers' metadata table.

    Attributes:
        `account_id (str)`: ID used to uniquely identify a customer account
        `phone_number (int)`: Phone number linked to a customer
        `wallets (Wallets)`: The customer's wallets
        `customer_sessions (CustomerSessions)`: The customer's sessions
        `user_account (UserAccounts)`: The customer's user account
    """

    __tablename__ = "customers"

    account_id: Mapped[str] = mapped_column(
        String, ForeignKey("user_accounts.id"), primary_key=True
    )
    phone_number: Mapped[int] = mapped_column(Integer)

    wallets: Mapped[List["Wallets"]] = relationship(
        "Wallets", back_populates="customer"
    )
    customer_sessions: Mapped[List["UserSessions"]] = relationship(
        "CustomerSessions", back_populates="customer"
    )
    user_account: Mapped["UserAccounts"] = relationship("UserAccounts")


class WhatsappAccounts(Base):
    """
    Whatsapp accounts metadata table.

    Attributes:
        `whatsapp_id (str)`: Unique identifier for a user's whatsapp account.
        `account_id (str)`: Unique identifier for a whatsapp account.
        `user_account (UserAccounts)`: The whatsapp user's account.
    """

    __tablename__ = "whatsapp_accounts"

    whatsapp_id: Mapped[str] = mapped_column(String, primary_key=True)
    account_id: Mapped[str] = mapped_column(String, ForeignKey("user_accounts.id"))

    user_account: Mapped["UserAccounts"] = relationship("UserAccounts")


class WalletTypes(Base):
    """
    Metadata table for wallet types

    Attributes:
        `id (int)`: Unique identifier for wallet types
        `name (str)`: Name of wallet type
    """

    __tablename__ = "wallet_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256))

    wallets: Mapped[List["Wallets"]] = relationship(
        "Wallets", back_populates="wallet_type"
    )


class Wallets(Base):
    """
    Metadata for `Users` `Wallets` on the system

    Attributes:
        `id (str)`: ID used to uniquely identify a wallet
        `savings_percentage (int)`: Percentage the user wants to save on each
            transacton
        `type_id (int)`: ID defining the type of wallet
        `customer_id (str)`: ID used to identify the owner of the wallet
        `customer (Customers)`: Instance of the wallet owner
        `wallet_type (WalletTypes)`: Instance of the wallet type
    """

    __tablename__ = "wallets"

    id: Mapped[str] = mapped_column(primary_key=True)
    savings_percentage: Mapped[int] = mapped_column(Integer)
    type_id: Mapped[int] = mapped_column(Integer, ForeignKey("wallet_types.id"))
    customer_id: Mapped[str] = mapped_column(String, ForeignKey("customers.account_id"))

    customer: Mapped["Customers"] = relationship("Customers", back_populates="wallets")
    wallet_type: Mapped["WalletTypes"] = relationship(
        "WalletTypes", back_populates="wallets"
    )


class SasapayWallets(Base):
    """
    Metadata table for sasapay wallets.

    Attributes:
        `external_id (str)`: Unique identifier for a sasapay wallet
        `wallet_id (str)`: Unique identifier for a customer's wallet
        `mobile_number (int)`: Customer's mobile number
        `mobile_country_code (int)`: Country code used to identify the phone
            number's country
        `document_type (str)`: The document type used to verify the user's identity
        `document_number (str)`: Number on the document type that uniquely
            identifies a customer in the real world
    """

    __tablename__ = "sasapay_wallets"

    external_id: Mapped[str] = mapped_column(String(256), primary_key=True)
    wallet_id: Mapped[str] = mapped_column(String(256), ForeignKey("wallets.id"))
    mobile_number: Mapped[int] = mapped_column(Integer)
    mobile_country_code: Mapped[int] = mapped_column(Integer)
    document_type: Mapped[str] = mapped_column(String(256))
    document_number: Mapped[str] = mapped_column(String(256))

    wallet: Mapped["Wallets"] = relationship("Wallets")


class Transactions(Base):
    """
    Metadata for all transactions in the system

    Attributes:
        `id (str)`: ID that uniquely identifies transactions in the system
        `credited_wallet (str)`: ID for the wallet that is being credited
        `debited_wallet (str)`: ID for the wallet that is being debited
        `transaction_amount (int)`: An integer representation of the
            transaction amount in cents
    """

    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(primary_key=True)
    transaction_amount: Mapped[int] = mapped_column(Integer)
    credited_wallet: Mapped[str] = mapped_column(String, ForeignKey("wallets.id"))
    debited_wallet: Mapped[str] = mapped_column(ForeignKey("wallets.id"))
