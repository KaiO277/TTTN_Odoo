from odoo import models, fields

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_invoiceable = fields.Boolean(
        string="Có xuất hóa đơn",
        related='product_id.product_tmpl_id.is_invoiceable',
        store=True,
        readonly=True,
    )