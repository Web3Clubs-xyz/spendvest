from abc import ABC, abstractmethod

from domain.usecases.interfaces.context_manager import UIContext


class WithdrawOutput:
    pass


class WithdrawInput:
    pass


class IWithdraw(ABC):
    """
    Abstract interface to be implemented by withdraw use cases
    """

    @abstractmethod
    async def withdraw(
        self,
        input: WithdrawInput,
        context: UIContext,
        # withdraw_strategy: IWithdrawStrategy,  # Implement withdraw strategy
        # so we can withdraw from different wallets
    ):
        pass
