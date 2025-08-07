from odoo import models, fields

from geopy.distance import geodesic


class CompanyLocation(models.Model):
    _name = 'xink.company.location'
    _description = 'Company Check-in Location'
    _order = 'name'

    name = fields.Char(string='Location Name', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, ondelete='cascade')
    latitude = fields.Float(string="Latitude", required=True)
    longitude = fields.Float(string="Longitude", required=True)
    radius_checkin = fields.Integer(string="Check-in Radius (m)", default=100)
    description = fields.Char(string="Description / Note")
    active = fields.Boolean(default=True)


class ResCompany(models.Model):
    _inherit = 'res.company'
    _description = 'List of company locations'

    location_ids = fields.One2many('xink.company.location', 'company_id', string='Check-in Locations')

    xink_checkin_by_wifi = fields.Boolean(string='Check-in by WiFi', default=False)
    xink_checkin_by_location = fields.Boolean(string='Check-in by Location', default=False)

    def is_user_within_location(self, user_lat, user_long):
        if not isinstance(user_lat, (float, int)) or not isinstance(user_long, (float, int)):
            raise ValueError("Invalid coordinates")

        self.ensure_one()
        for loc in self.location_ids.filtered(lambda l: l.active):
            distance = geodesic((loc.latitude, loc.longitude), (user_lat, user_long)).m
            if distance <= loc.radius_checkin:
                return True, {'name': loc.name, 'id': loc.id, 'description': loc.description, 'distance': round(distance, 2)}
        return False, None
