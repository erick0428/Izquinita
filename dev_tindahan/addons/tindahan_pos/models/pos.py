from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from psycopg2 import OperationalError
import time
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


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

    customer_name = fields.Char(
        string="Customer"
    )

    session_id = fields.Many2one(
        'tindahan_pos.session',
        string='Session',
        required=True
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

    cash = fields.Float(
        string='Cash',
        default=0.0
    )

    change = fields.Float(
        string='Change',
        default=0.0
    )

    # =====================================================
    # PAYMENT
    # =====================================================

    payment_status = fields.Selection(
        [
            ('unpaid', 'Unpaid'),
            ('paid', 'Paid'),
        ],
        string='Payment Status',
        default='unpaid',
        required=True,
        copy=False
    )

    paid_at = fields.Datetime(
        string='Paid At',
        readonly=True,
        copy=False
    )

    # =====================================================
    # KITCHEN
    # =====================================================

    kitchen_status = fields.Selection(
        [
            ('new', 'New'),
            ('preparing', 'Preparing'),
            ('ready', 'Ready'),
            ('completed', 'Completed'),
        ],
        string='Kitchen Status',
        default='new',
        required=True,
        copy=False
    )

    @api.depends('line_ids.subtotal')
    def _compute_total(self):
        for record in self:
            record.total = sum(
                line.subtotal
                for line in record.line_ids
            )

    # =====================================================
    # GENERATE ORDER NUMBER
    # =====================================================

    def _generate_name(self):
        user = self.env.user
        today = datetime.now().date()

        sequence = self.env["tindahan_pos.sequence"].search([
            ("name", "=", "Sales"),
            ("user_id", "=", user.id),
        ], limit=1)

        if not sequence:
            sequence = self.env["tindahan_pos.sequence"].create({
                "name": "Sales",
                "user_id": user.id,
                "date": today,
                "count": 0,
            })

        if sequence.date != today:
            sequence.date = today
            sequence.count = 0

        while True:
            sequence.count += 1

            name = (
                f"{datetime.now().strftime('%y%m%d')}-"
                f"{user.id}-"
                f"{str(sequence.count).zfill(5)}"
            )

            if not self.search([('name', '=', name)]):
                break

        return name

    # =====================================================
    # CREATE
    # =====================================================

    @api.model_create_multi
    def create(self, vals_list):

        for attempt in range(3):
            try:

                session = self.env[
                    'tindahan_pos.session'
                ].search(
                    [('state', '=', 'open')],
                    limit=1
                )

                if not session:
                    raise ValidationError(
                        "No open session. Please open POS first."
                    )

                for vals in vals_list:
                    vals['session_id'] = session.id
                    vals['name'] = self._generate_name()

                return super().create(vals_list)

            except OperationalError:

                if attempt == 2:
                    raise

                time.sleep(0.2)

    # =====================================================
    # CREATE + PAY ORDER
    # =====================================================

    @api.model
    def create_pos_order(self, vals):

        cash = float(vals.get('cash', 0.0))
        change = float(vals.get('change', 0.0))

        vals.pop('cash', None)
        vals.pop('change', None)
        vals["kitchen_status"] = "new"
        order = self.create(vals)

        if cash < order.total:
            raise UserError(
                f"Insufficient cash. "
                f"Total is ₱{order.total:.2f}."
            )

        order.write({
            'cash': cash,
            'change': change,
            'payment_status': 'paid',
            'paid_at': fields.Datetime.now(),
            'kitchen_status': 'new',
        })

        return {
            'id': order.id,
            'name': order.name,
            'customer_name': order.customer_name,
            'total': order.total,
            'cash': order.cash,
            'change': order.change,
            'payment_status': order.payment_status,
            'kitchen_status': order.kitchen_status,

            'items': [
                {
                    'product_id': line.product_id.id,
                    'name': line.product_description,
                    'quantity': line.quantity,
                }
                for line in order.line_ids
            ],
        }

    # =====================================================
    # GET KITCHEN ORDERS
    # =====================================================

    @api.model
    def get_kitchen_orders(self):

        orders = self.search(
            [
                ('kitchen_status', '!=', 'completed'),
            ],
            order='id desc'
        )

        _logger.warning(
            "KITCHEN: Found %s orders",
            len(orders)
        )

        for order in orders:
            _logger.warning(
                "KITCHEN ORDER: %s | payment=%s | kitchen=%s",
                order.name,
                order.payment_status,
                order.kitchen_status
            )

        result = []

        for order in orders:

            result.append({
                'id': order.id,
                'name': order.name,
                'customer_name': (
                    order.customer_name or
                    'Walk-in Customer'
                ),
                'total': order.total,
                'payment_status': order.payment_status,
                'kitchen_status': order.kitchen_status,

                'paid_at': (
                    order.paid_at.isoformat()
                    if order.paid_at
                    else None
                ),

                'items': [
                    {
                        'product_id': line.product_id.id,
                        'name': line.product_description,
                        'quantity': line.quantity,
                    }
                    for line in order.line_ids
                ],
            })

        return result


    # =====================================================
    # KITCHEN - START
    # =====================================================

    def action_start_preparing(self):

        for order in self:

            if order.payment_status != 'paid':
                raise UserError(
                    "Only paid orders can be prepared."
                )

            order.kitchen_status = 'preparing'

        return True

    # =====================================================
    # KITCHEN - READY
    # =====================================================

    def action_mark_ready(self):

        for order in self:
            order.kitchen_status = 'ready'

        return True

    # =====================================================
    # KITCHEN - COMPLETE
    # =====================================================

    def action_complete(self):

        for order in self:
            order.kitchen_status = 'completed'

        return True

    # =====================================================
    # RECEIPT
    # =====================================================

    def action_print_receipt(self):
        self.ensure_one()

        return self.env.ref(
            'tindahan_pos.action_report_pos_receipt'
        ).report_action(self)


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
        string='Code',
        required=True
    )

    product_description = fields.Char(
        related='product_id.description',
        string='Name',
        store=True
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
