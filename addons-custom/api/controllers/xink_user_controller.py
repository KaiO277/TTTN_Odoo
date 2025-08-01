from odoo import http, fields
from urllib.parse import quote
from odoo.http import request
from ..utils.jwt_helper import xink_check_auth_and_company, xink_get_roles_by_user, xink_request_env, xink_generate_password
from ..utils.response_helper import *

import json
import math
import logging

_logger = logging.getLogger(__name__)

class XinkUserController(http.Controller):
    @http.route('/api/user/register', type='http', auth='none', methods=['POST'], csrf=False)
    def user_register(self):
        try:
            # Parse JSON input
            try:
                data = json.loads(request.httprequest.data or '{}')
                xink_request_env()
            except json.JSONDecodeError:
                return xink_json_response_error('Invalid JSON body', 400)

            company_name = data.get('companyName', '').strip()
            manager_name = data.get('manager', '').strip()
            email = data.get('email', '').strip().lower()
            password = data.get('password', '').strip()

            # Validate required fields
            if not all([company_name, manager_name, email, password]):
                return xink_json_response_error('Required fields are missing', 400)

            # Check duplicate company
            existing_company = request.env['res.company'].sudo().search([('name', '=', company_name)], limit=1)
            if existing_company:
                return xink_json_response_error('Company name already exists', 409)

            # Check duplicate email
            existing_user = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
            if existing_user:
                return xink_json_response_error('Email already registered', 409)

            # Get currency
            currency = next(
                (c for c in request.env['res.currency'].sudo().search([('name', 'in', ['VND', 'USD'])])
                 if c.name == 'VND' or c.name == 'USD'),
                None
            )
            if not currency:
                return xink_json_response_error('Currency VND or USD not found', 404)

            # Get Permission
            res_group_admin = request.env.ref('xink_easy_checkin.group_xink_easy_checkin_admin',
                                              raise_if_not_found=False)
            if not res_group_admin:
                return xink_json_response_error('Required groups (permission) not found', 500)

            # Transaction block
            try:
                with request.env.cr.savepoint():
                    # Create company
                    company = request.env['res.company'].sudo().create({
                        'name': company_name,
                        'currency_id': currency.id
                    })

                    # Create user linked to company
                    user = request.env['res.users'].sudo().with_context(
                        no_reset_password=True,
                        tracking_disable=True,
                        mail_create_nosubscribe=True,
                        create_user=False
                    ).create({
                        'name': manager_name,
                        'login': email,
                        'company_id': company.id,
                        'company_ids': [(6, 0, [company.id])],
                        'password': password,
                        'groups_id': [(6, 0, [res_group_admin.id])],
                        'notification_type': 'email',
                        'active': True
                    })
                    expire_days = 7
                    user.partner_id.xink_generate_signup_token(expire_days * 24 * 60)  # ngày
                    user.partner_id.write({
                        'company_id': company.id,
                        'user_id': user.id,
                        'email': email,
                        'signup_type': 'api_register'
                    })
                    user.write({'active': False})

                    email_to = email
                    subject = 'Kích hoạt tài khoản'
                    safe_token = quote(user.partner_id.signup_token)
                    body_html = f"""
                            <p>
                                <a href="{xink_base_url()}/api/user/activate?token={safe_token}">
                                    Kích hoạt tài khoản
                                </a>
                            </p>
                            <p>
                                Liên kết này có hiệu lực trong <strong>{expire_days} ngày</strong>.
                            </p>
                            """

                    request.env['xink.mail.sender'].sudo().xink_send_mail_direct(
                        subject=subject,
                        body_html=body_html,
                        email_to=email_to
                    )

                    response_data = {
                        'companyId': company.id,
                        'companyName': company.name,
                        'userId': user.id,
                        'userName': user.name,
                        'email': user.login
                    }
                    return xink_json_response_object(response_data)
            except Exception as ex:
                return xink_json_response_error(f'Failed: {str(ex)}', 500)

        except Exception as e:
            _logger.exception('Register account admin error: %s', str(e))
            return xink_json_response_error(f'Internal Server Error - Register account admin: {str(e)}', 500)

    @http.route('/api/user/activate', type='http', auth='none', methods=['GET'], csrf=False)
    def activate_account(self, token=None):
        try:
            if not token:
                return xink_html_response_active_account('Account activated failed: Token is required', False)

            partner = request.env['res.partner'].sudo().search([('signup_token', '=', token)], limit=1)
            if not partner:
                return xink_html_response_active_account('Account activated failed: Invalid or expired token', False)

            if partner.signup_expiration and fields.Datetime.now() > partner.signup_expiration:
                return xink_html_response_active_account('Account activated failed: Token expired', False)

            if partner.signup_type != 'api_register':
                return xink_html_response_active_account('Account activated failed: Invalid token type', False)

            # Get matching user (include inactive)
            user = request.env['res.users'].with_context(active_test=False).sudo().search(
                [('partner_id', '=', partner.id)], limit=1)
            if not user:
                return xink_html_response_active_account('Account activation failed: No matching user found', False)

            # Transaction block
            with request.env.cr.savepoint():
                #  Reset token
                partner.sudo().write({
                    'signup_token': False,
                    'signup_expiration': False
                })

                # Active tài khoản
                if not user.active:
                    # user.sudo().write({'active': True})
                    request.env.cr.execute("""UPDATE res_users SET active = TRUE WHERE id = %s""", [user.id])

                # Tạo employee
                roles = xink_get_roles_by_user(user)
                if any(r.get('roleId') == 'group_xink_easy_checkin_employee' for r in roles):
                    existing_employee = request.env['hr.employee'].sudo().search([('work_email', '=', partner.email)],
                                                                                 limit=1)
                    if not existing_employee:
                        request.env['hr.employee'].sudo().with_context(
                            mail_create_nosubscribe=True,
                            tracking_disable=True,
                            mail_activity_quick_update=False
                        ).create({
                            'name': partner.email,
                            'company_id': user.company_id.id if user.company_id else False,
                            'user_id': user.id,
                            'work_email': partner.email,
                            'employee_type': 'employee',
                            'distance_home_work_unit': 'kilometers',
                            'marital': 'single'
                        })

                return xink_html_response_active_account('Account activated successfully')

        except Exception as e:
            request.env.cr.rollback()
            _logger.exception('Activate error: %s', str(e))
            return xink_html_response_active_account('Account activated failed', False)

    @http.route('/api/user/request_reset_password', type='http', auth='none', methods=['POST'], csrf=False)
    def request_reset_password(self):
        try:
            # Parse JSON input
            try:
                data = json.loads(request.httprequest.data or '{}')
            except json.JSONDecodeError:
                return xink_json_response_error('Invalid JSON body', 400)

            email = data.get('email').strip().lower()
            user = request.env['res.users'].sudo().search([('partner_id.email', '=', email)], limit=1)
            if not user:
                return xink_json_response_error('User not found (by email)', 404)

            partner = user.partner_id
            partner.xink_generate_reset_otp(30)

            # ctx = {
            #     'email_from': config.get('email_from'),
            # }

            email_to = email
            subject = 'OTP reset password'
            body_html = f"""
                            <p>
                                OTP: {partner.xink_reset_otp}
                            </p>
                            <p>
                                OTP này có hiệu lực trong <strong>{30} phút !</strong>.
                            </p>
                            """

            request.env['xink.mail.sender'].sudo().xink_send_mail_direct(
                subject=subject,
                body_html=body_html,
                email_to=email_to
            )

            # mail_result = request.env['xink.mail.sender'].sudo().xink_send_mail_by_template(
            #     template_xml_id='api.reset_password_mail_template',
            #     record=user,
            #     ctx=ctx
            # )
            #
            # if not mail_result or mail_result.state != 'sent':
            #     return json_response_error(f'Failed', 500)

            return xink_json_response_ok('OTP has been sent to your email')

        except Exception as e:
            request.env.cr.rollback()
            _logger.exception('Activate error: %s', str(e))
            return xink_json_response_error(f'Internal Server Error: {str(e)}', 500)

    @http.route('/api/user/confirm_reset_password', type='http', auth='none', methods=['POST'], csrf=False)
    def confirm_reset_password(self):
        try:
            # Parse JSON input
            try:
                data = json.loads(request.httprequest.data or '{}')
                xink_request_env()
            except json.JSONDecodeError:
                return xink_json_response_error('Invalid JSON body', 400)

            email = data.get('email').strip().lower()
            otp = data.get('otp').strip()

            # Validate required fields
            if not all([email, otp]):
                return xink_json_response_error('Required fields are missing', 400)

            user = request.env['res.users'].sudo().search([('partner_id.email', '=', email)], limit=1)
            if not user:
                return xink_json_response_error('Email not found', 404)

            partner = user.partner_id
            if not partner.xink_reset_otp:
                return xink_json_response_error('OTP not found, please request a new', 404)

            if partner.xink_reset_otp != otp:
                new_fail_count = partner.xink_reset_otp_fail_count + 1
                partner.sudo().write({'xink_reset_otp_fail_count': new_fail_count})

                if new_fail_count >= 5:
                    partner.sudo().write({
                        'xink_reset_otp': False,
                        'xink_reset_otp_expiration': False,
                        'xink_reset_otp_fail_count': 0
                    })
                    return xink_json_response_error('Too many incorrect OTP attempts. Please request a new OTP', 400)

                return xink_json_response_error(f'Invalid OTP. Attempts left: {5 - new_fail_count}', 400)

            if fields.Datetime.now() > partner.xink_reset_otp_expiration:
                return xink_json_response_error('OTP expired', 400)

            # Transaction block
            with request.env.cr.savepoint():
                partner.sudo().write({
                    'xink_reset_otp': False,
                    'xink_reset_otp_expiration': False,
                    'xink_reset_otp_fail_count': 0
                })
                temp_password = xink_generate_password()
                user.sudo().write({'password': temp_password})

                subject = 'Xác nhận OTP reset mật khẩu'
                email_to = user.login
                body_html = f"""
                            <p>
                                Xác nhận OTP reset mật khẩu thành công
                            </p>
                            <p>
                                Mật khẩu mới của bạn là: <strong>{temp_password}</strong>
                            </p>
                            """

                request.env['xink.mail.sender'].sudo().xink_send_mail_direct(
                    subject=subject,
                    body_html=body_html,
                    email_to=email_to
                )

                return xink_json_response_ok('Confirm OTP reset password successfully')

        except Exception as e:
            request.env.cr.rollback()
            _logger.exception('Activate error: %s', str(e))
            return xink_json_response_error(f'Internal Server Error: {str(e)}', 500)

    @http.route('/api/user/change_password', type='http', auth='none', methods=['POST'], csrf=False)
    def change_password(self):
        try:
            # Check token
            res = xink_check_auth_and_company()
            if isinstance(res, Response):
                return res
            user, company_id = res
            if not company_id:
                return xink_json_response_error('Unauthorized', 401)

            # Parse request data
            try:
                data = json.loads(request.httprequest.data or '{}')
            except json.JSONDecodeError:
                return xink_json_response_error('Invalid JSON body', 400)

            old_password = data.get('oldPassword', '').strip()
            confirm_old_password = data.get('confirmOldPassword', '').strip()
            new_password = data.get('newPassword', '').strip()

            # Validate required fields
            if not all([old_password, confirm_old_password, new_password]):
                return xink_json_response_error('Missing required fields', 400)

            if old_password != confirm_old_password:
                return xink_json_response_error('Old password confirmation does not match', 400)

            if new_password == old_password:
                return xink_json_response_error("New password must be different from the old password", 400)

            # Get hashed password from DB
            request.env.cr.execute(
                "SELECT COALESCE(password, '') FROM res_users WHERE id = %s",
                [user.id]
            )
            result = request.env.cr.fetchone()
            if not result:
                return xink_json_response_error('User not found', 404)
            [hashed] = result

            # Compare password and update hash (if any)
            crypt = request.env['res.users']._crypt_context()
            is_valid, new_hash = crypt.verify_and_update(old_password, hashed)
            if not is_valid:
                return xink_json_response_error('Old password is incorrect', 401)

            # Change password
            user2 = request.env['res.users'].sudo().browse(user.id)
            user2.sudo().with_context(no_notify=True).write({'password': new_password})

            return xink_json_response_ok('Password changed successfully')

        except Exception as e:
            _logger.exception('Change password error: %s', str(e))
            return xink_json_response_error('Password changed failed', 500)

    @http.route('/api/user/invite_employee', type='http', auth='none', methods=['POST'], csrf=False)
    def invite_employee(self):
        try:
            # Check token
            res = xink_check_auth_and_company()
            if isinstance(res, Response):
                return res
            user, company_id = res
            if not company_id:
                return xink_json_response_error('Unauthorized', 401)

            roles = xink_get_roles_by_user(user)
            if not any(r.get('roleId') == 'group_xink_easy_checkin_admin' for r in roles):
                return xink_json_response_error('Not allowed to invite employees', 400)

            # Read input from JSON body
            try:
                data = json.loads(request.httprequest.data or '{}')
            except json.JSONDecodeError:
                return xink_json_response_error('Invalid JSON body', 500)

            employees_data = data.get('employees', [])
            if not isinstance(employees_data, list):
                return xink_json_response_error('Missing companyId or invalid data format', 400)

            # Get Permission
            res_group_employee = request.env.ref('xink_easy_checkin.group_xink_easy_checkin_employee',
                                                 raise_if_not_found=False)
            if not res_group_employee:
                return xink_json_response_error('Required groups (permission) not found', 500)

            created_employees = []
            failed_employees = []
            for email in employees_data:
                if not email:
                    continue

                existing_user = request.env['res.users'].with_context(active_test=False).sudo().search(
                    [('login', '=', email)], limit=1)
                if existing_user:
                    failed_employees.append({
                        'email': email,
                        'error': 'Can not have two users with the same login!'
                    })
                    continue

                try:
                    with request.env.cr.savepoint():

                        temp_password = xink_generate_password()
                        expire_days = 7

                        # Tạo người dùng (res.users)
                        user = request.env['res.users'].sudo().with_context(
                            no_reset_password=True,
                            tracking_disable=True,
                            mail_create_nosubscribe=True,
                            create_user=False
                        ).create({
                            'name': email,
                            'login': email,
                            'email': email,
                            'password': temp_password,
                            'company_id': company_id,
                            'company_ids': [(6, 0, [company_id])],
                            'groups_id': [(6, 0, [res_group_employee.id])],
                            'notification_type': 'email',
                            'active': True
                        })

                        user.partner_id.sudo().xink_generate_signup_token(expire_days * 24 * 60)  # ngày
                        user.partner_id.sudo().write({
                            'company_id': company_id,
                            'user_id': user.id,
                            'email': email,
                            'signup_type': 'api_register'
                        })
                        user.sudo().write({'active': False})

                        email_to = email
                        subject = 'Kích hoạt tài khoản'
                        safe_token = quote(user.partner_id.signup_token)
                        body_html = f"""
                                    <p>
                                        <a href="{xink_base_url()}/api/user/activate?token={safe_token}">
                                            Kích hoạt tài khoản
                                        </a>
                                    </p>
                                    <p>
                                        Liên kết này có hiệu lực trong <strong>{expire_days} ngày</strong>.
                                    </p>
                                    <p>
                                        Sau khi kích hoạt tài khoản thành công, bạn có thể đăng nhập bằng mật khẩu: <strong>{temp_password}</strong>
                                    </p>
                                    """

                        request.env['xink.mail.sender'].sudo().xink_send_mail_direct(
                            subject=subject,
                            body_html=body_html,
                            email_to=email_to
                        )

                        created_employees.append({
                            'user_id': user.id,
                            'email': user.email
                        })
                except Exception as ex:
                    _logger.warning(f"Failed to invite {email}: {str(ex)}")
                    failed_employees.append({
                        'email': email,
                        'error': str(ex)
                    })

            root_response = RootResponse(data={
                'success': created_employees,
                'failed': failed_employees
            })
            return xink_json_response_object(root_response.to_dict())

        except Exception as e:
            _logger.exception('Invite employee error: %s', str(e))
            return xink_json_response_error(f'Internal Server Error - Invite employee: {str(e)}', 500)

    @http.route('/api/user/search_invite', type='http', auth='none', methods=['POST'], csrf=False)
    def search_invite(self):
        try:
            # Check token
            res = xink_check_auth_and_company()
            if isinstance(res, Response):
                return res
            user, company_id = res
            if not company_id:
                return xink_json_response_error('Unauthorized', 401)

            # Read input from JSON body
            try:
                data = json.loads(request.httprequest.data or '{}')
            except json.JSONDecodeError:
                return xink_json_response_error('Invalid JSON body', 500)

            active = data.get('active', None)
            search = (data.get('search') or '').strip()
            page_index = int(data.get('pageIndex', 1))
            page_size = int(data.get('pageSize', 10))
            offset = (page_index - 1) * page_size

            # Get role
            employee_group = request.env.ref('xink_easy_checkin.group_xink_easy_checkin_employee')
            group_id = employee_group.id

            # Get all users of conpany and group
            domain = [('company_id', '=', int(company_id)), ('groups_id', 'in', [group_id])]
            if active is None:
                domain.append(('active', 'in', [True, False]))
            else:
                domain.append(('active', '=', bool(active)))
            # Search
            if search:
                domain += ['|', ('name', 'ilike', search), ('email', 'ilike', search)]

            matched_users = request.env['res.users'].with_context(active_test=False).sudo().search(domain, order='create_date desc')
            paginated_users = matched_users[offset:offset + page_size]
            # paginated_users.read(['image_1920'])

            paginated_result = []
            for user in paginated_users:
                paginated_result.append({
                    'id': user.id,
                    'name': user.name,
                    'login': user.login,
                    'email': user.email,
                    'active': user.active,
                    'company_id': user.company_id.id,
                    'company_name': user.company_id.name,
                    'imgAvatar': f'/web/image/res.users/{user.id}/image_1920' if user.image_1920 else None
                })

            # Pagination
            total_records = len(matched_users)
            total_pages = math.ceil(total_records / page_size) if page_size > 0 else 1

            root_response = RootResponse(data={
                'pageIndex': page_index,
                'pageSize': page_size,
                'totalPages': total_pages,
                'totalRecords': total_records,
                'results': paginated_result
            })
            return xink_json_response_object(root_response.to_dict())

        except Exception as e:
            _logger.exception('Invite employee error: %s', str(e))
            return xink_json_response_error(f'Internal Server Error - Invite employee: {str(e)}', 500)

    @http.route('/api/user/test_send_mail_2', type='http', auth='none', methods=['POST'], csrf=False)
    def test_send_mail_2(self):
        try:
            data = json.loads(request.httprequest.data or '{}')
            xink_request_env()
        except json.JSONDecodeError:
            return xink_json_response_error('Invalid JSON body', 400)

        template_xml_id = data.get('template_xml_id')
        email_to = data.get('email_to')
        try:
            res_id = int(data.get('res_id'))
        except (TypeError, ValueError):
            return xink_json_response_error('Invalid res_id (must be integer)', 400)

        try:
            user = request.env['res.users'].sudo().browse(res_id)
            api_url = xink_base_url()
            # email_from = config.get('email_from')
            ctx = {
                'api_url': api_url,
                'email_from': email_from,
                'lang': user.partner_id.lang or 'vi_VN',
                'tz': user.partner_id.tz or 'UTC',
            }
            template = request.env.ref(template_xml_id)
            body_html_dict = template.with_context(**ctx)._render_field('body_html', [user.id])
            body_html = body_html_dict.get(user.id)

            # mail_id = template.with_context(**ctx).send_mail(
            #     res_id=user.id,
            #     email_values={
            #         'email_from': email_from,
            #         'email_to': email_to
            #     },
            #     force_send=True,
            #     raise_exception=True
            # )
            return xink_json_response_object({'mail_id': 1})
        except Exception as e:
            return xink_json_response_error(str(e), 500)
