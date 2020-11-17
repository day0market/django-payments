from collections import OrderedDict

from rest_framework import serializers

from .models import Transaction, Account, Payment

__all__ = ('TransactionSerializer', 'NewTransactionSerializer', 'AccountSerializer', 'PaymentSerializer')


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'


class NewTransactionSerializer(serializers.Serializer):
    from_account = serializers.CharField()
    to_account = serializers.CharField()
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    currency = serializers.CharField()


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    __none_keys_to_skip = {'from_account', 'to_account'}

    class Meta:
        model = Payment
        fields = ('account', 'from_account', 'to_account', 'amount', 'direction')

    def to_representation(self, instance):
        result = super().to_representation(instance)

        return OrderedDict([(key, result[key]) for key in result
                            if result[key] is not None or key not in self.__none_keys_to_skip])
