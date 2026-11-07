import logging
from typing import Optional
from datetime import datetime
from sqlmodel import Session, select
from fastapi import HTTPException

from ..models.plan import Plan
from ..schemas.plan import PlanCreate, PlanUpdate

logger = logging.getLogger("gymapi")


class PlanService:

    @staticmethod
    def get_all(session: Session, active: Optional[bool] = None) -> list[Plan]:
        q = select(Plan)
        if active is not None:
            q = q.where(Plan.active == active)
        return session.exec(q.order_by(Plan.name)).all()

    @staticmethod
    def get_by_id(session: Session, plan_id: int) -> Plan:
        plan = session.get(Plan, plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        return plan

    @staticmethod
    def create(session: Session, data: PlanCreate) -> Plan:
        existing = session.exec(
            select(Plan).where(Plan.name == data.name)
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="A plan with this name already exists")
        plan = Plan.model_validate(data)
        session.add(plan)
        session.commit()
        session.refresh(plan)
        logger.info(f"Plan created: {data.name}")
        return plan

    @staticmethod
    def update(session: Session, plan_id: int, data: PlanUpdate) -> Plan:
        plan = PlanService.get_by_id(session, plan_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(plan, key, value)
        plan.updated_at = datetime.utcnow()
        session.add(plan)
        session.commit()
        session.refresh(plan)
        return plan

    @staticmethod
    def delete(session: Session, plan_id: int) -> None:
        from ..models.membership import Membership
        plan = PlanService.get_by_id(session, plan_id)
        # Block deletion if there are memberships linked to this plan
        linked = session.exec(
            select(Membership).where(Membership.plan_id == plan_id)
        ).first()
        if linked:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete a plan that has memberships linked to it."
            )
        session.delete(plan)
        session.commit()
        logger.info(f"Plan deleted: id={plan_id}")