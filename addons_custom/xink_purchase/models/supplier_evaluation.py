from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class SupplierEvaluation(models.Model):
    _name = 'supplier.evaluation'
    _description = 'Đánh giá nhà cung cấp'
    _order = 'evaluation_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Mã đánh giá phải là duy nhất!'),
    ]

    name = fields.Char('Mã đánh giá', required=True, default='New', tracking=True)
    supplier_id = fields.Many2one('res.partner', string='Nhà cung cấp', 
                                  domain=[('is_company', '=', True), ('supplier_rank', '>', 0)], 
                                  required=True, tracking=True)
    department_id = fields.Many2one('hr.department', string='Bộ phận đánh giá', 
                                   default=lambda self: self._get_default_department(),
                                   required=False, tracking=True)
    evaluation_date = fields.Date('Ngày đánh giá', default=fields.Date.context_today, required=True)
    template_id = fields.Many2one('evaluation.template', string='Bộ tiêu chí đánh giá', required=True)
    
    line_ids = fields.One2many('supplier.evaluation.line', 'evaluation_id', string='Chi tiết đánh giá')
    note = fields.Text('Ghi chú')

    total_score = fields.Float('Tổng điểm', compute='_compute_classification', store=True, readonly=True)

    max_score = fields.Float('Điểm tối đa', compute='_compute_max_score', store=True, readonly=True)

    state = fields.Selection([
        ('draft', 'Nháp'),
        ('submitted', 'Đã gửi'),
        ('approved', 'Đã duyệt'),
        ('rejected', 'Từ chối'),
    ], string='Trạng thái', default='draft', tracking=True)

    status_display = fields.Html(string="Hiển thị trạng thái", compute="_compute_status_display", sanitize=False)

    classification = fields.Char(string='Xếp loại', compute='_compute_classification', store=True, readonly=True)

    classification_display = fields.Html(string="Hiển thị xếp loại", compute="_compute_classification_display", sanitize=False)

    def _get_default_department(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        if employee and employee.department_id:
            return employee.department_id.id
        return False

    @api.depends('template_id')
    def _compute_max_score(self):
        for record in self:
            record.max_score = 100

    @api.onchange('template_id')
    def _onchange_template_id(self):
        
        if self.template_id:
            
            self.line_ids = [(5, 0, 0)]
            
            if not self.template_id.criteria_line_ids:
                return
            
            lines = []
            for criteria in self.template_id.criteria_line_ids:
                lines.append((0, 0, {
                    'criteria_id': criteria.id,
                    'score': 0,
                }))
            
            self.line_ids = lines
        else:
            self.line_ids = [(5, 0, 0)]

    @api.depends('line_ids.score', 'line_ids.criteria_id.criteria_weight', 'line_ids.criteria_id.score_scale', 'line_ids.criteria_id.liet_score')
    def _compute_classification(self):
        for record in self:
            record.total_score = 0
            record.classification = 'eliminated'
            if not record.line_ids:
                continue
            try:
                total_score = 0
                total_possible = 0
                liet_found = False
                for line in record.line_ids:
                    scale = line.criteria_id.score_scale
                    score = line.score
                    if scale == '10':
                        score_10 = score
                        max_10 = 10
                    elif scale == '5':
                        score_10 = (score / 5) * 10
                        max_10 = 10
                    elif scale == 'boolean':
                        score_10 = 10 if score else 0
                        max_10 = 10
                    else:
                        score_10 = 0
                        max_10 = 0
                    weight = line.criteria_id.criteria_weight or 1
                    liet_score = getattr(line.criteria_id, 'liet_score', None)
                    _logger.info(f"[Eval {record.name}] Tiêu chí: {line.criteria_id.name}, Điểm gốc: {score}, Quy đổi thang 10: {score_10}, Điểm liệt: {liet_score}, Liet found: {liet_found}")
                    if liet_score is not None and score_10 <= liet_score:
                        liet_found = True
                    total_score += score_10 * weight
                    total_possible += max_10 * weight
                # Quy đổi về thang 100
                record.total_score = (total_score / total_possible) * 100 if total_possible else 0
                record.max_score = 100
                if liet_found:
                    record.classification = 'eliminated'
                    continue
                classification = 'eliminated'
                if record.template_id and record.template_id.rule_ids:
                    # Chỉ so sánh với min_score, bỏ max_score
                    for rule in record.template_id.rule_ids.filtered('active').sorted(key=lambda r: r.min_score, reverse=True):
                        if record.total_score >= rule.min_score:
                            classification = rule.category
                            break
                record.classification = classification
                print(f"Eval {record.name}: total_score={record.total_score}, classification={record.classification}, max_score={getattr(record, 'max_score', None)}")
            except Exception as e:
                _logger.warning(f"Error computing classification for record {record.id}: {str(e)}")
                record.total_score = 0
                record.classification = 'eliminated'
    @api.model
    def _get_default_template(self):
        return self.env['evaluation.template'].search([('active', '=', True)], limit=1).id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('template_id'):
                template = self.env['evaluation.template'].search([('active', '=', True)], limit=1)
                if template:
                    vals['template_id'] = template.id
            if not vals.get('line_ids') and vals.get('template_id'):
                template = self.env['evaluation.template'].browse(vals['template_id'])
                if template and template.criteria_line_ids:
                    vals['line_ids'] = [
                        (0, 0, {'criteria_id': c.id, 'score': 0}) for c in template.criteria_line_ids
                    ]
            if not vals.get('name') or vals.get('name') == 'New':
                new_name = self.env['ir.sequence'].next_by_code('supplier.evaluation') or 'New'
                while self.search([('name', '=', new_name)], limit=1):
                    new_name = self.env['ir.sequence'].next_by_code('supplier.evaluation') or 'New'
                vals['name'] = new_name
        records = super().create(vals_list)
        return records

    def action_submit(self):
        for record in self:
            if not record.line_ids:
                raise ValidationError('Vui lòng điền điểm cho ít nhất một tiêu chí!')
            
            has_score = any(line.score > 0 for line in record.line_ids)
            if not has_score:
                raise ValidationError('Vui lòng điền điểm đánh giá cho các tiêu chí!')
        
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_reject(self):
        self.write({'state': 'rejected'})

    def action_reset(self):
        self.write({'state': 'draft'})

    @api.constrains('line_ids')
    def _check_line_ids_criteria(self):
        for record in self:
            if record.template_id and record.template_id.criteria_line_ids:
                template_criteria_ids = set(record.template_id.criteria_line_ids.ids)
                line_criteria_ids = set(record.line_ids.mapped('criteria_id').ids)
                
                missing_criteria = template_criteria_ids - line_criteria_ids
                if missing_criteria:
                    missing_names = self.env['evaluation.criteria.line'].browse(missing_criteria).mapped('name')
                    raise ValidationError(f'Thiếu đánh giá cho các tiêu chí: {", ".join(missing_names)}')

    def get_classification_color(self):
        if self.template_id and self.classification:
            rule = self.template_id.rule_ids.filtered(lambda r: r.category == self.classification)
            if rule:
                color_map = {
                    'A': 'success',
                    'B': 'info',
                    'C': 'warning',
                    'eliminated': 'danger'
                }
                return color_map.get(self.classification, 'secondary')
        return 'secondary'

    @api.depends('state')
    def _compute_status_display(self):
        status_config = {
            'draft': {'label': 'Nháp', 'class': 'draft'},
            'submitted': {'label': 'Đã gửi', 'class': 'submitted'},
            'approved': {'label': 'Đã duyệt', 'class': 'approved'},
            'rejected': {'label': 'Từ chối', 'class': 'rejected'},
        }
        
        for rec in self:
            state = rec.state or 'draft'
            config = status_config.get(state, {'label': state, 'class': 'draft'})
            rec.status_display = f'<span class="badge badge-{config["class"]}">{config["label"]}</span>'

    @api.depends('classification')
    def _compute_classification_display(self):
        for rec in self:
            label = rec.classification or 'eliminated'
            color = rec.get_classification_color()
            # Lấy label hiển thị từ rule nếu có
            display_label = label
            if rec.template_id and rec.classification:
                rule = rec.template_id.rule_ids.filtered(lambda r: r.category == rec.classification)
                if rule:
                    display_label = rule[0].display_name if hasattr(rule[0], 'display_name') else rule[0].category
            rec.classification_display = f'<span class="badge badge-{color}">{display_label}</span>'
