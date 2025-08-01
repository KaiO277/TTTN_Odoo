from datetime import datetime
import pytz
from odoo import fields


# 1: Trả về format ISO 8601 (giữ nguyên format gốc)
def xink_format_to_iso(dt, env):
    """Convert to ISO format with user timezone"""
    if not dt:
        return None

    # Convert sang timezone user
    local_dt = fields.Datetime.context_timestamp(env.user, dt)

    # Format thành ISO với timezone offset
    return local_dt.strftime('%Y-%m-%dT%H:%M:%S.000%z')


# 2: Trả về format ISO UTC
def xink_format_to_iso_utc(dt):
    """Convert to ISO UTC format"""
    if not dt:
        return None

    # Đảm bảo dt là UTC
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)

    utc_dt = dt.astimezone(pytz.UTC)
    return utc_dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')


# 3: Parse từ ISO string và convert
def xink_parse_iso_string(iso_string):
    """Parse ISO string như '2025-06-10T17:00:00.000Z'"""
    if not iso_string:
        return None

    # Remove 'Z' và parse
    dt_str = iso_string.replace('Z', '+00:00')
    dt = datetime.fromisoformat(dt_str)

    return dt


# 4: Trả về format dễ đọc cho user
def xink_format_for_display(dt, env):
    """Format for user display"""
    if not dt:
        return None

    local_dt = fields.Datetime.context_timestamp(env.user, dt)
    return local_dt.strftime('%d/%m/%Y %H:%M:%S')
