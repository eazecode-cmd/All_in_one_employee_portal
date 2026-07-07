from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Super bypass: domain is empty, check_company is False, and we use a permissive domain in XML
    user_id = fields.Many2one('res.users', string='Related User', domain="['|', ('active', '=', True), ('active', '=', False)]", check_company=False)

    grant_portal_access = fields.Boolean(string="Grant Portal Access", default=False)

    # Portal Tiles Access Control Fields
    portal_show_profile = fields.Boolean(string="Show Profile Tile", default=True)
    portal_show_attendance = fields.Boolean(string="Show Attendance Tile", default=True)
    portal_show_crm = fields.Boolean(string="Show CRM Tile", default=True)
    portal_show_sales = fields.Boolean(string="Show Sales Tile", default=True)
    portal_show_tasks = fields.Boolean(string="Show Tasks Tile", default=True)
    portal_show_timesheets = fields.Boolean(string="Show Timesheets Tile", default=True)
    portal_show_leaves = fields.Boolean(string="Show Time Off Tile", default=True)
    portal_show_payroll = fields.Boolean(string="Show Payroll Tile", default=True)
    portal_show_expenses = fields.Boolean(string="Show Expenses Tile", default=True)
    portal_show_schedule = fields.Boolean(string="Show Schedule Tile", default=True)
    portal_show_announcement = fields.Boolean(string="Show Announcement Tile", default=True)

    @api.model_create_multi
    def create(self, vals_list):
        employees = super().create(vals_list)
        for employee in employees:
            if employee.grant_portal_access and employee.work_email:
                employee._create_portal_user_auto()
        return employees

    def write(self, vals):
        res = super().write(vals)
        if 'grant_portal_access' in vals or 'work_email' in vals:
            for employee in self:
                if employee.grant_portal_access and employee.work_email:
                    employee._create_portal_user_auto()
        return res

    def _create_portal_user_auto(self):
        """ Automatically create and link a portal user if one doesn't exist for the email. """
        self.ensure_one()
        if not self.user_id:
            # Check if a user with this login already exists
            user = self.env['res.users'].sudo().search([('login', '=', self.work_email)], limit=1)
            if not user:
                # Create a new portal user
                portal_group = self.env.ref('base.group_portal')
                user = self.env['res.users'].sudo().create({
                    'name': self.name,
                    'login': self.work_email,
                    'email': self.work_email,
                    'groups_id': [(6, 0, [portal_group.id])],
                    'company_id': self.company_id.id,
                })
            # Link the user to the employee
            self.sudo().user_id = user.id

    def action_portal_attendance_toggle(self, latitude=None, longitude=None):
        """ Toggle attendance for the employee via portal with GPS coordinates. """
        self.ensure_one()
        action_date = fields.Datetime.now()
        
        if self.attendance_state != 'checked_in':
            # Check-in
            attendance = self.env['hr.attendance'].sudo().create({
                'employee_id': self.id,
                'check_in': action_date,
                'in_latitude': latitude,
                'in_longitude': longitude,
            })
            return attendance
        else:
            # Check-out
            attendance = self.env['hr.attendance'].sudo().search([
                ('employee_id', '=', self.id),
                ('check_out', '=', False)
            ], limit=1, order='check_in desc')
            if attendance:
                attendance.sudo().write({
                    'check_out': action_date,
                    'out_latitude': latitude,
                    'out_longitude': longitude,
                })
            return attendance

    def get_portal_dashboard_stats(self):
        """ Return stats for the portal dashboard tiles. """
        self.ensure_one()
        return {
            'attendance_status': 'checked_in' if self.attendance_state == 'checked_in' else 'checked_out',
            'leave_balance': self.show_leaves and self.allocation_count or 0,
            'upcoming_tasks': self.env['project.task'].search_count([('user_ids', 'in', self.user_id.id), ('state', 'not in', ['1_done', '1_canceled'])]),
        }
