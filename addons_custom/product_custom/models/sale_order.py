from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_invoiceable_lines(self, final=False):
        # Lấy các dòng hóa đơn gốc
        lines = super()._get_invoiceable_lines(final)
        # Chỉ giữ lại dòng có is_invoiceable
        return lines.filtered(lambda l: getattr(l.product_id.product_tmpl_id, 'is_invoiceable', False))

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            # Lọc các dòng sản phẩm không xuất hóa đơn
            non_invoiceable_lines = order.order_line.filtered(
                lambda l: not getattr(l.product_id.product_tmpl_id, 'is_invoiceable', False)
            )
            if non_invoiceable_lines:
                amount = sum(non_invoiceable_lines.mapped('price_total'))
                if amount > 0:
                    # Tìm journal tiền mặt/ngân hàng đầu tiên
                    journal = self.env['account.journal'].search([
                        ('type', 'in', ['bank', 'cash']),
                        ('company_id', '=', order.company_id.id)
                    ], limit=1)
                    if not journal:
                        continue  # Không tìm thấy journal phù hợp
                    payment = self.env['account.payment'].create([{
                        'payment_type': 'inbound',
                        'partner_type': 'customer',
                        'partner_id': order.partner_id.id,
                        'amount': amount,
                        'journal_id': journal.id,
                        'name': 'Payment for non-invoiceable products in SO %s' % order.name,
                    }])
                    if payment:
                        payment[0].action_post()
        return res 