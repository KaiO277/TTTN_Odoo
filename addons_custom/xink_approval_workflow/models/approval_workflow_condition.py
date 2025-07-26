from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ApprovalWorkflowCondition(models.Model):
    _name = 'xink.approval.workflow.condition'
    _description = 'Điều kiện Quy trình Phê duyệt'
    _order = 'sequence, id'

    name = fields.Char(string='Tên điều kiện', help="Tên mô tả cho điều kiện này")
    sequence = fields.Integer(string='Thứ tự', default=10)
    workflow_id = fields.Many2one('xink.approval.workflow', string='Quy trình', 
                                 required=True, ondelete='cascade')
    
    # Trường sẽ được lấy dynamically từ model_id của workflow
    conditional_field_id = fields.Many2one('ir.model.fields', string='Trường điều kiện',
                                          help="Chọn trường từ model để làm điều kiện")
    
    conditional_operator = fields.Selection([
        ('=', '= (Bằng)'),
        ('!=', '≠ (Khác)'),
        ('>', '> (Lớn hơn)'),
        ('>=', '≥ (Lớn hơn hoặc bằng)'),
        ('<', '< (Nhỏ hơn)'),
        ('<=', '≤ (Nhỏ hơn hoặc bằng)'),
    ], string='Toán tử so sánh', required=True,
       help="Chọn toán tử để so sánh giá trị")

    conditional_value = fields.Text(string='Giá trị điều kiện', required=True,
                                   help="Nhập giá trị để so sánh. VD: 5000000, 'draft', True, False, hoặc danh sách 'value1,value2,value3'")
    
    field_name = fields.Char(string='Tên trường', related='conditional_field_id.name', readonly=True)
    field_type = fields.Selection(string='Loại trường', related='conditional_field_id.ttype', readonly=True)
    field_description = fields.Char(string='Mô tả trường', related='conditional_field_id.field_description', readonly=True)
    condition_domain = fields.Char(string='Domain', compute='_compute_condition_domain', store=True)
    
    @api.depends('conditional_field_id', 'conditional_operator', 'conditional_value')
    def _compute_condition_domain(self):
        """Tính toán domain từ điều kiện"""
        for record in self:
            if record.conditional_field_id and record.conditional_operator and record.conditional_value:
                field_name = record.conditional_field_id.name
                operator = record.conditional_operator
                value = record.conditional_value.strip()
                
                try:
                    if operator in ['in', 'not in']:
                        value_list = [v.strip() for v in value.split(',')]
                        if record.field_type in ['integer', 'float', 'monetary']:
                            value = [float(v) if '.' in v else int(v) for v in value_list if v.replace('.', '').replace('-', '').isdigit()]
                        else:
                            value = value_list
                            
                    elif operator in ['is', 'is not']:
                        # Boolean
                        if value.lower() in ['true', '1', 'yes', 'đúng']:
                            value = True
                        elif value.lower() in ['false', '0', 'no', 'sai']:
                            value = False
                        else:
                            value = None
                            
                    elif record.field_type in ['integer', 'float', 'monetary'] and operator not in ['ilike', 'not ilike', '=ilike']:
                        # Số
                        if value.replace('.', '').replace('-', '').isdigit():
                            value = float(value) if '.' in value else int(value)
                            
                    elif operator in ['ilike', 'not ilike'] and not value.startswith('%'):
                        # Chuỗi tìm kiếm
                        value = f'%{value}%'
                        
                except (ValueError, AttributeError):
                    pass
                
                record.condition_domain = str([(field_name, operator, value)])
            else:
                record.condition_domain = False
    
    @api.onchange('workflow_id')
    def _onchange_workflow_id(self):
        """Reset field khi đổi workflow"""
        if self.workflow_id:
            self.conditional_field_id = False
        
    @api.onchange('conditional_field_id')
    def _onchange_conditional_field_id(self):
        """Tự động điền tên điều kiện"""
        if self.conditional_field_id and not self.name:
            self.name = f"Điều kiện {self.conditional_field_id.field_description}"
