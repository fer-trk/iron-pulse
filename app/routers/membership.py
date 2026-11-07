from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from ..db.session import get_session
from ..core.security import get_current_user_sub
from ..services.membership import MembershipService
from ..schemas.membership import MembershipCreate, MembershipRead, MembershipUpdate
from ..models.membership import MembershipStatus

router = APIRouter(prefix="/memberships", tags=["memberships"])
auth = Depends(get_current_user_sub)


@router.get("/", response_model=list[MembershipRead], summary="List memberships")
def list_memberships(
    status: Optional[MembershipStatus] = None,
    member_id: Optional[int] = None,
    skip: int = 0,
    limit: int = Query(20, le=100),
    session: Session = Depends(get_session),
    _=auth
):
    return MembershipService.get_all(session, status=status, member_id=member_id, skip=skip, limit=limit)


@router.post("/", response_model=MembershipRead, status_code=201, summary="Create membership")
def create(data: MembershipCreate, session: Session = Depends(get_session), _=auth):
    return MembershipService.create(session, data)


@router.get("/expiring-soon", response_model=list[MembershipRead], summary="Memberships expiring soon")
def expiring_soon(
    days: int = Query(7, ge=1, le=60),
    session: Session = Depends(get_session),
    _=auth
):
    return MembershipService.expiring_soon(session, days)


@router.get("/{membership_id}", response_model=MembershipRead, summary="Membership detail")
def detail(membership_id: int, session: Session = Depends(get_session), _=auth):
    return MembershipService.get_by_id(session, membership_id)


@router.patch("/{membership_id}", response_model=MembershipRead, summary="Update status")
def update(
    membership_id: int,
    data: MembershipUpdate,
    session: Session = Depends(get_session),
    _=auth
):
    from datetime import datetime
    membership = MembershipService.get_by_id(session, membership_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(membership, field, value)
    membership.updated_at = datetime.utcnow()
    session.add(membership)
    session.commit()
    session.refresh(membership)
    return membership


@router.delete("/{membership_id}", status_code=204, summary="Delete membership")
def delete(membership_id: int, session: Session = Depends(get_session), _=auth):
    MembershipService.delete(session, membership_id)


@router.post("/{membership_id}/renew", response_model=MembershipRead, status_code=201, summary="Renew membership")
def renew(membership_id: int, session: Session = Depends(get_session), _=auth):
    return MembershipService.renew(session, membership_id)