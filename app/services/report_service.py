from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlmodel import Session, select
from app.models.payment import Payment, PaymentStatus
from app.schemas.report import IncomeReport


def _validate_date_range(
    start_date: Optional[date],
    end_date: Optional[date],
) -> tuple[date, date]:
    today = date.today()

    if start_date is None:
        start_date = today

    if end_date is None:
        end_date = today

    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be greater than end_date",
        )

    return start_date, end_date


def _date_range_to_datetimes(
    start_date: date,
    end_date: date,
) -> tuple[datetime, datetime]:
    start_datetime = datetime.combine(
        start_date,
        time.min,
        tzinfo=timezone.utc,
    )
    end_datetime = datetime.combine(
        end_date,
        time.max,
        tzinfo=timezone.utc,
    )

    return start_datetime, end_datetime


def get_income_report(
    session: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> IncomeReport:
    start_date, end_date = _validate_date_range(start_date, end_date)
    start_datetime, end_datetime = _date_range_to_datetimes(start_date, end_date)

    statement = select(
        func.coalesce(func.sum(Payment.amount), 0),
        func.count(Payment.id),
    ).where(
        Payment.payment_date >= start_datetime,
        Payment.payment_date <= end_datetime,
        Payment.status == PaymentStatus.completed,
    )

    total_income, total_payments = session.exec(statement).one()

    return IncomeReport(
        start_date=start_date,
        end_date=end_date,
        total_income=Decimal(total_income),
        total_payments=total_payments,
    )