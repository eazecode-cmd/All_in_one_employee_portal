from odoo import models, fields, api

class ProjectTask(models.Model):
    _inherit = 'project.task'

    # New field to link directly to hr.employee
    employee_id = fields.Many2one('hr.employee', string='Assigned Employee', tracking=True)
    
    # We'll keep the user_ids fix as well just in case, but employee_id will be our primary portal link
    user_ids = fields.Many2many('res.users', string='Assignees', 
                                domain="['|', ('share', '=', False), ('groups_id', 'in', [7])]",
                                help="The internal or portal users assigned to this task.")
    # Task start tracking for portal
    is_task_started = fields.Boolean(string='Is Started', default=False, tracking=True)
    task_start_time = fields.Datetime(string='Start Time', tracking=True)
