from odoo import models, api, _
from odoo.exceptions import UserError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model
    def create(self, vals):
        user = self.env.user
        if 'price_unit' in vals and not user.has_group('sales_team.group_sale_manager'):
            raise UserError(_('Bạn không có quyền chỉnh sửa đơn giá.'))
        return super().create(vals)

    def write(self, vals):
        user = self.env.user
        if 'price_unit' in vals and not user.has_group('sales_team.group_sale_manager'):
            raise UserError(_('Bạn không có quyền chỉnh sửa đơn giá.'))
        return super().write(vals)
