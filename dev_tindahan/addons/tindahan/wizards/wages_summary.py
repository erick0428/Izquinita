import logging
from collections import defaultdict

from odoo import models, fields

_logger = logging.getLogger(__name__)


class WagesSummary(models.TransientModel):
    _name = "tindahan.wages_summary"
    _description = "Wages Summary"

    start_date = fields.Date(
        "Start Date",
        required=True,
        default=fields.Date.context_today,
    )

    date_end = fields.Date(
        "End Date",
        required=True,
        default=fields.Date.context_today,
    )

    wages_summary_ids = fields.One2many(
        "tindahan.wages_summary_line",
        "wizard_id",
        string="Wages Summary",
    )
    employee_id = fields.Many2one(
        "tindahan.employee",
        string="Employee Name",
    )

    def action_submit(self):
        self.ensure_one()
        
        # ---------------------------------------------------------
        # Get attendance records within selected date range
        # ---------------------------------------------------------
        domain = [ ("attendance_id.date", ">=", self.start_date),
                    ("attendance_id.date", "<=", self.date_end),]
        
        if self.employee_id:
            domain.append(('employee_id', '=', self.employee_id.id))
            
        attendance_records = self.env["tindahan.attendance_item"].search(domain)

        # ---------------------------------------------------------
        # Group by employee and date
        # ---------------------------------------------------------
        employee_data = defaultdict(
            lambda: defaultdict(
                lambda: {
                    "paid": 0.0,
                    "not_paid": 0.0,
                }
            )
        )

        for attendance in attendance_records:

            employee = attendance.employee_id

            if not employee:
                continue

            date = attendance.attendance_id.date
            amount = attendance.amount or 0.0

            if attendance.status == "paid":
                employee_data[employee.id][date]["paid"] += amount
            else:
                employee_data[employee.id][date]["not_paid"] += amount

        # ---------------------------------------------------------
        # Prepare summary lines
        # ---------------------------------------------------------
        items = []

        for employee_id, dates in employee_data.items():

            employee_total_paid = 0.0
            employee_total_unpaid = 0.0

            # Daily lines
            for date in sorted(dates.keys()):

                data = dates[date]

                total = data["paid"] + data["not_paid"]

                items.append((0, 0, {
                    "employee_id": employee_id,
                    "display_name": employee.name,
                    "date": date,
                    "amount_paid": data["paid"],
                    "amount_not_paid": data["not_paid"],
                    "salary_amount": total,
                    "total_amount": total,
                }))

                employee_total_paid += data["paid"]
                employee_total_unpaid += data["not_paid"]

            # Employee total
            employee_total = (
                employee_total_paid +
                employee_total_unpaid
            )

            items.append((0, 0, {
                "display_name": "GRAND TOTAL",
                "date": self.date_end,
                "amount_paid": employee_total_paid,
                "amount_not_paid": employee_total_unpaid,
                "salary_amount": employee_total,
                "total_amount": employee_total,
                "is_employee_total": True,
            }))

        self.wages_summary_ids = [(5, 0, 0)] + items

        return True




class WagesSummaryLine(models.TransientModel):
    _name = "tindahan.wages_summary_line"
    _description = "Wages Summary Line"

    wizard_id = fields.Many2one(
        "tindahan.wages_summary",
        string="Wizard",
        ondelete="cascade",
    )

    date = fields.Date("Date")

    employee_id = fields.Many2one(
        "tindahan.employee",
        string="Employee Name",
    )
    display_name = fields.Char(
        "Employee",
    )
    amount_paid = fields.Float("Amount Paid")

    amount_not_paid = fields.Float("Amount Unpaid")

    salary_amount = fields.Float("Labor")

    total_amount = fields.Float("Total Amount")

    # Employee subtotal
    is_employee_total = fields.Boolean(
        "Employee Total",
    )

    # # Overall grand total
    # is_grand_total = fields.Boolean(
    #     "Grand Total",
    # )

