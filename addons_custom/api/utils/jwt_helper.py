import datetime
import uuid
import jwt
import logging
import secrets
import random
import string

from werkzeug.exceptions import NotFound

from odoo.exceptions import AccessDenied
from odoo.http import request

from .redis_helper import *
from ..utils.response_helper import *
from ..response.root_response import RootResponse
from ..response.token_content_response import TokenContentResponse
from ..response.user_info_response import UserInfoResponse

_logger = logging.getLogger(__name__)

SECRET_KEY = config.get(
    'jwt_secret_key') or 'TtWZNGNNq0zXLn_8cyCM1kM9IRZcQUy12OSOt1bgj05Qw-lLq5Bev7z8nW2kXbl4hAJn6AyZ6IMaNHTnObeL3g'
ALGORITHM = config.get('algorithm') or 'HS512'
EXPIRES_IN_ACCESS_TOKEN = int(config.get('jwt_expires_in_access_token') or 900)  # 15 phút
EXPIRES_IN_REFRESH_TOKEN = int(config.get('jwt_expires_in_refresh_token') or 604800)  # 7 ngày


def xink_encode_token(payload, secret=SECRET_KEY, algorithm=ALGORITHM):
    return jwt.encode(payload, secret, algorithm=algorithm)


def xink_decode_token(token, secret=SECRET_KEY, algorithms=ALGORITHM):
    return jwt.decode(token, secret, algorithms=algorithms)


def xink_generate_access_token(user, latest_inout_info):
    roles = xink_get_roles_by_user(user)

    payload = {
        'uid': user.id,
        'type': 'access',
        'login': user.login,
        'name': user.name,
        'email': user.email,
        'roles': roles,
        'exp': datetime.datetime.now() + datetime.timedelta(seconds=EXPIRES_IN_ACCESS_TOKEN),
        'iat': datetime.datetime.now(),
        'company_id': user.company_id.id
    }

    access_token = xink_encode_token(payload)

    refresh_token = xink_generate_refresh_token(user.id)

    user_info = UserInfoResponse(
        id=user.id,
        name=user.name,
        username=user.login,
        email=user.email,
        roles=roles,
        latestStatusInOut=latest_inout_info['check_type'],
        latestCheckInTime=latest_inout_info['check_in_time'],
        latestCheckOutTime=latest_inout_info['check_out_time'],
        companyId=user.company_id.id
    )

    token_content = TokenContentResponse(
        accessToken=access_token,
        refreshToken=refresh_token,
        expiresIn=EXPIRES_IN_ACCESS_TOKEN,
        user=user_info
    )

    root_response = RootResponse(data=token_content)
    return root_response.to_dict()


def xink_generate_refresh_token(user_id):
    payload = {
        'uid': user_id,
        'type': 'refresh',
        'jti': str(uuid.uuid4()),
        'exp': datetime.datetime.now() + datetime.timedelta(seconds=EXPIRES_IN_REFRESH_TOKEN),
        'iat': datetime.datetime.now()
    }
    refresh_token = xink_encode_token(payload)
    return refresh_token


def xink_blacklist_token(jti: str, exp: int):
    ttl = exp - int(datetime.datetime.now().timestamp())
    if ttl > 0:
        redis_client = xink_redis_client()
        redis_client.setex(f"blacklist:{jti}", ttl, 'true')


def xink_is_token_blacklisted(jti: str) -> bool:
    redis_client = xink_redis_client()
    return redis_client.exists(f"blacklist:{jti}")


def xink_extract_authorization():
    authorization = request.httprequest.headers.get('Authorization')
    if not authorization or not authorization.startswith("Bearer "):
        raise AccessDenied("Missing or invalid Authorization header")

    return authorization.split("Bearer ")[1].strip()


def xink_extract_info_from_token():
    token = xink_extract_authorization()
    try:
        payload = xink_decode_token(token)
    except jwt.ExpiredSignatureError:
        raise AccessDenied("Token expired")
    except jwt.InvalidTokenError:
        raise AccessDenied("Invalid token")

    user_id = payload.get('uid')
    if not user_id:
        raise AccessDenied("Invalid token payload: missing 'uid'")

    return {
        "user_id": int(user_id),
        "username": payload.get('login'),
        "company_id": int(payload.get('company_id')) if payload.get('company_id') else None
    }


def xink_extract_user_from_token():
    info = xink_extract_info_from_token()
    user = request.env['res.users'].browse(info['user_id'])
    xink_request_env(user)
    if not user.exists():
        raise NotFound("User not found")
    return user.sudo(), info


def xink_check_auth_and_company():
    try:
        user, info = xink_extract_user_from_token()
        return user, info['company_id']
    except NotFound as e:
        return xink_json_response_error(str(e), 404)
    except AccessDenied as e:
        return xink_json_response_error(str(e), 401)
    except Exception as e:
        return xink_json_response_error(str(e), 500)


def xink_current_employee():
    try:
        user, info = xink_extract_user_from_token()
        request.env.cr.execute("""SELECT id FROM hr_employee WHERE user_id = %s AND company_id = %s LIMIT 1""",
                               (user.id, user.company_id.id))
        row = request.env.cr.fetchone()
        if not row:
            return {"status_code": 404, "message": "No employee linked to this user."}

        employee_id = row[0]
        employee = request.env['hr.employee'].sudo().browse(employee_id)

        return {
            "status_code": 200,
            "employee": employee,
            "employee_id": employee_id,
            "user_id": user.id,
            "company_id": info['company_id']
        }

    except AccessDenied as e:
        return {"status_code": 401, "message": str(e)}
    except Exception as e:
        return {"status_code": 500, "message": str(e)}


def xink_request_env(user=None):
    # Set request.env
    if user:
        request.env = request.env(user=user)
    else:
        env_user = request.env['res.users'].sudo().search([('login', 'in', ['admin', 'hi@ixink.vn'])], limit=1)
        if env_user:
            request.env = request.env(user=env_user)


def xink_base_url():
    return request.env['ir.config_parameter'].sudo().get_param('web.base.url')


def xink_generate_password(length=8):
    if length < 6:
        raise ValueError("Password length must be at least 6 characters")

    # Các nhóm ký tự
    lowercase = string.ascii_lowercase
    uppercase = string.ascii_uppercase
    digits = string.digits
    special = "@#$"

    # Bắt buộc 1 ký tự từ mỗi nhóm
    password_chars = [
        secrets.choice(lowercase),
        secrets.choice(uppercase),
        secrets.choice(digits),
        secrets.choice(special)
    ]

    # Phần còn lại: chọn ngẫu nhiên từ tất cả các nhóm
    all_chars = lowercase + uppercase + digits + special
    remaining_length = length - len(password_chars)
    password_chars += [secrets.choice(all_chars) for _ in range(remaining_length)]

    # Xáo trộn thứ tự để ngẫu nhiên
    random.shuffle(password_chars)

    return ''.join(password_chars)


def xink_get_roles_by_user(user):
    xink_request_env()
    roles = []
    for group in user.groups_id:
        data = request.env['ir.model.data'].search([
            ('model', '=', 'res.groups'),
            ('res_id', '=', group.id)
        ], limit=1)
        roles.append({
            "roleId": data.name if data else f"xink_group_{group.id}",
            "roleName": group.name
        })
    return roles
