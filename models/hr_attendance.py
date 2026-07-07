from odoo import models, fields, api

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    in_latitude = fields.Float(string="In Latitude", digits=(10, 7), readonly=True)
    in_longitude = fields.Float(string="In Longitude", digits=(10, 7), readonly=True)
    out_latitude = fields.Float(string="Out Latitude", digits=(10, 7), readonly=True)
    out_longitude = fields.Float(string="Out Longitude", digits=(10, 7), readonly=True)
    
    in_address = fields.Char(string="In Address", readonly=True)
    out_address = fields.Char(string="Out Address", readonly=True)
