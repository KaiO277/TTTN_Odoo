from odoo import models, fields

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection([
        ('draft', 'Nháp'),
        ('sent', 'Đã gửi'),
        ('to approve', 'Chờ xác nhận'),
        ('purchase', 'Đã xác nhận'),
        ('done', 'Hoàn tất'),
        ('cancel', 'Đã hủy')
    ], string='Trạng thái', readonly=True, copy=False, tracking=True, default='draft')