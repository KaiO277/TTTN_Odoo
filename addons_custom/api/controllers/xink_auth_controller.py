from odoo import http
from odoo.http import request
from ..utils.jwt_helper import xink_extract_authorization, xink_generate_access_token
from ..utils.response_helper import *
from ..service.attendance_service import AttendanceService

import logging

_logger = logging.getLogger(__name__)


class XinkAuthController(http.Controller):
    @http.route('/api/auth/login', type='http', auth='none', methods=['POST'], csrf=False)
    def login(self):
        try:
            try:
                data = json.loads(request.httprequest.data or '{}')
            except json.JSONDecodeError:
                return xink_json_response_error('Invalid JSON body.')

            username = data.get('username')
            password = data.get('password')
            if not username or not password:
                return xink_json_response_error('Missing username or password')

            user = request.env['res.users'].sudo().search([('login', '=', username)], limit=1)
            if not user:
                return xink_json_response_error('User not found', 404)

            try:
                request.env.cr.execute("SELECT COALESCE(password, '') FROM res_users WHERE id=%s", [user.id])
                [hashed] = request.env.cr.fetchone()
                crypt = request.env['res.users']._crypt_context()
                is_valid, new_hash = crypt.verify_and_update(password, hashed)
            except Exception as e:
                _logger.exception('Crypt - verify_and_update: ' + str(e))
                return xink_json_response_error('Invalid password hash format: ' + str(e), 500)

            if is_valid:
                if new_hash:
                    user.write({'password': new_hash})

                latest_inout_info = AttendanceService.latest_inout_info(user.id)
                return xink_json_response_object(xink_generate_access_token(user, latest_inout_info))
            else:
                return xink_json_response_error('Unauthorized', 401)

        except Exception as e:
            _logger.exception('Login API exception: ' + str(e))
            return xink_json_response_error('Exception: ' + str(e), 500)

    @http.route('/api/auth/logout', type='http', auth='none', methods=['POST'], csrf=False)
    def logout(self):
        try:
            try:
                refresh_token = xink_extract_authorization()
            except Exception as e:
                return xink_json_response_error(str(e), 401)

            payload = xink_decode_token(refresh_token)

            # When is refresh token -> blacklist
            if payload.get('type') == 'refresh':
                exp = int(payload.get('exp'))
                xink_blacklist_token(payload.get('jti'), exp)

            return xink_json_response_ok('Logout successful')

        except Exception as e:
            _logger.exception('Logout API exception: ' + str(e))
            return xink_json_response_error('Exception: ' + str(e), 500)

    @http.route('/api/auth/refresh', type='http', auth='none', methods=['POST'], csrf=False)
    def refresh_token(self):
        try:
            refresh_token = xink_extract_authorization()
        except Exception as e:
            return xink_json_response_error(str(e), 401)

        payload = xink_decode_token(refresh_token)

        if payload.get('type') != 'refresh':
            return xink_json_response_error('Invalid token type')

        try:
            jti = payload.get('jti')
            if xink_is_token_blacklisted(jti):
                return xink_json_response_error('Token is blacklisted', 401)

            user_id = payload.get('uid')
            user = request.env['res.users'].sudo().browse(user_id)
            if not user.exists():
                return xink_json_response_error('User not found', 404)

            latest_inout_info = AttendanceService.latest_inout_info(user_id)
            return xink_json_response_object(xink_generate_access_token(user, latest_inout_info))

        except Exception as e:
            _logger.exception('Refresh token exception: ' + str(e))
            return xink_json_response_error('Exception: ' + str(e), 500)
