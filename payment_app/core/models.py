import logging
from decimal import Decimal
from typing import TypeVar, Type, Optional, Union, List

from django.db import models, transaction
from django.db.models import F
from django.db.models import QuerySet

from .exceptions import *

TransactionType = TypeVar('TransactionType', bound='Transaction')
AccountType = TypeVar('AccountType', bound='Account')
PaymentType = TypeVar('PaymentType', bound='Payment')


class Currency(models.Model):
    code = models.CharField(max_length=3, primary_key=True)
    description = models.TextField(null=True)


class Account(models.Model):
    id = models.TextField(primary_key=True)
    balance = models.DecimalField(default=0, max_digits=15, decimal_places=2)
    currency = models.ForeignKey('Currency', on_delete=models.PROTECT)

    def __str__(self) -> str:
        return self.id

    @classmethod
    def get_or_raise(cls: Type[AccountType], account_id: str) -> Optional[AccountType]:
        try:
            return Account.objects.prefetch_related().get(id=account_id)
        except Account.DoesNotExist:
            raise AccountNotFoundException(f'{account_id} not found')

    @property
    def incoming_payments(self) -> Union[QuerySet, List['Transaction']]:
        return Transaction.objects.filter(state=Transaction.STATE_SUCCEED, to_account=self)

    @property
    def outgoing_payments(self) -> Union[QuerySet, List['Transaction']]:
        return Transaction.objects.filter(from_account=self)

    def can_use_currency(self, currency_code: str) -> bool:
        return self.currency_id == currency_code


class Transaction(models.Model):
    STATE_SUCCEED = 'succeed'
    STATE_FAILED = 'failed'

    id = models.BigAutoField(primary_key=True)

    from_account = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='from_account')
    to_account = models.ForeignKey('Account', on_delete=models.CASCADE, related_name='to_account')

    amount = models.DecimalField(max_digits=15, decimal_places=2)
    message = models.TextField(null=True, blank=True)
    state = models.CharField(max_length=8, choices=((STATE_FAILED, STATE_FAILED), (STATE_SUCCEED, STATE_SUCCEED)))

    def __str__(self):
        return f'{self.amount} ({self.account.currency}) from {self.account} to {self.to_account}'

    @classmethod
    def create_new(cls: Type[TransactionType], *, from_account_id: str, to_account_id: str,
                   amount: Decimal, currency_code: str) -> Optional[TransactionType]:
        from_account = Account.get_or_raise(from_account_id)
        to_account = Account.get_or_raise(to_account_id)

        if not from_account.can_use_currency(currency_code):
            raise DifferentCurrenciesException(
                f'Withdrawal account {from_account_id} has currency different from payment currency')

        if not to_account.can_use_currency(currency_code):
            raise DifferentCurrenciesException(
                f'Target account {from_account_id} has currency different from payment currency')

        if from_account.balance < amount:
            raise InsufficientFundsException(f'{from_account_id} has insufficient funds')

        try:
            with transaction.atomic():
                from_account = Account.objects.select_for_update().filter(id=from_account_id).last()
                to_account = Account.get_or_raise(to_account_id)
                if from_account.balance < amount:
                    cls.objects.create(
                        from_account=from_account,
                        to_account=to_account,
                        amount=amount,
                        message='insufficient funds',
                        state=cls.STATE_FAILED,
                    )
                    raise InsufficientFundsException(f'{from_account_id} has insufficient funds')

                from_account.balance = F('balance') - amount
                from_account.save()
                to_account.balance = F('balance') + amount
                to_account.save()

                tx = cls.objects.create(
                    from_account=from_account,
                    to_account=to_account,
                    amount=amount,
                    message=None,
                    state=cls.STATE_SUCCEED,
                )
                Payment.new_incoming_from_transaction(tx)
                Payment.new_outgoing_from_transaction(tx)
                return tx
        except Exception as e:
            logging.exception(f'Failed to process transaction from {from_account_id} to {to_account_id}: {e}')
            raise ErrorProcessingException('Unknown exception')


class Payment(models.Model):
    INCOMING = 'incoming'
    OUTGOING = 'outgoing'

    transaction = models.ForeignKey('Transaction', on_delete=models.CASCADE)
    direction = models.CharField(max_length=10, choices=((INCOMING, INCOMING), (OUTGOING, OUTGOING)))
    account = models.ForeignKey('Account', on_delete=models.PROTECT, related_name='account')
    from_account = models.ForeignKey('Account', on_delete=models.PROTECT, null=True, related_name='from_account+')
    to_account = models.ForeignKey('Account', on_delete=models.PROTECT, null=True, related_name='to_account+')
    amount = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self) -> str:
        if self.direction == self.INCOMING:
            return f'{self.account} {self.direction} {self.account} from {self.from_account}'
        return f'{self.account} {self.direction} {self.account} to {self.to_account}'

    def save(self, **kwargs):
        # sanity check for field correctness
        if self.direction == self.INCOMING and not self.from_account:
            raise Exception(f'`from_account` is missed for {self.direction}')
        if self.direction == self.OUTGOING and not self.to_account:
            raise Exception(f'`to_account` is missed for {self.direction}')

        super().save(**kwargs)

    @classmethod
    def new_incoming_from_transaction(cls: Type[PaymentType], tx: Transaction) -> PaymentType:
        return cls.objects.create(
            transaction=tx,
            direction=cls.INCOMING,
            account=tx.to_account,
            from_account=tx.from_account,
            to_account=None,
            amount=tx.amount,
        )

    @classmethod
    def new_outgoing_from_transaction(cls: Type[PaymentType], tx: Transaction) -> PaymentType:
        return cls.objects.create(
            transaction=tx,
            direction=cls.OUTGOING,
            account=tx.from_account,
            to_account=tx.to_account,
            from_account=None,
            amount=tx.amount,
        )
