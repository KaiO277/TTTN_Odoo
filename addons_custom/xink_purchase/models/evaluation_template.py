from odoo import models, fields, api
from odoo.exceptions import ValidationError

class EvaluationTemplate(models.Model):
    # @api.onchange('criteria_line_ids', 'total_max_score', 'rule_ids')
    # def _onchange_criteria_line_ids_set_rule_priority_max(self):
    #     for template in self:
    #         if template.total_max_score and template.rule_ids:
    #             rule_a = template.rule_ids.filtered(lambda r: r.category == 'A')
    #             if rule_a:
    #                 rule_a[0].max_score = template.total_max_score
    # @api.constrains('rule_ids', 'total_max_score')
    # def _check_rule_max_score(self):
    #     for template in self:
    #         if not template.rule_ids:
    #             continue
    #         rule_a = template.rule_ids.filtered(lambda r: r.category == 'A')
    #         if rule_a and rule_a[0].max_score != template.total_max_score:
    #             raise ValidationError(
    #                 "Điểm tối đa của xếp loại A (max_score) phải bằng tổng điểm tối đa của bộ tiêu chí (total_max_score)!"
    #             )
    _name = 'evaluation.template'
    _description = 'Bộ cấu hình đánh giá nhà cung cấp'

    name = fields.Char('Tên bộ đánh giá', required=True)
    active = fields.Boolean('Kích hoạt', default=True)
    criteria_line_ids = fields.One2many('evaluation.criteria.line', 'template_id')
    rule_ids = fields.One2many('evaluation.rule', 'template_id')
    total_max_score = fields.Float('Tổng điểm tối đa', compute='_compute_total_max_score', store=True, 
                                   help="Tổng điểm tối đa có thể đạt được từ tất cả tiêu chí")

    @api.depends('criteria_line_ids.max_score')
    def _compute_total_max_score(self):
        for template in self:
            template.total_max_score = sum(template.criteria_line_ids.mapped('max_score'))

class EvaluationCriteriaLine(models.Model):
    _name = 'evaluation.criteria.line'
    _description = 'Tiêu chí đánh giá nhà cung cấp'

    template_id = fields.Many2one('evaluation.template', string='Bộ đánh giá', required=True, ondelete='cascade')
    name = fields.Char('Tên tiêu chí', required=True)
    score_scale = fields.Selection([
        ('boolean', 'Đạt/Không đạt'),
        ('5', 'Thang điểm 5'),
        ('10', 'Thang điểm 10'),
    ], string='Thang điểm', required=True, default='10')
    criteria_weight = fields.Float('Hệ số', required=True, default=1.0)
    min_score = fields.Float('Điểm tối thiểu', default=0.0)
    liet_score = fields.Float('Điểm liệt', default=0.0, help="Nếu điểm tiêu chí này nhỏ hơn hoặc bằng điểm liệt thì coi là bị loại.")
    max_score = fields.Float('Điểm tối đa', compute='_compute_max_score', store=True)

    @api.depends('criteria_weight', 'score_scale')
    def _compute_max_score(self):
        for rec in self:
            if rec.score_scale == 'boolean':
                rec.max_score = 10 * rec.criteria_weight
            else:
                try:
                    scale = int(rec.score_scale or 0)
                except Exception:
                    scale = 0
                rec.max_score = rec.criteria_weight * scale

class EvaluationRule(models.Model):
    # @api.onchange('category', 'template_id')
    # def _onchange_max_score_for_A(self):
    #     if self.category == 'A' and self.template_id:
    #         self.max_score = self.template_id.total_max_score
    #     elif self.category != 'A':
    #         pass
    _name = 'evaluation.rule'
    _description = 'Quy tắc xếp loại'
    _order = 'min_score desc'

    min_score = fields.Float(string='Điểm tối thiểu', required=True)
    # max_score = fields.Float(string='Điểm tối đa', required=True)  # Không sử dụng, chỉ so sánh min_score
    category = fields.Selection([
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('eliminated', 'Eliminated'),
    ], string='Xếp loại', required=True)
    active = fields.Boolean(string='Kích hoạt', default=True)
    template_id = fields.Many2one('evaluation.template', string='Bộ đánh giá')

    # @api.constrains('min_score', 'max_score')
    # def _check_score_range(self):
    #     for rule in self:
    #         if rule.min_score > rule.max_score:
    #             raise ValidationError("Điểm tối thiểu không được lớn hơn điểm tối đa!")
