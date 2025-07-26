from odoo import models, fields, api


class XinkHashTag(models.Model):
    _name = 'xink.hash.tag'
    _description = 'Hash Tags for Activities'
    _order = 'name'
    _rec_name = 'name'
    
    activity_id = fields.Many2one(
        'mail.activity',
        string='Activity',
        required=True,
        ondelete='cascade',
        help='The activity this hash tag is associated with'
    )

    name = fields.Char(
        string='Tag Name',
        required=True,
        help='Name of the hash tag'
    )

    color = fields.Char(
        string='Color',
        default='#0066CC',
        help='Color hex code for the tag display'
    )
    
 
class MailActivity(models.Model):
    _inherit = 'mail.activity'

    xink_hash_tag_ids = fields.One2many(
        'xink.hash.tag',
        'activity_id',
        string='Hash Tags',
        help='Hash tags associated with this activity'
    )
    
    important_work = fields.Boolean(
        string='Important Work',
        default=False,
        help='Mark this activity as important work'
    )