from collections import namedtuple
from decimal import Decimal

from django.test import TestCase, Client

from .models import Account, Currency, Transaction, Payment

account_balance = namedtuple('account_balance', ('currency', 'balance'))


class BaseTestCase(TestCase):
    test_data = {
        'john': account_balance('USD', Decimal('100.0')),
        'alice': account_balance('EUR', Decimal('200.0')),
        'bob': account_balance('USD', Decimal('50.0')),
        'mark': account_balance('EUR', Decimal('10.0')),
    }

    def insert_test_data(self):
        for acc, (currency, balance) in self.test_data.items():
            ccy, _ = Currency.objects.get_or_create(code=currency)
            Account.objects.create(
                id=acc,
                balance=balance,
                currency=ccy,
            )


class TestCreateTransaction(BaseTestCase):

    def setUp(self) -> None:
        self.client = Client()
        self.insert_test_data()

    def test_normal_transfer(self):
        from_account_id = 'john'
        to_account_id = 'bob'
        amount = Decimal('50.0')
        response = self.client.post('/api/v1/transfer/create/', data={
            'from_account': from_account_id,
            'to_account': to_account_id,
            'amount': amount,
            'currency': 'USD',
        })

        self.assertEqual(response.status_code, 201)
        # check json format
        json_ = response.json()
        self.assertEqual(Decimal(json_.get('amount', '0')), amount)
        self.assertEqual(json_.get('state'), Transaction.STATE_SUCCEED)
        self.assertEqual(json_.get('from_account'), from_account_id)
        self.assertEqual(json_.get('to_account'), to_account_id)

        # check accounts balances
        from_account = Account.objects.get(id=from_account_id)
        self.assertEqual(from_account.balance, self.test_data[from_account_id].balance - amount)

        to_account = Account.objects.get(id=to_account_id)
        self.assertEqual(to_account.balance, self.test_data[to_account_id].balance + amount)

        # check transaction
        tx = Transaction.objects.get(id=json_['id'])
        self.assertEqual(tx.to_account_id, to_account_id)
        self.assertEqual(tx.from_account_id, from_account_id)
        self.assertEqual(tx.amount, amount)
        self.assertEqual(tx.state, Transaction.STATE_SUCCEED)

        # check payments
        payments = Payment.objects.filter(transaction_id=tx.id)
        self.assertEqual(payments.count(), 2)

        for p in payments:
            if p.direction == Payment.OUTGOING:
                self.assertEqual(p.account_id, from_account_id)
                self.assertEqual(p.to_account_id, to_account_id)
                self.assertEqual(p.amount, amount)
                self.assertIsNone(p.from_account_id)
            elif p.direction == Payment.INCOMING:
                self.assertEqual(p.account_id, to_account_id)
                self.assertEqual(p.from_account_id, from_account_id)
                self.assertEqual(p.amount, amount)
                self.assertIsNone(p.to_account_id)
            else:
                raise Exception(f'Unknown payment direction: {p.direction}')
