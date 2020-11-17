from decimal import Decimal

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework import viewsets
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from .exceptions import *
from .filters import PaymentFilter
from .models import Payment, Account, Transaction
from .serializers import PaymentSerializer, AccountSerializer, NewTransactionSerializer, TransactionSerializer

__all__ = ('PaymentsViewSet', 'AccountsViewSet', 'CreateTransactionView')


class PaymentsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentSerializer
    queryset = Payment.objects.all()
    filter_class = PaymentFilter


class AccountsViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AccountSerializer
    queryset = Account.objects.all()


class CreateTransactionView(CreateAPIView):
    serializer_class = NewTransactionSerializer
    model = Transaction

    @swagger_auto_schema(responses={
        201: TransactionSerializer(),
        400: openapi.Schema(
            type=openapi.TYPE_OBJECT, properties={
                "error": openapi.Schema(type=openapi.TYPE_STRING, description="Error description"),
            }
        ),
    })
    def post(self, request, *args, **kwargs) -> Response:
        data = request.data
        serializer = self.serializer_class(data=data)

        if not serializer.is_valid(raise_exception=False):
            return Response(data={'error': 'provided data is not valid'}, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.data
        try:
            amount = Decimal(data['amount'])
        except ValueError:
            return Response(data={'error': 'wrong amount'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            created = self.model.create_new(
                from_account_id=data['from_account'],
                to_account_id=data['to_account'],
                amount=amount,
                currency_code=data['currency'],
            )
        except (AccountNotFoundException, DifferentCurrenciesException,
                InsufficientFundsException, ErrorProcessingException) as e:
            return Response(data={'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data=TransactionSerializer(instance=created).data, status=status.HTTP_201_CREATED)
