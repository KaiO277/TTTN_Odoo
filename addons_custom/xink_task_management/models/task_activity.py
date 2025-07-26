from odoo import models, fields

class MailActivity(models.Model):
    _inherit = 'mail.activity'

    task_name = fields.Char('Tên Công việc')
    # Người thực hiện và Ngày đến hạn đã có sẵn: user_id, date_deadline
    task_tag_ids = fields.Many2many('xink.task.tag', string='Tag')
    # Thêm trường priority (quan trọng)
    priority = fields.Selection([
        ('0', 'Thường'),
        ('1', 'Quan trọng'),
    ], default='0', string='Độ ưu tiên')


class XinkTaskTag(models.Model):
    _name = 'xink.task.tag'
    _description = 'Task Tag'

    name = fields.Char('Tag Name', required=True) 