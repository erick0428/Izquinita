import logging
from collections import defaultdict
from odoo import models, fields
from datetime import datetime
_logger = logging.getLogger(__name__)


class BusinessPerformanceSummary(models.TransientModel):
    _name = "tindahan.business_performance_summary"
    _description = "Business Performance Summary"

    start_date = fields.Date("Start Date", required=True, default=fields.Date.context_today)
    date_end = fields.Date("End Date", required=True, default=fields.Date.context_today)

    business_performance_summary_ids = fields.One2many(
        "tindahan.business_performance_summary_line",
        "wizard_id",
        string="Business Performance Summary",
    )





    def action_submit(self):
        self.ensure_one()

        # ---------------------------------------------------------
        # SALES
        # ---------------------------------------------------------
        sales_summary = self.env["tindahan.sales"].search([
            ("date", ">=", self.start_date),
            ("date", "<=", self.date_end),
        ])

        # ---------------------------------------------------------
        # EXPENSES
        # ---------------------------------------------------------
        expenses_summary = self.env["tindahan.expenses_item"].search([
            ("expenses_id.date", ">=", self.start_date),
            ("expenses_id.date", "<=", self.date_end),
        ])

        # ---------------------------------------------------------
        # LABOR / SALARY
        # ---------------------------------------------------------
        attendance_summary = self.env["tindahan.attendance_item"].search([
            ("attendance_id.date", ">=", self.start_date),
            ("attendance_id.date", "<=", self.date_end),
        ])

        # ---------------------------------------------------------
        # GROUP DATA BY DATE
        # ---------------------------------------------------------
        daily_data = defaultdict(lambda: {
            "sales": 0.0,
            "expenses": 0.0,
            "salary": 0.0,
        })

        # SALES
        for sale in sales_summary:
            daily_data[sale.date]["sales"] += sale.amount

        # EXPENSES
        for expense in expenses_summary:
            date = expense.expenses_id.date
            daily_data[date]["expenses"] += expense.amount

        # LABOR / SALARY
        for attendance in attendance_summary:
            date = attendance.attendance_id.date
            daily_data[date]["salary"] += attendance.amount

        # ---------------------------------------------------------
        # CREATE DAILY ROWS
        # ---------------------------------------------------------
        items = []

        grand_sales = 0.0
        grand_expenses = 0.0
        grand_salary = 0.0

        for date in sorted(daily_data):

            sales_amount = daily_data[date]["sales"]
            expenses_amount = daily_data[date]["expenses"]
            salary_amount = daily_data[date]["salary"]

            total_amount = (
                sales_amount
                - expenses_amount
                - salary_amount
            )

            grand_sales += sales_amount
            grand_expenses += expenses_amount
            grand_salary += salary_amount

            items.append((0, 0, {
                "date": date,
                "sales_amount": sales_amount,
                "expenses_amount": expenses_amount,
                "salary_amount": salary_amount,
                "total_amount": total_amount,
                "is_grand_total": False,
            }))

        # ---------------------------------------------------------
        # GRAND TOTAL
        # ---------------------------------------------------------
        grand_total = (
            grand_sales
            - grand_expenses
            - grand_salary
        )

        items.append((0, 0, {
            "date": False,
            "sales_amount": grand_sales,
            "expenses_amount": grand_expenses,
            "salary_amount": grand_salary,
            "total_amount": grand_total,
            "is_grand_total": True,
        }))

        # ---------------------------------------------------------
        # REPLACE EXISTING LINES
        # ---------------------------------------------------------
        self.business_performance_summary_ids = [(5, 0, 0)]
        self.business_performance_summary_ids = items

        return True




class BusinessPerformanceSummaryLine(models.TransientModel):
    _name = "tindahan.business_performance_summary_line"
    _description = "Business Performance Summary Line"

    wizard_id = fields.Many2one(
        "tindahan.business_performance_summary",
        string="Wizard",
        ondelete="cascade",
    )
    date = fields.Date("Date")
    sales_amount = fields.Float("Sales")
    expenses_amount = fields.Float("Expenses")
    salary_amount = fields.Float("Labor")
    total_amount = fields.Float("Business Performance")
    is_grand_total = fields.Boolean("Grand Total")

