from . import models
from odoo import api, SUPERUSER_ID
def _monero_journal_post_init(cr, registry):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        for company in env["res.company"].search([]):
            chart_template = company.chart_template_id
            company.env['account.journal'].sudo().try_loading_monero()
