from odoo import models, fields, api
from odoo.exceptions import ValidationError
from psycopg2 import OperationalError
import time


class POS(models.Model):
    _name = 'tindahan_pos.pos'
    _description = 'POS'
    _order = 'id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        default='New',
        copy=False
    )

    line_ids = fields.One2many(
        'tindahan_pos.pos.line',
        'pos_id',
        string='Order Lines'
    )

    total = fields.Float(
        string='Total',
        compute='_compute_total',
        store=True
    )

    @api.depends('line_ids.subtotal')
    def _compute_total(self):
        for record in self:
            record.total = sum(
                line.subtotal
                for line in record.line_ids
            )
    @api.model_create_multi
    def create(self, vals_list):
        for attempt in range(3):
            try:
                return super().create(vals_list)
            except OperationalError:
                if attempt == 2:
                    raise
                time.sleep(0.2) 

class POSLine(models.Model):
    _name = 'tindahan_pos.pos.line'
    _description = 'POS Order Line'

    pos_id = fields.Many2one(
        'tindahan_pos.pos',
        string='POS',
        required=True,
        ondelete='cascade'
    )

    product_id = fields.Many2one(
        'tindahan_pos.product',
        string='Product',
        required=True
    )

    variant_id = fields.Many2one(
        related='product_id.variant_id',
        string='Variant',
        store=True,
        readonly=True
    )

    quantity = fields.Float(
        string='Quantity',
        required=True,
        default=1.0
    )

    price = fields.Float(
        string='Price',
        related='product_id.srp',
        store=True,
        readonly=True
    )

    subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_subtotal',
        store=True
    )

    @api.depends('quantity', 'price')
    def _compute_subtotal(self):
        for record in self:
            record.subtotal = record.quantity * record.price

    @api.constrains('quantity')
    def _check_quantity(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(
                    'Quantity must be greater than zero.'
                )
                
                               