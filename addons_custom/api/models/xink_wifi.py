from odoo import models, fields


class Wifi(models.Model):
    _name = 'wifi'
    _description = 'Xink Wifi'
    _check_company_auto = True

    wifi_name = fields.Char(string='Wifi Name', required=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company.id
    )
