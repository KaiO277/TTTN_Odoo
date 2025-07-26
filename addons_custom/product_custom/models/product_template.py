from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_invoiceable = fields.Boolean(string='Có xuất hóa đơn', default=False) 