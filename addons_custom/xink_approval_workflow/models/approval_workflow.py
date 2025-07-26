from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import ValidationError


class ApprovalWorkflow(models.Model):
    _name = 'xink.approval.workflow'
    _description = 'Approval Workflow'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name, id'

    name = fields.Char(string='Name', required=True, tracking=True, translate=True)
    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade',
                              domain="[('model', 'in', ['sale.order', 'purchase.order'])]",
                              help="Chọn loại phiếu áp dụng quy trình phê duyệt (Bán hàng, Mua hàng, Hóa đơn, Phiếu kho)")
    department_id = fields.Many2one('hr.department', string='Phòng Ban', 
                                   help="Phòng ban áp dụng quy trình phê duyệt này")
    active = fields.Boolean(default=True, tracking=True)
    
    # Điều kiện áp dụng - sử dụng bảng riêng
    condition_ids = fields.One2many('xink.approval.workflow.condition', 'workflow_id', 
                                   string='Các điều kiện áp dụng',
                                   help="Danh sách các điều kiện để kích hoạt quy trình phê duyệt")
    
    # Domain tổng hợp từ tất cả điều kiện
    final_domain = fields.Text(string='Domain cuối cùng', compute='_compute_final_domain', store=True,
                              help="Domain được tạo từ tất cả các điều kiện")
    
    level_ids = fields.One2many('xink.approval.workflow.level', 'workflow_id', string='Các cấp phê duyệt của quy trình này')

    notify_user_ids = fields.Many2many('res.users', string='Notify Users',
                                        help="Danh sách người dùng nhận thông báo khi hoàn thành")
    
    @api.depends('condition_ids.condition_domain')
    def _compute_final_domain(self):
        """Tính toán domain cuối cùng từ tất cả các điều kiện"""
        for record in self:
            if not record.condition_ids:
                record.final_domain = "[]"
                continue
                
            domains = []
            for condition in record.condition_ids:
                if condition.condition_domain:
                    try:
                        domain = eval(condition.condition_domain)
                        if isinstance(domain, list) and domain:
                            domains.append(domain[0])  # Lấy tuple đầu tiên
                    except:
                        continue
            
            if not domains:
                record.final_domain = "[]"
            elif len(domains) == 1:
                record.final_domain = str([domains[0]])
            else:
                # Kết hợp các điều kiện với AND logic
                record.final_domain = str(domains)
    
    def action_save_workflow(self):
        """Lưu quy trình phê duyệt"""
        if not self.name:
            raise ValidationError("Tên quy trình không được để trống")
        if not self.model_id:
            raise ValidationError("Phải chọn model áp dụng")
        self.write({})
        
        # Return action to refresh the form or go to list view
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'xink.approval.workflow',
            'view_mode': 'list',
            'target': 'current',
        }
    

