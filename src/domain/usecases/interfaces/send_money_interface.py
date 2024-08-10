from abc import abstractmethod
from dataclasses import dataclass, field

from domain.entities.services.send_money_service import ISendMoneyService
from domain.entities.services.wallet_service import IWalletService


@dataclass
class SendMoneyInput:
    _customer_id: str = field(init=False)
    _recepient_phone_number: int = field(init=False)
    _transaction_amount: int = field(init=False)

    def __init__(
        self, customer_id: str, recepient_phone_number: int, transaction_amount: int
    ) -> None:
        self._customer_id = customer_id
        self._recepient_phone_number = recepient_phone_number
        self._transaction_amount = transaction_amount

    @property
    def customer_id(self) -> str:
        return self._customer_id

    @customer_id.setter
    def customer_id(self, customer_id: str) -> None:
        self._customer_id = customer_id

    @property
    def recepient_phone_number(self) -> int:
        return self._recepient_phone_number

    @recepient_phone_number.setter
    def recepient_phone_number(self, recepient_phone_number: int) -> None:
        self._recepient_phone_number = recepient_phone_number

    @property
    def transaction_amount(self) -> int:
        return self._transaction_amount

    @transaction_amount.setter
    def transaction_amount(self, transaction_amount: int) -> None:
        self._transaction_amount = transaction_amount


@dataclass
class SendMoneyOutput:
    _transaction_amount: int = field(init=False)
    _recepient_phone_number: int = field(init=False)
    _saved_amount: int = field(init=False)
    _transaction_status: int = field(init=False)

    def __init__(
        self,
        transaction_amount: int,
        recepient_phone_number: int,
        saved_amount: int,
        transaction_status: bool,
    ) -> None:
        self._transaction_amount = transaction_amount
        self._recepient_phone_number = recepient_phone_number
        self._saved_amount = saved_amount
        self._transaction_status = transaction_status

    @property
    def transaction_amount(self) -> int:
        return self._transaction_amount

    @transaction_amount.setter
    def transaction_amount(self, transaction_amount: int) -> None:
        self._transaction_amount = transaction_amount

    @property
    def recepient_phone_number(self) -> int:
        return self._recepient_phone_number

    @recepient_phone_number.setter
    def recepient_phone_number(self, recepient_phone_number: int) -> None:
        self._recepient_phone_number = recepient_phone_number

    @property
    def saved_amount(self) -> int:
        return self._saved_amount

    @saved_amount.setter
    def saved_amount(self, saved_amount: int) -> None:
        self._saved_amount = saved_amount

    @property
    def transaction_status(self) -> int:
        return self._transaction_status

    @transaction_status.setter
    def transaction_status(self, transaction_status: bool) -> None:
        self._transaction_status = transaction_status


class ISendMoney:
    """
    Abstract class that should be overriden by concrete implementations of
    usecases that facilitate the 'Send Money' functionality.
    """

    @abstractmethod
    def send_money(
        self,
        input: SendMoneyInput,
        send_money_service: ISendMoneyService,  # Replace this with a strategy
        # so we can send money through different payment gateways
        wallet_service: IWalletService,
    ) -> SendMoneyOutput:
        """
        Abstract method that should be overriden to enable a customer to save
        money while spending

        Args:
            input (SendMoneyInput): Input containing the transaction
                information

        Returns:
            SendMoneyOutput: Output that contains information about the
                transaction
        """

        pass
