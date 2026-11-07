import logging
from typing import Optional
from datetime import date, timedelta
from decimal import Decimal
from sqlmodel import Session, select
from fastapi import HTTPException
from ..models.membership import Membership, MembershipStatus
from ..models.member import MemberStatus
from ..models.payment import Payment, PaymentStatus
from ..models.plan import Plan
from ..schemas.membership import MembershipCreate, MembershipUpdate

logger = logging.getLogger("gymapi")


class MembershipService:

    @staticmethod
    def get_all(session: Session, status: Optional[MembershipStatus] = None,
                member_id: Optional[int] = None, skip: int = 0, limit: int = 20) -> list[Membership]:
        q = select(Membership)
        if status:
            q = q.where(Membership.status == status)
        if member_id:
            q = q.where(Membership.member_id == member_id)
        return session.exec(q.order_by(Membership.start_date.desc()).offset(skip).limit(limit)).all()

    @staticmethod
    def get_by_id(session: Session, membership_id: int) -> Membership:
        m = session.get(Membership, membership_id)
        if not m:
            raise HTTPException(status_code=404, detail="Membership not found")
        return m

    @staticmethod
    def create(session: Session, data: MembershipCreate) -> Membership:
        from ..models.member import Member
        member = session.get(Member, data.member_id)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        if member.status != MemberStatus.active:
            raise HTTPException(status_code=400, detail="Cannot create a membership for an inactive member")
        plan = session.get(Plan, data.plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        if not plan.active:
            raise HTTPException(status_code=400, detail="The selected plan is not active")
        membership = Membership.model_validate(data)
        membership.calculate_end_date(plan.duration_days)
        session.add(membership)
        session.commit()
        session.refresh(membership)
        logger.info(f"Membership created: member={data.member_id} plan={plan.name}")
        return membership

    @staticmethod
    def delete(session: Session, membership_id: int) -> None:
        membership = MembershipService.get_by_id(session, membership_id)
        # Block deletion if there are completed payments linked to this membership
        payments = session.exec(
            select(Payment).where(
                Payment.membership_id == membership_id,
                Payment.status == PaymentStatus.completed
            )
        ).first()
        if payments:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete a membership with completed payments."
            )
        session.delete(membership)
        session.commit()
        logger.info(f"Membership deleted: id={membership_id}")

    @staticmethod
    def renew(session: Session, membership_id: int) -> Membership:
        current = MembershipService.get_by_id(session, membership_id)
        if current.status not in [MembershipStatus.active, MembershipStatus.expired]:
            raise HTTPException(status_code=400, detail="Only active or expired memberships can be renewed")
        plan = session.get(Plan, current.plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        new_membership = Membership(
            member_id=current.member_id,
            plan_id=current.plan_id,
            start_date=current.end_date + timedelta(days=1),
            status=MembershipStatus.pending,
        )
        new_membership.calculate_end_date(plan.duration_days)
        session.add(new_membership)
        session.commit()
        session.refresh(new_membership)
        logger.info(f"Membership renewed for member_id={current.member_id}")
        return new_membership

    @staticmethod
    def expiring_soon(session: Session, days: int = 7) -> list[Membership]:
        today = date.today()
        limit = today + timedelta(days=days)
        return session.exec(
            select(Membership).where(
                Membership.status == MembershipStatus.active,
                Membership.end_date >= today,
                Membership.end_date <= limit,
            )
        ).all()

    @staticmethod
    def get_total_paid(session: Session, membership_id: int) -> Decimal:
        payments = session.exec(
            select(Payment).where(
                Payment.membership_id == membership_id,
                Payment.status == PaymentStatus.completed,
            )
        ).all()
        return sum(p.amount for p in payments) or Decimal("0.00")