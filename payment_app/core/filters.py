import django_filters

from .models import Payment


class PaymentFilter(django_filters.FilterSet):
    class Meta:
        model = Payment
        fields = ('from_account', 'to_account', 'direction')
