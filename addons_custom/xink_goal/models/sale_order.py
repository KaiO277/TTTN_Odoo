from odoo import models, api, fields
from odoo.fields import Date
from datetime import date

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._recompute_sales_targets()
        return records

    def write(self, vals):
        res = super().write(vals)
        self._recompute_sales_targets()
        return res

    def unlink(self):
        targets = self._get_related_sales_targets()
        res = super().unlink()
        targets._compute_achieved_amount()
        return res

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self._recompute_sales_targets()
        return res

    def _recompute_sales_targets(self):
        for order in self:
            targets = order._get_related_sales_targets()
            targets._compute_achieved_amount()

    def _get_related_sales_targets(self):
        domain = []
        if self and self.user_id and self.date_order:
            order_date = Date.to_date(self.date_order) if self.date_order else None
            domain = [
                ('employee_id.user_id', '=', self.user_id.id),
                ('date_start', '<=', order_date),
                ('date_end', '>=', order_date),
            ]
        return self.env['sales.target'].search(domain) if domain else self.env['sales.target'] 