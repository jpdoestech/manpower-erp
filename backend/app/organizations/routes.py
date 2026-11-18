from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator
from sqlalchemy import select

from app.identity.routes import Current, Db, check_csrf, check_origin
from app.organizations import service
from app.organizations.models import Company

router = APIRouter(prefix="/api/companies", tags=["Companies"])


class CompanyView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    code: str
    legal_name: str
    is_active: bool
    version: int


class CompanyEdit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    legal_name: str = Field(min_length=1, max_length=200)
    is_active: StrictBool
    version: int = Field(ge=1, strict=True)

    @field_validator("legal_name")
    @classmethod
    def valid_name(cls, value: str) -> str:
        return service.validated_company("OK", value)[1]


@router.get("", response_model=list[CompanyView])
def list_companies(
    current: Current,
    db: Db,
    response: Response,
    q: Annotated[str, Query(max_length=100)] = "",
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
    active: bool | None = None,
) -> list[Company]:
    service.set_actor(db, current.user.id)
    response.headers["Cache-Control"] = "no-store"
    query = select(Company).where(
        Company.id.in_(service.authorized_company_ids(current.user.id))
    )
    if q.strip():
        query = query.where(
            Company.legal_name.icontains(q.strip(), autoescape=True)
            | Company.code.icontains(q.strip(), autoescape=True)
        )
    if active is not None:
        query = query.where(Company.is_active == active)
    return list(db.scalars(query.order_by(Company.code).offset(offset).limit(21)))


@router.get("/{company_id}", response_model=CompanyView)
def get_company(
    company_id: UUID, current: Current, db: Db, response: Response
) -> Company:
    service.set_actor(db, current.user.id)
    response.headers["Cache-Control"] = "no-store"
    return service.company_for_user(db, current.user.id, company_id)


@router.patch(
    "/{company_id}", response_model=CompanyView, dependencies=[Depends(check_origin)]
)
def edit_company(
    company_id: UUID,
    body: CompanyEdit,
    current: Current,
    db: Db,
    request: Request,
    response: Response,
) -> Company:
    check_csrf(request, current)
    service.set_actor(db, current.user.id)
    response.headers["Cache-Control"] = "no-store"
    try:
        return service.edit_company(
            db,
            current.user.id,
            company_id,
            body.legal_name,
            body.is_active,
            body.version,
            UUID(request.state.request_id),
        )
    except ValueError:
        raise HTTPException(422) from None
