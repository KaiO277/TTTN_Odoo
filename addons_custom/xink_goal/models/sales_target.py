from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, timedelta

class SalesTarget(models.Model):
    _name = 'sales.target'
    _description = 'Sales Target'
    _order = 'date_start desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Mã mục tiêu', required=True, default='New', copy=False, readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True, tracking=True)
    target_amount = fields.Float('Mục tiêu doanh số (VNĐ)', required=True, tracking=True)
    assign_type = fields.Selection(selection=[
        ('custom', 'Tùy chỉnh'),
        ('this_month', 'Tháng này'),
        ('this_quarter', 'Quý này'),
        ('this_year', 'Năm này'),
    ], string='Giao theo', required=True, default='custom', tracking=True)
    date_start = fields.Date('Từ ngày', required=True, tracking=True)
    date_end = fields.Date('Đến ngày', required=True, tracking=True)
    achieved_amount = fields.Float('Thực đạt (VNĐ)', compute='_compute_achieved_amount', store=True, readonly=True)
    progress = fields.Float('Tiến độ (%)', compute='_compute_progress', store=True, readonly=True)
    state = fields.Selection(selection=[
        ('in_progress', 'Đang diễn ra'),
        ('done', 'Đã kết thúc'),
    ], string='Trạng thái', default='in_progress', tracking=True, compute='_compute_state', store=True)
    note = fields.Text('Ghi chú')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('sales.target') or 'MTD/%s/0001' % fields.Date.today().year
        return super(SalesTarget, self).create(vals_list)

    @api.onchange('assign_type')
    def _onchange_assign_type(self):
        today = fields.Date.context_today(self)
        if self.assign_type == 'this_month':
            self.date_start = date(today.year, today.month, 1)
            if today.month == 12:
                self.date_end = date(today.year, 12, 31)
            else:
                self.date_end = date(today.year, today.month + 1, 1) - timedelta(days=1)
        elif self.assign_type == 'this_quarter':
            q = (today.month - 1) // 3 + 1
            self.date_start = date(today.year, 3 * q - 2, 1)
            if q == 4:
                self.date_end = date(today.year, 12, 31)
            else:
                self.date_end = date(today.year, 3 * q + 1, 1) - timedelta(days=1)
        elif self.assign_type == 'this_year':
            self.date_start = date(today.year, 1, 1)
            self.date_end = date(today.year, 12, 31)
        # Tùy chỉnh thì không set gì

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_end and rec.date_start and rec.date_end < rec.date_start:
                raise ValidationError('Ngày kết thúc phải lớn hơn hoặc bằng ngày bắt đầu!')

    @api.depends('employee_id', 'date_start', 'date_end')
    def _compute_achieved_amount(self):
        from odoo.fields import Date
        for rec in self:
            rec.achieved_amount = 0.0
            if rec.employee_id and rec.employee_id.user_id and rec.date_start and rec.date_end:
                orders = self.env['sale.order'].search([
                    ('user_id', '=', rec.employee_id.user_id.id),
                    ('state', '=', 'sale'),
                ])
                total = 0.0
                for order in orders:
                    order_date = Date.to_date(order.date_order) if order.date_order else None
                    if order_date and rec.date_start <= order_date <= rec.date_end:
                        total += order.amount_total or 0.0
                rec.achieved_amount = total

    @api.depends('achieved_amount', 'target_amount')
    def _compute_progress(self):
        for rec in self:
            if rec.target_amount > 0:
                rec.progress = min(100.0, rec.achieved_amount / rec.target_amount * 100)
            else:
                rec.progress = 0.0

    @api.depends('progress', 'date_end')
    def _compute_state(self):
        today = fields.Date.context_today(self)
        for rec in self:
            # Nếu tiến độ >= 100% hoặc đã hết hạn thì kết thúc
            if rec.progress >= 100.0 or (rec.date_end and today > rec.date_end):
                rec.state = 'done'
            else:
                rec.state = 'in_progress'