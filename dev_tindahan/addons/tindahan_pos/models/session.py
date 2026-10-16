
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class POSSession(models.Model):
    _name = 'tindahan_pos.session'
    _description = 'POS Session'
    _order = 'id desc'

    # --------------------------------------------------
    # SESSION INFORMATION
    # --------------------------------------------------

    name = fields.Char(
        string='Session Reference',
        default='New',
        required=True,
        readonly=True,
        copy=False,
    )

    state = fields.Selection(
        [
            ('open', 'Open'),
            ('closed', 'Closed'),
        ],
        string='Status',
        default='open',
        required=True,
    )

    date = fields.Datetime(
        string='Date',
        readonly=True,
        default=fields.Datetime.now,
        copy=False,
    )

    # --------------------------------------------------
    # CASH MANAGEMENT
    # --------------------------------------------------

    opening_cash = fields.Float(
        string='Opening Cash',
        default=0.0,
    )

    closing_cash = fields.Float(
        string='Expected Closing Cash',
        readonly=True,
        copy=False,
    )

    closing_input = fields.Float(
        string='Actual Cash Counted',
        default=0.0,
    )

    difference = fields.Float(
        string='Cash Difference',
        compute='_compute_difference',
        store=True,
    )

    # --------------------------------------------------
    # POS ORDERS
    # --------------------------------------------------

    pos_ids = fields.One2many(
        'tindahan_pos.pos',
        'session_id',
        string='Orders',
    )

    # --------------------------------------------------
    # COMPUTED TOTALS
    # --------------------------------------------------

    total_sales = fields.Float(
        string='Total Sales',
        compute='_compute_total_sales',
       
    )

    total_cash = fields.Float(
        string='Total Cash',
        compute='_compute_total_cash',
      
    )

    total_gcash = fields.Float(
        string='Total GCash',
        compute='_compute_total_gcash',
       
    )

    total_df = fields.Float(
        string='Total Delivery Fee',
        compute='_compute_total_df',
      
    )

    # --------------------------------------------------
    # SESSION SEQUENCE
    # --------------------------------------------------

    def _generate_name(self):
        user = self.env.user
        today = fields.Date.today()

        sequence = self.env['tindahan_pos.sequence'].search(
            [
                ('name', '=', 'Session'),
                ('user_id', '=', user.id),
            ],
            limit=1,
        )

        if not sequence:
            sequence = self.env['tindahan_pos.sequence'].create({
                'name': 'Session',
                'user_id': user.id,
                'date': today,
                'count': 0,
            })

        # Reset the counter every day.
        if sequence.date != today:
            sequence.write({
                'date': today,
                'count': 0,
            })

        sequence.count += 1

        return (
            f'{today.strftime("%y%m%d")}-'
            f'{user.id}-'
            f'{sequence.count:03d}'
        )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self._generate_name()

        return super().create(vals_list)

    # --------------------------------------------------
    # TOTAL SALES
    # Includes all POS orders, regardless of payment status.
    # --------------------------------------------------

    @api.depends('pos_ids', 'pos_ids.total')
    def _compute_total_sales(self):
        for rec in self:
            rec.total_sales = sum(rec.pos_ids.mapped('total'))

    # --------------------------------------------------
    # TOTAL CASH
    # Includes paid cash transactions only.
    # --------------------------------------------------

    @api.depends(
        'pos_ids',
        'pos_ids.total',
        'pos_ids.payment_type',
        'pos_ids.payment_status',
    )
    def _compute_total_cash(self):
        for rec in self:
            rec.total_cash = sum(
                order.total
                for order in rec.pos_ids
                if order.payment_type == 'cash'
                and order.payment_status == 'paid'
            )

    # --------------------------------------------------
    # TOTAL GCASH
    # Includes paid GCash transactions only.
    # --------------------------------------------------

    @api.depends(
        'pos_ids',
        'pos_ids.total',
        'pos_ids.payment_type',
        'pos_ids.payment_status',
    )
    def _compute_total_gcash(self):
        for rec in self:
            rec.total_gcash = sum(
                order.total
                for order in rec.pos_ids
                if order.payment_type == 'gcash'
                and order.payment_status == 'paid'
            )

    # --------------------------------------------------
    # TOTAL DELIVERY FEES
    # --------------------------------------------------

    @api.depends('pos_ids', 'pos_ids.delivery_fee')
    def _compute_total_df(self):
        for rec in self:
            rec.total_df = sum(rec.pos_ids.mapped('delivery_fee'))

    # --------------------------------------------------
    # CASH DIFFERENCE
    # --------------------------------------------------

    @api.depends(
        'closing_input',
        'opening_cash',
        'total_cash',
    )
    def _compute_difference(self):
        for rec in self:
            expected_cash = rec.opening_cash + rec.total_cash
            rec.difference = rec.closing_input - expected_cash

    # --------------------------------------------------
    # SESSION REPORT
    # --------------------------------------------------

    def get_report_data(self):
        self.ensure_one()

        expected_cash = self.opening_cash + self.total_cash

        return {
            'name': self.name,
            'total_orders': len(self.pos_ids),
            'total_sales': self.total_sales,
            'total_cash': self.total_cash,
            'total_gcash': self.total_gcash,
            'total_df': self.total_df,
            'opening_cash': self.opening_cash,
            'expected_cash': expected_cash,
            'closing_cash': self.closing_cash,
            'closing_input': self.closing_input,
            'difference': self.difference,
        }

    # --------------------------------------------------
    # CLOSE SESSION
    # --------------------------------------------------

    def close_session(self, actual_cash):
        self.ensure_one()

        if self.state != 'open':
            raise ValidationError(
                'Only an open session can be closed.'
            )

        expected_cash = self.opening_cash + self.total_cash
        difference = actual_cash - expected_cash

        self.write({
            'closing_cash': expected_cash,
            'closing_input': actual_cash,
            'state': 'closed',
        })

        return {
            'opening_cash': self.opening_cash,
            'total_sales': self.total_sales,
            'total_cash': self.total_cash,
            'total_gcash': self.total_gcash,
            'total_df': self.total_df,
            'expected_cash': expected_cash,
            'closing_input': actual_cash,
            'difference': difference,
        }
