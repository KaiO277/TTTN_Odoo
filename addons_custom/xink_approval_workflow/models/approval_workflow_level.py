from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ApprovalLevel(models.Model):
    _name = 'xink.approval.workflow.level'
    _description = 'Cấp Phê duyệt Quy trình'
    _order = 'sequence, id'

    name = fields.Char(string='Tên cấp duyệt', required=True, translate=True)
    sequence = fields.Integer(string='Thứ tự', default=10, 
                             help="Thứ tự xác định trình tự thực hiện")
    workflow_id = fields.Many2one('xink.approval.workflow', string='Quy trình', 
                                 required=True, ondelete='cascade')
    
    approver_type = fields.Selection([
        ('user', 'Người dùng cụ thể'),
        ('department_manager', 'Phòng ban'),
    ], string='Loại người duyệt', default='user', required=True)
    
    user_ids = fields.Many2many('res.users', string='Người dùng',
                               help="Những người dùng cụ thể có thể phê duyệt ở cấp này")
    
    department_ids = fields.Many2many('hr.department', string='Phòng ban',
                                    help="Trưởng phòng của các phòng ban này có thể phê duyệt ở cấp này")
    
    approval_mode = fields.Selection([
        ('all', 'Tất cả người duyệt'),
        ('any', 'Bất kỳ người duyệt nào'),
        ('percentage', 'Theo tỷ lệ phần trăm')
    ], string='Chế độ phê duyệt', default='all', required=True,
        help="Cách xác định phê duyệt: Tất cả người duyệt phải duyệt, bất kỳ người nào, hoặc theo tỷ lệ phần trăm")
    
    required_percentage = fields.Float(string='Tỷ lệ yêu cầu (%)', default=50.0,
                                     help="Tỷ lệ phần trăm người duyệt cần thiết (khi chế độ là 'percentage')")

