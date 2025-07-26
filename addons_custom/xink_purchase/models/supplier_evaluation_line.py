
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SupplierEvaluationLine(models.Model):
    @api.onchange('score', 'score_bool')
    def _onchange_notify_parent(self):
        for line in self:
            if line.evaluation_id:
                line.evaluation_id._compute_classification()
    _name = 'supplier.evaluation.line'
    _description = 'Chi tiết đánh giá nhà cung cấp'

    evaluation_id = fields.Many2one('supplier.evaluation', string='Đánh giá', required=True, ondelete='cascade')
    criteria_id = fields.Many2one('evaluation.criteria.line', string='Tiêu chí', required=True)
    
    score_scale = fields.Selection(related='criteria_id.score_scale', string='Thang điểm', store=True)
    score = fields.Float(string='Điểm đánh giá', default=0)
    score_bool = fields.Selection([
        ('10', 'Đạt'),
        ('0', 'Không đạt')
    ], string='Đạt/Không đạt', default='0')

    def button_set_dat(self):
        for line in self:
            if line.score_scale == 'boolean':
                line.score_bool = '10'
                line.score = 10

    def button_set_khong_dat(self):
        for line in self:
            if line.score_scale == 'boolean':
                line.score_bool = '0'
                line.score = 0
    
    @api.constrains('score', 'score_bool', 'criteria_id')
    def _check_score_range(self):
        for line in self:
            if not line.criteria_id:
                continue
            min_score = line.criteria_id.min_score or 0
            max_score = line.criteria_id.max_score or 0
            if line.criteria_id.score_scale == 'boolean':
                if line.score_bool == '10':
                    if line.score != 10:
                        line.score = 10
                elif line.score_bool == '0':
                    if line.score != 0:
                        line.score = 0
                if line.score not in (0, 10):
                    raise ValidationError(f'Chỉ được chọn Đạt (10) hoặc Không đạt (0) cho tiêu chí "{line.criteria_id.name}"!')
            else:
                if line.score < min_score or line.score > max_score:
                    raise ValidationError(f'Điểm phải nằm trong khoảng {min_score} - {max_score} theo tiêu chí "{line.criteria_id.name}"!')

    @api.onchange('score_bool')
    def _onchange_score_bool(self):
        for line in self:
            if line.score_scale == 'boolean':
                line.score = 10 if line.score_bool == '10' else 0

    @api.onchange('score')
    def _onchange_score(self):
        for line in self:
            if line.score_scale == 'boolean':
                if line.score == 10:
                    line.score_bool = '10'
                else:
                    line.score_bool = '0'