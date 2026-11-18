from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator

from app.identity.routes import Current, Db, check_csrf, check_origin
from app.organizations import hierarchy
from app.organizations.models import Branch, HeadOffice
from app.organizations.service import set_actor, validated_company

router = APIRouter(
    prefix="/api/companies/{company_id}", tags=["Organization hierarchy"]
)


class UnitView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    company_id: UUID
    code: str
    name: str
    valid_from: date
    valid_to: date | None
    is_active: bool
    version: int


class BranchView(UnitView):
    head_office_id: UUID
    head_office_name: str


class UnitEnd(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    valid_to: date | None = None

    @field_validator("valid_to", mode="before")
    @classmethod
    def iso_end(cls, value: object) -> date | None:
        if value is None:
            return None
        if not isinstance(value, str) or len(value) != 10:
            raise ValueError("ISO date required")
        return date.fromisoformat(value)


class UnitCreate(UnitEnd):
    code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=1, max_length=200)
    valid_from: date
    is_active: StrictBool = True

    @field_validator("code")
    @classmethod
    def valid_code(cls, value: str) -> str:
        return validated_company(value, "name")[0]

    @field_validator("name")
    @classmethod
    def valid_name(cls, value: str) -> str:
        return validated_company("OK", value)[1]

    @field_validator("valid_from", mode="before")
    @classmethod
    def iso_start(cls, value: object) -> date:
        result = cls.iso_end(value)
        if result is None:
            raise ValueError("Start date required")
        return result


class BranchCreate(UnitCreate):
    head_office_id: UUID


class UnitEdit(UnitEnd):
    valid_to: date | None = Field(...)
    name: str = Field(min_length=1, max_length=200)
    is_active: StrictBool
    version: int = Field(ge=1, strict=True)

    @field_validator("name")
    @classmethod
    def valid_name(cls, value: str) -> str:
        return validated_company("OK", value)[1]


def access(db: Db, current: Current, company_id: UUID, response: Response) -> None:
    set_actor(db, current.user.id)
    hierarchy.company_access(db, current.user.id, company_id)
    response.headers["Cache-Control"] = "no-store"


@router.get("/head-offices", response_model=list[UnitView])
def head_offices(
    company_id: UUID,
    db: Db,
    current: Current,
    response: Response,
    q: Annotated[str, Query(max_length=100)] = "",
    active: bool | None = None,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
) -> list[HeadOffice | Branch]:
    access(db, current, company_id, response)
    return hierarchy.list_units(db, company_id, "head_office", q, active, offset)


@router.get("/branches", response_model=list[BranchView])
def branches(
    company_id: UUID,
    db: Db,
    current: Current,
    response: Response,
    q: Annotated[str, Query(max_length=100)] = "",
    active: bool | None = None,
    offset: Annotated[int, Query(ge=0, le=10000)] = 0,
    head_office_id: UUID | None = None,
) -> list[HeadOffice | Branch]:
    access(db, current, company_id, response)
    return hierarchy.list_units(
        db, company_id, "branch", q, active, offset, head_office_id
    )


@router.get("/head-offices/{unit_id}", response_model=UnitView)
def head_office(
    company_id: UUID, unit_id: UUID, db: Db, current: Current, response: Response
) -> HeadOffice | Branch:
    access(db, current, company_id, response)
    return hierarchy.get_unit(db, company_id, unit_id, "head_office")


@router.get("/branches/{unit_id}", response_model=BranchView)
def branch(
    company_id: UUID, unit_id: UUID, db: Db, current: Current, response: Response
) -> HeadOffice | Branch:
    access(db, current, company_id, response)
    return hierarchy.get_unit(db, company_id, unit_id, "branch")


@router.post(
    "/head-offices",
    response_model=UnitView,
    status_code=201,
    dependencies=[Depends(check_origin)],
)
def create_head_office(
    company_id: UUID,
    body: UnitCreate,
    db: Db,
    current: Current,
    request: Request,
    response: Response,
) -> HeadOffice | Branch:
    check_csrf(request, current)
    access(db, current, company_id, response)
    return hierarchy.create_unit(
        db,
        current.user.id,
        company_id,
        "head_office",
        body.code,
        body.name,
        body.valid_from,
        body.valid_to,
        body.is_active,
        None,
        UUID(request.state.request_id),
    )


@router.post(
    "/branches",
    response_model=BranchView,
    status_code=201,
    dependencies=[Depends(check_origin)],
)
def create_branch(
    company_id: UUID,
    body: BranchCreate,
    db: Db,
    current: Current,
    request: Request,
    response: Response,
) -> HeadOffice | Branch:
    check_csrf(request, current)
    access(db, current, company_id, response)
    return hierarchy.create_unit(
        db,
        current.user.id,
        company_id,
        "branch",
        body.code,
        body.name,
        body.valid_from,
        body.valid_to,
        body.is_active,
        body.head_office_id,
        UUID(request.state.request_id),
    )


@router.patch(
    "/head-offices/{unit_id}",
    response_model=UnitView,
    dependencies=[Depends(check_origin)],
)
def edit_head_office(
    company_id: UUID,
    unit_id: UUID,
    body: UnitEdit,
    db: Db,
    current: Current,
    request: Request,
    response: Response,
) -> HeadOffice | Branch:
    check_csrf(request, current)
    access(db, current, company_id, response)
    return hierarchy.edit_unit(
        db,
        current.user.id,
        company_id,
        unit_id,
        "head_office",
        body.name,
        body.valid_to,
        body.is_active,
        body.version,
        UUID(request.state.request_id),
    )


@router.patch(
    "/branches/{unit_id}",
    response_model=BranchView,
    dependencies=[Depends(check_origin)],
)
def edit_branch(
    company_id: UUID,
    unit_id: UUID,
    body: UnitEdit,
    db: Db,
    current: Current,
    request: Request,
    response: Response,
) -> HeadOffice | Branch:
    check_csrf(request, current)
    access(db, current, company_id, response)
    return hierarchy.edit_unit(
        db,
        current.user.id,
        company_id,
        unit_id,
        "branch",
        body.name,
        body.valid_to,
        body.is_active,
        body.version,
        UUID(request.state.request_id),
    )
