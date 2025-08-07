from odoo import http
from odoo.http import request, Response
from ..utils.jwt_helper import xink_extract_user_from_token, xink_check_auth_and_company
from ..utils.response_helper import *
from werkzeug.exceptions import NotFound
from odoo.exceptions import AccessDenied

import json
import logging

_logger = logging.getLogger(__name__)


class XinkWifiController(http.Controller):
    @http.route('/api/wifi', type='http', auth='none', methods=['GET'], csrf=False)
    def get_wifi_list(self):
        # Check token
        res = xink_check_auth_and_company()
        if isinstance(res, Response):
            return res
        user, company_id = res
        if not company_id:
            return xink_json_response_error('Unauthorized', 401)

        wifi_list = request.env['wifi'].sudo().search([('company_id', '=', int(company_id))])
        wifi_dict = [{
            'id': rec.id,
            'wifiName': rec.wifi_name,
            'companyId': rec.company_id.id,
            'companyName': rec.company_id.name
        } for rec in wifi_list]

        root_response = RootResponse(data=wifi_dict)
        return xink_json_response_object(root_response.to_dict())

    @http.route('/api/wifi/<wifi_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def get_wifi_by_id(self, wifi_id):
        # Check token
        res = xink_check_auth_and_company()
        if isinstance(res, Response):
            return res
        user, company_id = res
        if not company_id:
            return xink_json_response_error('Unauthorized', 401)

        try:
            wifi_id = int(wifi_id)
        except ValueError:
            return xink_json_response_error('Invalid wifi ID (must be integer)')

        try:
            wifi = request.env['wifi'].sudo().browse(wifi_id)
            if not wifi.exists():
                return xink_json_response_error('Wifi not found', 404)

            wifi_dict = {
                'id': wifi.id,
                'wifiName': wifi.wifi_name,
                'companyId': wifi.company_id.id,
                'companyName': wifi.company_id.name
            }

            root_response = RootResponse(data=wifi_dict)
            return xink_json_response_object(root_response.to_dict())

        except Exception as e:
            _logger.exception('Wifi: get_by_id: ' + str(e))
            return xink_json_response_error('Exception: ' + str(e), 500)

    @http.route('/api/wifi', type='http', auth='none', methods=['POST'], csrf=False)
    def create_wifi(self):
        # Check token
        res = xink_check_auth_and_company()
        if isinstance(res, Response):
            return res
        user, company_id = res
        if not company_id:
            return xink_json_response_error('Unauthorized', 401)

        try:
            data = json.loads(request.httprequest.data or '{}')
        except json.JSONDecodeError:
            return xink_json_response_error('Invalid JSON body')

        company_request_id = data.get('companyId') or company_id
        wifi_name = data.get('wifiName')
        if not wifi_name:
            return xink_json_response_error('Wifi name is requried')
        if not company_request_id:
            return xink_json_response_error('Company ID is required')

        try:
            # Check Wi-Fi exists
            wifi_exist = request.env['wifi'].sudo().search([
                ('wifi_name', '=', wifi_name),
                ('company_id', '=', company_request_id)
            ], limit=1)
            if wifi_exist:
                return xink_json_response_error(
                    f"Wifi name '{wifi_name}' already exists for company ID: {company_request_id}.",
                    409)

            wifi = request.env['wifi'].sudo().create({'wifi_name': wifi_name, 'company_id': company_request_id})
            wifi_dict = {
                'id': wifi.id,
                'wifiName': wifi.wifi_name,
                'companyId': wifi.company_id.id,
                'companyName': wifi.company_id.name
            }

            root_response = RootResponse(message='Wifi created successfully', data=wifi_dict)
            return xink_json_response_object(root_response.to_dict())

        except Exception as e:
            _logger.exception('Wifi: create: ' + str(e))
            return xink_json_response_error('Exception: ' + str(e), 500)

    @http.route('/api/wifi/<wifi_id>', type='http', auth='none', methods=['PUT'], csrf=False)
    def update_wifi(self, wifi_id):
        # Check token
        res = xink_check_auth_and_company()
        if isinstance(res, Response):
            return res
        user, company_id = res
        if not company_id:
            return xink_json_response_error('Unauthorized', 401)

        try:
            wifi_id = int(wifi_id)
        except ValueError:
            return xink_json_response_error('Invalid wifi ID (must be integer)')

        wifi = request.env['wifi'].sudo().browse(wifi_id)
        if not wifi.exists():
            return xink_json_response_error('Wifi not found', 404)

        try:
            data = json.loads(request.httprequest.data or '{}')
        except json.JSONDecodeError:
            return xink_json_response_error('Invalid JSON body')

        company_request_id = data.get('companyId') or company_id
        wifi_name = data.get('wifiName')
        if not wifi_name:
            return xink_json_response_error('Wifi name is required')
        if not company_request_id:
            return xink_json_response_error('Company ID is required')

        try:
            # Check Wi-Fi exists
            wifi_exist = request.env['wifi'].sudo().search([
                ('id', '!=', wifi_id),
                ('wifi_name', '=', wifi_name),
                ('company_id', '=', company_request_id)
            ], limit=1)
            if wifi_exist:
                return xink_json_response_error(
                    f"Wifi name '{wifi_name}' already exists for company ID: {company_request_id}.",
                    409)

            wifi.write({'wifi_name': wifi_name})
            wifi_dict = {
                'id': wifi.id,
                'wifiName': wifi.wifi_name,
            }

            root_response = RootResponse(message='Wifi updated successfully', data=wifi_dict)
            return xink_json_response_object(root_response.to_dict())
        except Exception as e:
            _logger.exception('Wifi: update: ' + str(e))
            return xink_json_response_error('Exception: ' + str(e), 500)

    @http.route('/api/wifi/<wifi_id>', type='http', auth='none', methods=['DELETE'], csrf=False)
    def delete_wifi(self, wifi_id):
        # Check token
        res = xink_check_auth_and_company()
        if isinstance(res, Response):
            return res
        user, company_id = res
        if not company_id:
            return xink_json_response_error('Unauthorized', 401)

        try:
            wifi_id = int(wifi_id)
        except ValueError:
            return xink_json_response_error('Invalid wifi ID (must be integer)')

        wifi = request.env['wifi'].sudo().browse(wifi_id)
        if not wifi.exists():
            return xink_json_response_error('Wifi name not found', 404)
        try:
            wifi.unlink()
            return xink_json_response_ok('Wifi deleted successfully')
        except Exception as e:
            _logger.exception('Wifi: delete: ' + str(e))
            return xink_json_response_error('Exception: ' + str(e), 500)

    # Using for OneXink TODO
    @http.route('/api/wifi/by_company/<company_id>', type='http', auth='none', methods=['GET'], csrf=False)
    def get_wifi_by_company(self, company_id):
        # Check token
        try:
            xink_extract_user_from_token()
        except NotFound as e:
            return xink_json_response_error(str(e), 404)
        except AccessDenied as e:
            return xink_json_response_error(str(e), 401)
        except Exception as e:
            return xink_json_response_error(str(e), 500)

        wifi_list = request.env['wifi'].sudo().search([('company_id', '=', int(company_id))])
        wifi_dict = [{
            'id': rec.id,
            'wifiName': rec.wifi_name,
            'companyId': rec.company_id.id,
            'companyName': rec.company_id.name
        } for rec in wifi_list]

        root_response = RootResponse(data=wifi_dict)
        return xink_json_response_object(root_response.to_dict())
