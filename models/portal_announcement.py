from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PortalAnnouncement(models.Model):
    _name = 'portal.announcement'
    _description = 'Portal Announcement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_published desc, id desc'
    _mail_post_access = 'read'

    name = fields.Char(string='Title', required=True, tracking=True)
    summary = fields.Text(string='Summary', help='A short text shown on the announcement list card.')
    content = fields.Html(string='Content', required=True, sanitize=True, strip_style=False)
    date_published = fields.Datetime(string='Publish Date', default=fields.Datetime.now, required=True, tracking=True)
    date_expiry = fields.Datetime(string='Expiry Date', tracking=True)
    image = fields.Binary(string='Banner Image')
    is_published = fields.Boolean(string='Published', default=True, tracking=True)
    all_employees = fields.Boolean(string='All Employees', default=True, tracking=True,
                                    help='If checked, visible to all employees. Otherwise, specify targeted employees.')
    employee_ids = fields.Many2many('hr.employee', 'portal_announcement_employee_rel', 'announcement_id', 'employee_id',
                                    string='Specific Employees', help='Visible only to the selected employees.')
    read_employee_ids = fields.Many2many('hr.employee', 'portal_announcement_read_rel', 'announcement_id', 'employee_id',
                                         string='Read By Employees')

    @api.model
    def get_active_announcements(self, employee_id=False):
        """ Fetch active announcements based on specific employee & date filters """
        now = fields.Datetime.now()
        domain = [
            ('is_published', '=', True),
            ('date_published', '<=', now),
            '|',
            ('date_expiry', '=', False),
            ('date_expiry', '>', now)
        ]
        
        if employee_id:
            domain.append('|')
            domain.append(('all_employees', '=', True))
            domain.append(('employee_ids', 'in', employee_id))
        else:
            domain.append(('all_employees', '=', True))

        return self.search(domain)
