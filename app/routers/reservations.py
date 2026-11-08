from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from app.db.session import get_session
from app.schemas.reservation import ReservationCreate, ReservationRead
from app.services import reservation as service

router = APIRouter(prefix="/reservations", tags=["Class enrollments"])


@router.post("/", response_model=ReservationRead, status_code=201)
def enroll(data: ReservationCreate, session: Session = Depends(get_session)):
    return service.create_reservation(session, data)


@router.get("/", response_model=list[ReservationRead])
def list_enrollments(member_id: Optional[int] = None, shift_id: Optional[int] = None,
                     day: Optional[date] = None, skip: int = Query(0, ge=0),
                     limit: int = Query(100, ge=1, le=100), session: Session = Depends(get_session)):
    return service.get_reservations(session, member_id, shift_id, day, skip, limit)


@router.get("/{reservation_id}", response_model=ReservationRead)
def detail(reservation_id: int, session: Session = Depends(get_session)):
    return service.get_reservation(session, reservation_id)


@router.patch("/{reservation_id}/cancel", response_model=ReservationRead)
def cancel(reservation_id: int, session: Session = Depends(get_session)):
    return service.cancel_reservation(session, reservation_id)
