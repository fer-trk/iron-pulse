from datetime import date, datetime
from typing import List, Optional
from sqlmodel import Session, select
from sqlalchemy import func
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.models.shift import AvailableShift, DayOfWeek
from app.models.reservation import Reservation, ReservationStatus
from app.schemas.shift import ShiftCreate, ShiftUpdate, ShiftAvailability


def create_shift(session: Session, shift_data: ShiftCreate) -> AvailableShift:
    if shift_data.end_time <= shift_data.start_time:
        raise HTTPException(400, "Class end must be after its start")
    shift = AvailableShift.model_validate(shift_data)
    session.add(shift)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "A class already exists on this weekday and start time")
    session.refresh(shift)
    return shift


def get_shift(session: Session, shift_id: int) -> AvailableShift:
    shift = session.get(AvailableShift, shift_id)
    if not shift:
        raise HTTPException(status_code=404, detail="Shift not found")
    return shift


def get_all_shifts(
    session: Session,
    day_of_week: Optional[DayOfWeek] = None,
    name: Optional[str] = None
) -> List[AvailableShift]:
    statement = select(AvailableShift)
    if day_of_week:
        statement = statement.where(AvailableShift.day_of_week == day_of_week)
    if name:
        statement = statement.where(AvailableShift.class_name == name)
    return session.exec(statement).all()


def update_shift(session: Session, shift_id: int, shift_data: ShiftUpdate) -> AvailableShift:
    shift = get_shift(session, shift_id)
    if session.exec(select(Reservation).where(Reservation.shift_id == shift_id, Reservation.status == ReservationStatus.confirmed)).first():
        changes = shift_data.model_dump(exclude_unset=True)
        if any(key in changes and changes[key] != getattr(shift, key) for key in ("day_of_week", "start_time", "end_time")):
            raise HTTPException(400, "Cancel confirmed enrollments before changing the schedule")
    for key, value in shift_data.model_dump(exclude_unset=True).items():
        setattr(shift, key, value)
    if shift.end_time <= shift.start_time:
        raise HTTPException(400, "Class end must be after its start")
    counts = session.exec(select(func.count(Reservation.id)).where(
        Reservation.shift_id == shift_id, Reservation.status == ReservationStatus.confirmed,
    ).group_by(Reservation.date)).all()
    if counts and shift.max_capacity < max(counts):
        raise HTTPException(400, "Capacity cannot be lower than confirmed enrollments")
    shift.updated_at = datetime.utcnow()
    session.add(shift)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "A class already exists on this weekday and start time")
    session.refresh(shift)
    return shift


def delete_shift(session: Session, shift_id: int) -> None:
    shift = get_shift(session, shift_id)
    if session.exec(select(Reservation).where(Reservation.shift_id == shift_id)).first():
        raise HTTPException(400, "Cannot delete a class with enrollment history. Deactivate instead.")
    session.delete(shift)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, "A class already exists on this weekday and start time")


def get_shift_availability(session: Session, shift_id: int, date: date) -> ShiftAvailability:
    shift = get_shift(session, shift_id)
    active_bookings = session.exec(
        select(func.count(Reservation.id)).where(
            Reservation.shift_id == shift_id,
            Reservation.date == date,
            Reservation.status == ReservationStatus.confirmed
        )
    ).one()
    available_spots = shift.max_capacity - active_bookings
    return ShiftAvailability(
        shift_id=shift.id,
        shift_name=shift.class_name,
        date=date,
        day_of_week=shift.day_of_week,
        start_time=shift.start_time,
        end_time=shift.end_time,
        max_capacity=shift.max_capacity,
        active_bookings=active_bookings,
        available_spots=available_spots,
        is_available=shift.active_slot and available_spots > 0
    )