from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.onchange('partner_id')
    def _onchange_partner_id_vendor_code(self):
        if self.partner_id and self.partner_id.vendor_code:
            self.partner_ref = self.partner_id.vendor_code
