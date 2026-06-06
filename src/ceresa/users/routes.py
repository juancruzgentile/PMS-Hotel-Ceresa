from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ceresa.users import repository


router = APIRouter(prefix="/users", tags=["Users"])


class DepartmentCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=100)


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=150)
    email: str | None = Field(default=None, max_length=150)

    user_type: Literal[
        "employee",
        "supervisor",
        "director",
        "guest",
    ]

    department_id: int | None = Field(default=None, ge=1)


def validate_user_department(user: UserCreate) -> None:
    """
    Validates the relationship between user type and department.
    """
    internal_types = {"employee", "supervisor"}

    if user.user_type in internal_types and user.department_id is None:
        raise HTTPException(
            status_code=400,
            detail="Employees and supervisors require a department.",
        )

    if user.user_type in {"director", "guest"} and user.department_id is not None:
        raise HTTPException(
            status_code=400,
            detail="Directors and guests cannot belong to one department.",
        )

    if user.department_id is not None:
        department = repository.get_department_by_id(user.department_id)

        if department is None:
            raise HTTPException(
                status_code=404,
                detail="Department not found.",
            )

        if not bool(department["is_active"]):
            raise HTTPException(
                status_code=400,
                detail="Department is inactive.",
            )


@router.post("/departments")
def create_department(department: DepartmentCreate) -> dict:
    """
    Creates a hotel department.
    """
    try:
        department_id = repository.create_department(
            code=department.code.strip().lower(),
            name=department.name.strip(),
        )

    except Exception as error:
        if repository.is_unique_constraint_error(error):
            raise HTTPException(
                status_code=409,
                detail="A department with this code already exists.",
            )

        raise

    return {
        "message": "Department created successfully",
        "department_id": department_id,
    }


@router.get("/departments")
def list_departments() -> list[dict]:
    """
    Returns all hotel departments.
    """
    return repository.list_departments()


@router.post("")
def create_user(user: UserCreate) -> dict:
    """
    Creates a user without authentication credentials.

    Authentication will be implemented in a later security phase.
    """
    validate_user_department(user)

    try:
        user_id = repository.create_user(user.model_dump())

    except Exception as error:
        if repository.is_unique_constraint_error(error):
            raise HTTPException(
                status_code=409,
                detail="Username or email already exists.",
            )

        raise

    return {
        "message": "User created successfully",
        "user_id": user_id,
    }


@router.get("")
def list_users() -> list[dict]:
    """
    Returns all users and their department information.
    """
    return repository.list_users()