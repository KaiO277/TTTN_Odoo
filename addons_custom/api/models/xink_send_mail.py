import logging

from odoo import models, api

_logger = logging.getLogger(__name__)


class MailSender(models.AbstractModel):
    _name = 'xink.mail.sender'
    _description = 'Custom send mail by Xink'

    @api.model
    def xink_send_mail_by_template(self, template_xml_id, record, ctx=None, email_to=None, force_send=True):
        """
        Send email using a custom XML template for any model, with a record passed from outside.

        :param template_xml_id: XML ID of the email template (e.g., 'your_module_name.xink_mail_template_user_activate')
        :param record: Odoo record object (e.g., a res.users or sale.order record)
        :param ctx: Custom context (default: None)
        :param email_to: Recipient email address (optional, overrides template's email_to)
        :param force_send: Send email immediately if True (default: True)
        :return: True if email is sent successfully, otherwise raises an error
        """
        # Initialize context if not provided
        ctx = ctx or {}

        # Retrieve email template
        try:
            template = self.env.ref(template_xml_id)
        except Exception:
            raise ValueError(f"Template with XML ID {template_xml_id} not found.")

        # Validate record
        if not record or not hasattr(record, '_name') or not record.exists():
            raise ValueError("Invalid or non-existent record provided.")

        # Check if template is associated with the record's model
        if template.model_id.model != record._name:
            raise ValueError(f"Template {template_xml_id} is not associated with model {record._name}.")

        # Check recipient email
        email_field = getattr(record, 'email', None) or getattr(record, 'partner_id', None) and record.partner_id.email
        if not email_to and not email_field:
            raise ValueError(f"Record {record._name} with ID {record.id} has no recipient email.")

        # Override recipient email if provided
        if email_to:
            ctx['email_to'] = email_to

        # Send email
        try:
            return template.with_context(**ctx).send_mail(record.id, force_send=force_send)
        except Exception as e:
            raise ValueError(f"Error sending email: {str(e)}")

    @api.model
    def xink_send_mail_direct(self, subject, body_html, email_to, email_from=None, force_send=True):
        """
        Send mail directly without template.

        :param subject: str
        :param body_html: str
        :param email_from: str
        :param email_to: str
        :param force_send: bool
        """
        if not email_from:
            mail_server = self.env['ir.mail_server'].search([('active', '=', True)], limit=1)
            email_from = mail_server.smtp_user if mail_server else 'system@ixink.vn'

        mail = self.env['mail.mail'].create(
            {
                'subject': subject,
                'body_html': body_html,
                'email_from': email_from,
                'email_to': email_to,
            }
        )

        if force_send:
            mail.send()
        return mail.id
