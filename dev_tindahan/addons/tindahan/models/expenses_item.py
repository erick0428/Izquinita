from odoo import models, fields,api
from odoo.exceptions import ValidationError

class ExpensesItem(models.Model):
    _name = 'tindahan.expenses_item'
    _description = 'Expenses Item'


    expenses_id = fields.Many2one(
        'tindahan.expenses',
        ondelete='cascade'
    )
   
    amount = fields.Float('Amount',required=True)
    item_model_id = fields.Many2one(
        'tindahan.item_model',
        required=True
    )
        
   
    