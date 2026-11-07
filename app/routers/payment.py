import csv
import io
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session
from ..db.session import get_session
from ..core.security import get_current_user_sub
from ..services.payment import PaymentService
from ..schemas.payment import PaymentCreate, PaymentRead, PaymentUpdate
from datetime import date

router = APIRouter(prefix="/payments", tags=["payments"])
auth = Depends(get_current_user_sub)


@router.get("/", response_model=list[PaymentRead], summary="List payments")
def list_payments(status=None, method=None, membership_id=None, skip: int = 0,
                  limit: int = Query(20, le=100), session: Session = Depends(get_session), _=auth):
    return PaymentService.get_all(session, status=status, method=method,
                                  membership_id=membership_id, skip=skip, limit=limit)


@router.post("/", response_model=PaymentRead, status_code=201, summary="Register payment")
def create(data: PaymentCreate, session: Session = Depends(get_session), _=auth):
    return PaymentService.create(session, data)


@router.get("/export-csv", summary="Export payment history to CSV")
def export_csv(session: Session = Depends(get_session), _=auth):
    rows = PaymentService.export_csv(session)
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "id", "member", "plan", "amount", "payment_method", "status", "reference", "payment_date"
    ])
    writer.writeheader()
    writer.writerows(rows)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=payments_{date.today()}.csv"},
    )


@router.get("/{payment_id}", response_model=PaymentRead, summary="Payment detail")
def detail(payment_id: int, session: Session = Depends(get_session), _=auth):
    return PaymentService.get_by_id(session, payment_id)


@router.patch("/{payment_id}", response_model=PaymentRead, summary="Update payment status")
def update(payment_id: int, data: PaymentUpdate,
           session: Session = Depends(get_session), _=auth):
    return PaymentService.update(session, payment_id, data)


@router.delete("/{payment_id}", status_code=204, summary="Delete payment")
def delete(payment_id: int, session: Session = Depends(get_session), _=auth):
    PaymentService.delete(session, payment_id)