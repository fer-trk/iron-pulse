from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.db.session import get_session
from app.schemas.report import IncomeReport
from app.services.report_service import get_income_report

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/income", response_model=IncomeReport)
def income(start_date: Optional[date] = None, end_date: Optional[date] = None,
           session: Session = Depends(get_session)):
    return get_income_report(session, start_date, end_date)
