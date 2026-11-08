from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class IncomeReport(BaseModel):
    start_date: date
    end_date: date
    total_income: Decimal
    total_payments: int
