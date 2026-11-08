from datetime import date, datetime
from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import Session, select
from app.models.member import Member, MemberStatus
from app.models.membership import Membership, MembershipStatus
from app.models.reservation import Reservation, ReservationStatus
from app.models.shift import AvailableShift
from app.schemas.reservation import ReservationCreate


def create_reservation(session: Session, data: ReservationCreate) -> Reservation:
    # Lock the class row so concurrent staff requests cannot overbook it.
    shift = session.exec(select(AvailableShift).where(AvailableShift.id == data.shift_id).with_for_update()).first()
    if not shift:
        raise HTTPException(404, "Shift not found")
    if not shift.active_slot or ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")[data.date.weekday()] != shift.day_of_week.value:
        raise HTTPException(400, "Choose an active class on its scheduled weekday")
    member = session.get(Member, data.member_id)
    if not member:
        raise HTTPException(404, "Member not found")
    if not member.is_active or member.status != MemberStatus.active:
        raise HTTPException(400, "Inactive members cannot enroll")
    membership = session.exec(select(Membership).where(
        Membership.member_id == member.id, Membership.status == MembershipStatus.active,
        Membership.start_date <= data.date, Membership.end_date >= data.date,
    )).first()
    if membership is None:
        raise HTTPException(400, "A paid membership covering the class date is required")
    existing = session.exec(select(Reservation).where(
        Reservation.member_id == member.id, Reservation.shift_id == shift.id, Reservation.date == data.date,
    )).first()
    if existing and existing.status == ReservationStatus.confirmed:
        raise HTTPException(409, "Member already enrolled in this class")
    count = session.exec(select(func.count(Reservation.id)).where(
        Reservation.shift_id == shift.id, Reservation.date == data.date,
        Reservation.status == ReservationStatus.confirmed,
    )).one()
    if count >= shift.max_capacity:
        raise HTTPException(409, "Shift is fully booked")
    reservation = existing or Reservation(member_id=member.id, shift_id=shift.id, date=data.date)
    reservation.status = ReservationStatus.confirmed
    reservation.updated_at = datetime.utcnow()
    session.add(reservation)
    session.commit()
    session.refresh(reservation)
    return reservation


def get_reservation(session: Session, reservation_id: int) -> Reservation:
    record = session.get(Reservation, reservation_id)
    if record is None:
        raise HTTPException(404, "Enrollment not found")
    return record


def get_reservations(session: Session, member_id=None, shift_id=None, day=None, skip=0, limit=100):
    query = select(Reservation)
    if member_id is not None:
        query = query.where(Reservation.member_id == member_id)
    if shift_id is not None:
        query = query.where(Reservation.shift_id == shift_id)
    if day is not None:
        query = query.where(Reservation.date == day)
    # Legacy rows without a member or class are not valid class enrollments.
    query = query.where(Reservation.member_id.is_not(None), Reservation.shift_id.is_not(None))
    return session.exec(query.order_by(Reservation.date.desc(), Reservation.id.desc()).offset(skip).limit(limit)).all()


def cancel_reservation(session: Session, reservation_id: int) -> Reservation:
    record = get_reservation(session, reservation_id)
    record.status = ReservationStatus.cancelled
    record.updated_at = datetime.utcnow()
    session.add(record)
    session.commit()
    session.refresh(record)
    return record
