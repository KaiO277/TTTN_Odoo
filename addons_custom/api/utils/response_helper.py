from ..response.root_response import RootResponse
from odoo.http import Response
import json


def xink_json_response_object(data, status=200):
    return Response(
        json.dumps(data),
        status=status,
        content_type='application/json'
    )


def xink_json_response_ok(message, status=200):
    token_response = RootResponse(
        message=message
    )

    return Response(
        json.dumps(token_response.to_dict()),
        status=status,
        content_type='application/json'
    )


def xink_json_response_error(message, status=400):
    token_response = RootResponse(
        status="error",
        message=message
    )
    return Response(
        json.dumps(token_response.to_dict()),
        status=status,
        content_type='application/json'
    )


def xink_html_response_active_account(message, success = True):
    color = "green" if success else "red"
    return f"""
        <html>
            <head><title>easyCheckin - Account Activation</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h2 style="color: {color};">{message}</h2>
            </body>
        </html>
    """