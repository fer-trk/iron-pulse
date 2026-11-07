import logging
from typing import Optional
from sqlmodel import Session, select
from fastapi import HTTPException

from ..models.member import Member
from ..schemas.member import MemberCreate, MemberUpdate

logger = logging.getLogger("gymapi")


class MemberService:

    @staticmethod
    def get_all(
        session: Session,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20
    ) -> list[Member]:
        q = select(Member)
        if is_active is not None:
            q = q.where(Member.is_active == is_active)
        return session.exec(q.order_by(Member.first_name).offset(skip).limit(limit)).all()

    @staticmethod
    def get_by_id(session: Session, member_id: int) -> Member:
        member = session.get(Member, member_id)
        if not member:
            raise HTTPException(status_code=404, detail="Member not found")
        return member

    @staticmethod
    def create(session: Session, data: MemberCreate) -> Member:
        existing = session.exec(
            select(Member).where(Member.email == data.email)
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")
        member = Member.model_validate(data)
        session.add(member)
        session.commit()
        session.refresh(member)
        logger.info(f"Member created: {data.email}")
        return member

    @staticmethod
    def update(session: Session, member_id: int, data: MemberUpdate) -> Member:
        member = MemberService.get_by_id(session, member_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(member, key, value)
        session.add(member)
        session.commit()
        session.refresh(member)
        return member

    @staticmethod
    def delete(session: Session, member_id: int) -> None:
        from ..models.membership import Membership, MembershipStatus
        from sqlmodel import select
        member = MemberService.get_by_id(session, member_id)
        active = session.exec(
            select(Membership).where(
                Membership.member_id == member_id,
                Membership.status == MembershipStatus.active
            )
        ).first()
        if active:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete a member with an active membership. Cancel the membership first."
            )
        session.delete(member)
        session.commit()
        logger.info(f"Member deleted: id={member_id}")