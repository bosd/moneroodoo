# -*- coding: utf-8 -*-

from odoo.exceptions import AccessError
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

import logging

_logger = logging.getLogger(__name__)


class account_journal(models.Model):
    _inherit = "account.journal"

    def try_loading_monero(self, company=False, install_demo=True):
        """Installs this chart of accounts for the current company if not chart
        of accounts had been created for it yet.
        :param company (Model<res.company>): the company we try to load the chart template on.
            If not provided, it is retrieved from the context.
        :param install_demo (bool): whether or not we should load demo data right after loading the
            chart template.
        """

        # do not use `request.env` here, it can cause deadlocks
        if not company:
            if request and hasattr(request, "allowed_company_ids"):
                company = self.env["res.company"].browse(request.allowed_company_ids[0])
            else:
                company = self.env.company
        # Try to find an exsisting monero journal
        currency_code, journal = self.env["account.journal"]._find_additional_data(
            currency_code="XMR"
        )
        if journal:
            _logger.debug("found exsisting monero journal with id " + str(journal.id))
            # if no journal is found, create it
        if not journal:
            return self.with_context(default_company_id=company.id)._load_monero(
                company
            )

    def _load_monero(self, company):
        """Setups the monero journal on the current company
        Also, note that this function can only be run by someone with administration
        rights.
        """

        # do not use `request.env` here, it can cause deadlocks
        # Ensure everything is translated to the company's language, not the user's one.
        self = self.with_context(lang=company.partner_id.lang).with_company(company)
        if not self.env.is_admin():
            raise AccessError(_("Only administrators can load a journal"))

        # Create the Monero journal
        self._create_monero_journal(company)
        return {}

    def _create_monero_journal(self, company):
        """
        This function creates the monero journal and their account for each line
        data returned by the function _get_default_bank_journals_data.
        :param company: the company for which the wizard is running.
        """

        m_journals = self.env["account.journal"]
        # Create the journals
        for acc in self._get_default_monero_journal_data():
            m_journals += self.env["account.journal"].create(
                {
                    "name": acc["acc_name"],
                    "type": acc["account_type"],
                    "code": acc["code"],
                    "company_id": company.id,
                    "currency_id": acc.get("currency_id", self.env["res.currency"]).id,
                    "sequence": 10,
                }
            )
        return m_journals

    @api.model
    def _get_default_monero_journal_data(self):
        """Returns the data needed to create the default bank journals when
        installing this chart of accounts, in the form of a list of dictionaries.
        The allowed keys in these dictionaries are:
            - acc_name: string (mandatory)
            - account_type: 'cash' or 'bank' (mandatory)
            - currency_id (optional, only to be specified if != company.currency_id)
        """
        currency = self.env["res.currency"].search([("name", "=", "XMR")], limit=1)
        return [
            {
                "acc_name": _("Monero"),
                "account_type": "cash",
                "currency_id": currency,
                "code": "XMR",
            }
        ]

    def _find_additional_data(self, currency_code):
        """Look for a res.currency and account.journal and make sure it's consistent."""
        company_currency = self.env.company.currency_id
        journal_obj = self.env["account.journal"]
        currency = None

        if currency_code:
            currency = self.env["res.currency"].search(
                [("name", "=ilike", currency_code)], limit=1
            )
            if not currency:
                raise UserError(_("No currency found matching '%s'.") % currency_code)

        journal = journal_obj.browse(self.env.context.get("journal_id", []))
        _logger.info("find additional data found journal object" + str(journal.id))
        if not journal:
            journal = journal_obj.search(
                [
                    (
                        "code",
                        "=",
                        "XMR",
                    )
                ]
            )

        # If importing into an existing journal,
        # its currency must be the same as the monero currency
        if journal:
            journal_currency = journal.currency_id
            if currency is None:
                currency = journal_currency
            if currency and currency != journal_currency:
                statement_cur_code = (
                    not currency and company_currency.name or currency.name
                )
                journal_cur_code = (
                    not journal_currency
                    and company_currency.name
                    or journal_currency.name
                )
                _logger.warning(
                    "The currency of the Monero Journal should be set to (%s) "
                    "but it is not the same as the currently configured currency of the journal (%s)."
                    % (statement_cur_code, journal_cur_code)
                )
                currency = self.env["res.currency"].search(
                    [("name", "=", "XMR")], limit=1
                )
                # Try to update the journal currency
                journal.update({"currency_id": currency.id})

        return currency, journal
