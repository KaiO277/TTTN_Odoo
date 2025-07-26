from odoo import http
from odoo.http import request, Response
from ..utils.jwt_helper import xink_check_auth_and_company
from ..utils.response_helper import *
import json

def _location_to_dict(location):
    return {
        'id': location.id,
        'name': location.name,
        'latitude': location.latitude,
        'longitude': location.longitude,
        'radiusCheckin': location.radius_checkin,
        'description': location.description,
        'companyId': location.company_id.id,
        'companyName': location.company_id.name
    }


class XinkCompanyLocationController(http.Controller):

    @http.route('/api/company_locations', type='http', auth='none', methods=['GET'], csrf=False)
    def get_locations(self):
        res = xink_check_auth_and_company()
        if isinstance(res, Response):
            return res
        user, company_id = res
        if not company_id:
            return xink_json_response_error('Unauthorized', 401)

        locations = request.env['xink.company.location'].sudo().search([
            ('company_id', '=', company_id),
            ('active', '=', True)
        ])

        location_dict = [_location_to_dict(l) for l in locations]
        root_response = RootResponse(data=location_dict)
        return xink_json_response_object(root_response.to_dict())

    @http.route('/api/company_location/<string:loc_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def get_location(self, loc_id):
        try:
            loc_id = int(loc_id)
        except ValueError:
            return xink_json_response_error('Invalid location ID (must be integer)')

        res = xink_check_auth_and_company()
        if isinstance(res, Response):
            return res
        user, company_id = res
        if not company_id:
            return xink_json_response_error('Unauthorized', 401)


        location = request.env['xink.company.location'].sudo().browse(loc_id)
        if not location.exists():
            return xink_json_response_error('Location not found', 404)

        if location.company_id.id != company_id:
            return xink_json_response_error('Access denied', 403)

        root_response = RootResponse(data=_location_to_dict(location))
        return xink_json_response_object(root_response.to_dict())

    @http.route('/api/company_location', type='http', auth='none', methods=['POST'], csrf=False)
    def create_location(self):
        res = xink_check_auth_and_company()
        if isinstance(res, Response):
            return res
        user, company_id = res
        if not company_id:
            return xink_json_response_error('Unauthorized', 401)

        try:
            data = json.loads(request.httprequest.data or '{}')

            required_fields = ['name', 'latitude', 'longitude', 'radiusCheckin']
            for field in required_fields:
                if not data.get(field):
                    return xink_json_response_error(f'{field} is required', 400)

            location_name = data.get('name', '').strip().lower()
            existing = request.env['xink.company.location'].sudo().search([
                ('company_id', '=', company_id),
                ('name', 'ilike', location_name)
            ], limit=1)
            if existing:
                return xink_json_response_error('Location name already exists', 409)

            vals = {
                'name': data.get('name', '').strip(),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                'radius_checkin': data.get('radiusCheckin'),
                'description': data.get('description'),
                'company_id': company_id
            }
            location = request.env['xink.company.location'].sudo().create(vals)
            location_dict = _location_to_dict(location)
            root_response = RootResponse(message='Location created successfully', data=location_dict)
            return xink_json_response_object(root_response.to_dict())

        except Exception as e:
            return xink_json_response_error('Create failed: ' + str(e), 500)

    @http.route('/api/company_location/<string:loc_id>', type='http', auth='none', methods=['PUT'], csrf=False)
    def update_location(self, loc_id):
        try:
            loc_id = int(loc_id)
        except ValueError:
            return xink_json_response_error('Invalid location ID (must be integer)')

        res = xink_check_auth_and_company()
        if isinstance(res, Response):
            return res
        user, company_id = res
        if not company_id:
            return xink_json_response_error('Unauthorized', 401)

        location = request.env['xink.company.location'].sudo().browse(loc_id)
        if not location.exists():
            return xink_json_response_error('Location not found', 404)

        # Prevent editing location of another company
        if location.company_id.id != company_id:
            return xink_json_response_error('Access denied', 403)

        try:
            data = json.loads(request.httprequest.data or '{}')

            required_fields = ['name', 'latitude', 'longitude', 'radiusCheckin']
            for field in required_fields:
                if not data.get(field):
                    return xink_json_response_error(f'{field} is required', 400)

            location_name = data.get('name', '').strip().lower()
            existing = request.env['xink.company.location'].sudo().search([
                ('id', '!=', loc_id),
                ('company_id', '=', company_id),
                ('name', 'ilike', location_name)
            ], limit=1)
            if existing:
                return xink_json_response_error('Location name already exists', 409)

            vals = {
                'name': data.get('name', '').strip(),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                'radius_checkin': data.get('radiusCheckin'),
                'description': data.get('description')
            }
            location.write({k: v for k, v in vals.items() if v is not None})
            location_dict = _location_to_dict(location)
            root_response = RootResponse(message='Location updated successfully', data=location_dict)
            return xink_json_response_object(root_response.to_dict())
        except Exception as e:
            return xink_json_response_error('Update failed: ' + str(e), 500)

    @http.route('/api/company_location/<string:loc_id>', type='http', auth='none', methods=['DELETE'], csrf=False)
    def delete_location(self, loc_id):
        try:
            loc_id = int(loc_id)
        except ValueError:
            return xink_json_response_error('Invalid location ID (must be integer)')

        res = xink_check_auth_and_company()
        if isinstance(res, Response):
            return res
        user, company_id = res
        if not company_id:
            return xink_json_response_error('Unauthorized', 401)

        location = request.env['xink.company.location'].sudo().browse(loc_id)
        if not location.exists():
            return xink_json_response_error('Location not found', 404)

        # Prevent deleting location of another company
        if location.company_id.id != company_id:
            return xink_json_response_error('Access denied', 403)

        location.write({'active': False})  # Soft delete
        return xink_json_response_ok('Location deleted successfully')
