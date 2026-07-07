# -*- coding: utf-8 -*-
from odoo import models, fields

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    user_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        default=lambda self: self.env.user,
        domain="['|', ('share', '=', False), ('share', '=', True)]"
    )
