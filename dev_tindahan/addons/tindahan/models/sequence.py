from odoo import models, fields

class Sequence(models.Model):
    _name = 'tindahan.sequence'
    _description = 'Sequence'
    
    name = fields.Char('Name')
    count = fields.Integer('Count')
    year = fields.Char('Year')