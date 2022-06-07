from . import models
from odoo import api, SUPERUSER_ID
def _account_post_init(cr, registry):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
    # self.try_loading()
        for company in env["res.company"].search([]):
            # company._l10n_nl_set_unece_on_taxes()
            company.env['account.chart.template'].try_loading_monero()
    #env['account.chart.template'].try_loading_monero()
#   _auto_install_l10n(env)
#   _set_fiscal_country(env)
