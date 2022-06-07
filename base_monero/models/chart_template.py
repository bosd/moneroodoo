

# from account_journal
# I want to call the create function
#########
"""
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._fill_missing_values(vals)

        journals = super(AccountJournal, self.with_context(mail_create_nolog=True)).create(vals_list)

        for journal, vals in zip(journals, vals_list):
            # Create the bank_account_id if necessary
            if journal.type == 'bank' and not journal.bank_account_id and vals.get('bank_acc_number'):
                journal.set_bank_account(vals.get('bank_acc_number'), vals.get('bank_id'))

        return journals
"""
##

## gets called from
###############################
## chart_template.py

# -*- coding: utf-8 -*-

from odoo.exceptions import AccessError
from odoo import api, fields, models, _
from odoo import SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from odoo.http import request
# from odoo.addons.account.models.account_tax import TYPE_TAX_USE

import logging

_logger = logging.getLogger(__name__)


class AccountChartTemplate(models.Model):
    _name = "account.chart.template"
    _description = "Account Chart Template"
# above is a plain copy
# needs adjusting

    def try_loading_monero(self, company=False, install_demo=True):
        """ Installs this chart of accounts for the current company if not chart
        of accounts had been created for it yet.
        :param company (Model<res.company>): the company we try to load the chart template on.
            If not provided, it is retrieved from the context.
        :param install_demo (bool): whether or not we should load demo data right after loading the
            chart template.
        """
        # do not use `request.env` here, it can cause deadlocks
        if not company:
            if request and hasattr(request, 'allowed_company_ids'):
                company = self.env['res.company'].browse(request.allowed_company_ids[0])
            else:
                company = self.env.company
        _logger.warning('Try loading called!!!!!')
        # self._load(company)
        # If we don't have any chart of account on this company, install this chart of account
        # B if not company.chart_template_id and not self.existing_accounting(company):
        _logger.warning('Self is!!!!! %s', self)
        for rec in self:
            _logger.warning('Try Template is!!!!! %s', template)
            template._create_bank_journals(company)
            # template.with_context(default_company_id=company.id)._load2(company)
            # Install the demo data when the first localization is instanciated on the company
            # B if install_demo and self.env.ref('base.module_account').demo:
                # B self.with_context(
                    # B default_company_id=company.id,
                    # B allowed_company_ids=[company.id],
                # B )._create_demo_data()
    # demodataa todo

    def _create_demo_data(self):

        try:
            with self.env.cr.savepoint():
                demo_data = self._get_demo_data()
                for model, data in demo_data:
                    created = self.env[model]._load_records([{
                        'xml_id': "account.%s" % xml_id if '.' not in xml_id else xml_id,
                        'values': record,
                        'noupdate': True,
                    } for xml_id, record in data.items()])
                    self._post_create_demo_data(created)
        except Exception:
            # Do not rollback installation of CoA if demo data failed
            _logger.exception('Error while loading accounting demo data')

    def _load2(self, company):
        """ Installs this chart of accounts on the current company, replacing
        the existing one if it had already one defined. If some accounting entries
        had already been made, this function fails instead, triggering a UserError.
        Also, note that this function can only be run by someone with administration
        rights.
        """
        self.ensure_one()
        _logger.warning('_load called!!!!!')
        # do not use `request.env` here, it can cause deadlocks
        # Ensure everything is translated to the company's language, not the user's one.
        self = self.with_context(lang=company.partner_id.lang).with_company(company)
        if not self.env.is_admin():
            raise AccessError(_("Only administrators can load a chart of accounts"))

        # Install all the templates objects and generate the real objects
        # acc_template_ref, taxes_ref = self._install_template(company, code_digits=self.code_digits)

        # Create Bank journals
        self._create_bank_journals(company)  # , acc_template_ref

        return {}

    def _create_bank_journals(self, company): # , acc_template_ref
        '''
        This function creates bank journals and their account for each line
        data returned by the function _get_default_bank_journals_data.
        :param company: the company for which the wizard is running.
        :param acc_template_ref: the dictionary containing the mapping between the ids of account templates and the ids
            of the accounts that have been generated from them.
        '''
        _logger.warning('_create_bank_journals called!!!!!')
        self.ensure_one()
        bank_journals = self.env['account.journal']
        # Create the journals that will trigger the account.account creation
        for acc in self._get_default_bank_journals_data():
            bank_journals += self.env['account.journal'].create({
                'name': acc['acc_name'],
                'type': acc['account_type'],
                'company_id': company.id,
                'currency_id': acc.get('currency_id', self.env['res.currency']).id,
                'sequence': 10,
            })

        return

    @api.model
    def _get_default_bank_journals_data(self):
        """ Returns the data needed to create the default bank journals when
        installing this chart of accounts, in the form of a list of dictionaries.
        The allowed keys in these dictionaries are:
            - acc_name: string (mandatory)
            - account_type: 'cash' or 'bank' (mandatory)
            - currency_id (optional, only to be specified if != company.currency_id)
        """
        return [{'acc_name': _('Monero'), 'account_type': 'cash'}]
# add 'currency_id': 'xmr'
# for now it is correct and can be called.
