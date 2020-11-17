from rest_framework.exceptions import APIException

__all__ = ('AccountNotFoundException', 'DifferentCurrenciesException',
           'InsufficientFundsException', 'ErrorProcessingException')


class AccountNotFoundException(APIException):
    status_code = 404
    default_detail = 'Account not found'
    default_code = 'not_found'


class DifferentCurrenciesException(APIException):
    status_code = 417
    default_detail = 'Different currencies are not supported'
    default_code = 'expectations_failed'


class InsufficientFundsException(APIException):
    status_code = 400
    default_detail = 'Insufficient funds'
    default_code = 'bad_request'


class ErrorProcessingException(APIException):
    status_code = 500
    default_detail = 'Unknown error'
    default_code = 'internal_server_error'
