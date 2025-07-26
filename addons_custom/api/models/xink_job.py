from odoo import models, fields, api
import logging
import requests
import json

_logger = logging.getLogger(__name__)


class XinkJob(models.Model):
    _name = 'xink.job'
    _description = 'Employee Job Check-in Management'
    _order = 'check_in desc'
    _rec_name = 'shop_name'

    employee_id = fields.Many2one(
        'hr.employee', 
        string='Employee', 
        required=True,
        ondelete='cascade'
    )
    
    longitude = fields.Float(
        string='Longitude', 
        digits=(10, 6),
        help='GPS longitude coordinate'
    )
    latitude = fields.Float(
        string='Latitude', 
        digits=(10, 6),
        help='GPS latitude coordinate'
    )
    
    check_in = fields.Datetime(
        string='Check-in Time', 
        required=True,
        default=fields.Datetime.now
    )
    
    shop_name = fields.Char(
        string='Shop Name', 
        required=True,
        size=200
    )
    shop_owner_name = fields.Char(
        string='Shop Owner Name', 
        size=150
    )
    phone_number = fields.Char(
        string='Phone Number', 
        size=20
    )
    
    potential_customer = fields.Boolean(
        string='Potential Customer', 
        default=False,
        help='Mark if this shop is a potential customer'
    )
    job_content = fields.Text(
        string='Job Content',
        help='Description of work performed'
    )
    job_note = fields.Text(
        string='Job Note',
        help='Additional notes about the job'
    )
    
    location_display = fields.Char(
        string='Location', 
        compute='_compute_location_display',
        store=True
    )
    
    display_name = fields.Char(
        string='Address Display Name',
        size=500,
        help='Address from GPS coordinates via Nominatim API'
    )
    
    @api.depends('latitude', 'longitude')
    def _compute_location_display(self):
        for record in self:
            if record.latitude and record.longitude:
                record.location_display = f"{record.latitude:.6f}, {record.longitude:.6f}"
            else:
                record.location_display = ""
    
    @api.model
    def create(self, vals):
        """Override create to add logging and get address"""
        
        # Get address from coordinates if provided
        if vals.get('latitude') and vals.get('longitude'):
            display_name = self._get_address_from_coordinates(vals['latitude'], vals['longitude'])
            vals['display_name'] = display_name
    
        result = super().create(vals)
        return result
    
    def write(self, vals):
        """Override write to add logging"""
        
        if 'latitude' in vals or 'longitude' in vals:
            latitude = vals.get('latitude', self.latitude)
            longitude = vals.get('longitude', self.longitude)
            
            if latitude and longitude:
                display_name = self._get_address_from_coordinates(latitude, longitude)
                if display_name:
                    vals['display_name'] = display_name
        
        return super().write(vals)
    
    def unlink(self):
        """Override unlink to add logging"""
        _logger.info(f"Deleting xink.job records: {self.ids}")
        return super().unlink()

    @api.constrains('latitude', 'longitude')
    def _check_coordinates(self):
        for record in self:
            if record.latitude and (record.latitude < -90 or record.latitude > 90):
                raise models.ValidationError("Latitude must be between -90 and 90 degrees")
            if record.longitude and (record.longitude < -180 or record.longitude > 180):
                raise models.ValidationError("Longitude must be between -180 and 180 degrees")

    def _get_address_from_coordinates(self, latitude, longitude):
        """Get address from GPS coordinates using Nominatim API"""
        try:
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                'format': 'jsonv2',
                'lat': float(latitude),
                'lon': float(longitude),
                'accept-language': 'vi,en'
            }
            
            headers = {
                'User-Agent': 'Odoo-Xink'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                display_name = data.get('display_name')
                
                if display_name:
                    return display_name
                else:
                    return None
            else:
                return None
        except Exception as e:
            return None
