# -*- coding: utf-8 -*-
from typing import Union


class BillingError(Exception):
    def __init__(self, msg: Union[str, dict], *args):
        super().__init__(*args)
        self.msg = msg

    def errors(self):
        return self.msg


class SenderNotEnoughMoneyError(BillingError):
    pass


class SenderNotExistError(BillingError):
    pass


class RecipientNotExistError(BillingError):
    pass
