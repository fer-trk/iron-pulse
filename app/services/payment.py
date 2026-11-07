import logging
from decimal import Decimal
from datetime import datetime
from sqlmodel import Session, select
from fastapi import HTTPException

from ..models.payment import Payment, PaymentStatus
from ..models.membership import Membership, MembershipStatus
from ..schemas.payment import PaymentCreate, PaymentUpdate

logger = logging.getLogger("gymapi")


class PaymentService:

    @staticmethod
    def get_all(session: Session, status=None, method=None, membership_id=None,
                skip: int = 0, limit: int = 20) -> list[Payment]:
        q = select(Payment)
        if status:
            q = q.where(Payment.status == status)
        if method:
            q = q.where(Payment.payment_method == method)
        if membership_id:
            q = q.where(Payment.membership_id == membership_id)
        return session.exec(q.order_by(Payment.payment_date.desc()).offset(skip).limit(limit)).all()

    @staticmethod
    def get_by_id(session: Session, payment_id: int) -> Payment:
        p = session.get(Payment, payment_id)
        if not p:
            raise HTTPException(status_code=404, detail="Payment not found")
        return p

    @staticmethod
    def create(session: Session, data: PaymentCreate) -> Payment:
        from ..models.plan import Plan

        membership = session.get(Membership, data.membership_id)
        if not membership:
            raise HTTPException(status_code=404, detail="Membership not found")
        if membership.status == MembershipStatus.cancelled:
            raise HTTPException(status_code=400, detail="Cannot register payments on cancelled memberships")

        if data.amount is None:
            plan = session.get(Plan, membership.plan_id)
            if not plan:
                raise HTTPException(status_code=404, detail="Plan not found")
            data = data.model_copy(update={"amount": Decimal(str(plan.price))})

        payment = Payment.model_validate(data)
        session.add(payment)
        session.flush()

        if payment.status == PaymentStatus.completed and membership.status == MembershipStatus.pending:
            previous_payments = session.exec(
                select(Payment).where(
                    Payment.membership_id == membership.id,
                    Payment.status == PaymentStatus.completed,
                    Payment.id != payment.id
                )
            ).all()
            total = sum(p.amount for p in previous_payments) + payment.amount
            plan = session.get(Plan, membership.plan_id)
            if plan and total >= plan.price:
                membership.status = MembershipStatus.active
                membership.updated_at = datetime.utcnow()
                session.add(membership)
                logger.info(f"Membership {membership.id} automatically activated via full payment")

        session.commit()
        session.refresh(payment)
        return payment

    @staticmethod
    def update(session: Session, payment_id: int, data: PaymentUpdate) -> Payment:
        payment = PaymentService.get_by_id(session, payment_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(payment, key, value)
        session.add(payment)
        session.commit()
        session.refresh(payment)
        logger.info(f"Payment {payment_id} updated")
        return payment

    @staticmethod
    def export_csv(session: Session) -> list[dict]:
        from ..models.member import Member
        from ..models.plan import Plan

        payments = session.exec(select(Payment)).all()
        rows = []
        for p in payments:
            membership = session.get(Membership, p.membership_id)
            member = session.get(Member, membership.member_id) if membership else None
            plan = session.get(Plan, membership.plan_id) if membership else None
            rows.append({
                "id": p.id,
                "member": f"{member.first_name} {member.last_name}" if member else "",
                "plan": plan.name if plan else "",
                "amount": str(p.amount),
                "payment_method": p.payment_method.value,
                "status": p.status.value,
                "reference": p.reference,
                "payment_date": p.payment_date.strftime("%d/%m/%Y %H:%M"),
            })
        return rows

    @staticmethod
    def delete(session: Session, payment_id: int) -> None:
        from datetime import timedelta
        payment = PaymentService.get_by_id(session, payment_id)
        if datetime.utcnow() - payment.created_at > timedelta(minutes=30):
            raise HTTPException(
                status_code=400,
                detail="Payment can only be deleted within 30 minutes of creation."
            )
        session.delete(payment)
        session.commit()
        logger.info(f"Payment {payment_id} deleted")