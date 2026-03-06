import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.exceptions import ForbiddenError, NotFoundError
from db.models.policy import Policy
from db.models.user import User
from dependencies import get_current_user, get_db
from schemas.policy import PolicyCreate, PolicyResponse, PolicyUpdate

router = APIRouter(prefix="/policies", tags=["policies"])


@router.get("", response_model=list[PolicyResponse])
async def list_policies(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.org_id:
        return []
    stmt = select(Policy).where(Policy.org_id == user.org_id)
    return (await db.execute(stmt)).scalars().all()


@router.post("", response_model=PolicyResponse, status_code=201)
async def create_policy(
    body: PolicyCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not user.org_id:
        raise ForbiddenError("User must belong to an organization")

    policy = Policy(
        org_id=user.org_id,
        name=body.name,
        rules=body.rules.model_dump(),
    )
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    return policy


@router.patch("/{policy_id}", response_model=PolicyResponse)
async def update_policy(
    policy_id: uuid.UUID,
    body: PolicyUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Policy).where(Policy.id == policy_id)
    policy = (await db.execute(stmt)).scalar_one_or_none()
    if not policy:
        raise NotFoundError("Policy", str(policy_id))
    if policy.org_id != user.org_id:
        raise ForbiddenError()

    updates = body.model_dump(exclude_unset=True)
    if "rules" in updates and updates["rules"] is not None:
        updates["rules"] = body.rules.model_dump()
    for field, value in updates.items():
        setattr(policy, field, value)

    await db.commit()
    await db.refresh(policy)
    return policy


@router.delete("/{policy_id}", status_code=204)
async def delete_policy(
    policy_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Policy).where(Policy.id == policy_id)
    policy = (await db.execute(stmt)).scalar_one_or_none()
    if not policy:
        raise NotFoundError("Policy", str(policy_id))
    if policy.org_id != user.org_id:
        raise ForbiddenError()

    await db.delete(policy)
    await db.commit()
