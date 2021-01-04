# -*- coding: utf-8 -*-
import logging

from odoo import fields, models

from monero.transaction import IncomingPayment
from ..models.exceptions import NoTXFound, NumConfirmationsNotMet, MoneroAddressReuse
from ..models.exceptions import MoneroPaymentAcquirerRPCUnauthorized
from ..models.exceptions import MoneroPaymentAcquirerRPCSSLError

_logger = logging.getLogger(__name__)


class MoneroSalesOrder(models.Model):
    _inherit = "sale.order"

    is_payment_recorded = fields.Boolean(
        "Is the Payment Recorded in this ERP",
        help="Cryptocurrency transactions need to be recorded and "
             "associated with this server for order handling.",
        default=False,
    )

    def process_transaction(self, transaction, token, security_level):
        _logger.info('PROCESS ZEROCONF TRANSACTION')
        _logger.info(a for a in dir(self) if not a.startswith('__'))
        try:
            wallet = transaction.acquirer_id.get_wallet()
        except MoneroPaymentAcquirerRPCUnauthorized:
            raise MoneroPaymentAcquirerRPCUnauthorized(
                "Monero Processing Queue: "
                "Monero Payment Acquirer "
                "can't authenticate with RPC "
                "due to user name or password"
            )
        except MoneroPaymentAcquirerRPCSSLError:
            raise MoneroPaymentAcquirerRPCSSLError(
                "Monero Processing Queue: Monero Payment Acquirer "
                "experienced an SSL Error with RPC"
            )
        except Exception as e:
            raise Exception(
                f"Monero Processing Queue: Monero Payment Acquirer "
                f"experienced an Error with RPC: {e.__class__.__name__}"
            )

        if security_level == 0:
            # get transaction in mem_pool
            incoming_payment = wallet.incoming(local_address=token.name, unconfirmed=True, confirmed=True)
        else:
            incoming_payment = wallet.incoming(local_address=token.name)

        if incoming_payment == []:
            # TODO if the job is on it's final retry and there is still no tx found, then cancel order
            raise NoTXFound(
                f"PaymentAcquirer: {transaction.acquirer_id.provider} Subaddress: {token.name} "
                "Status: No transaction found. TX probably hasn't been added to a block or mem-pool yet. "
                "This is fine. "
                f"Another job will execute. Action: Nothing"
            )
        if len(incoming_payment) > 1:
            # TODO custom logic if the end user sends
            #  multiple transactions for one order
            raise MoneroAddressReuse(
                f"PaymentAcquirer: {transaction.acquirer_id.provider} Subaddress: {token.name} "
                "Status: Address reuse found. The end user most likely sent multiple transactions for a single order. "
                "Action: Reconcile transactions manually"
            )

        this_payment: IncomingPayment = incoming_payment.pop()

        _logger.info(f"comparing amount: {this_payment.amount}, {transaction.amount}")

        if transaction.amount == this_payment.amount:
            self.write({"is_payment_recorded": True,
                               "state": "sale"})
            transaction.write({"state": "done"})
            _logger.info(f"Monero payment recorded for sale order: {self.id}, associated with subaddress: {token.name}")


    # An order that is submitted,
    # will have a sale order,
    # an associated invoice,
    # a payment, and a payment token
    # check if the payment has been completed, if so mark the payment as done
    def salesorder_payment_sync(self):
        # retrieve all the cryptocurrency payment acquirers
        # TODO search 'is_enabled' '=' True?
        cryptocurrency_payment_acquirers = self.env["payment.acquirer"].search(
            [("is_cryptocurrency", "=", True)]
        )

        for acquirer in cryptocurrency_payment_acquirers:
            pass
            # TODO
