from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from ceresa.billing import repository
from ceresa.core.settings import HOTEL_CONFIG


router = APIRouter(prefix="/billing", tags=["Billing"])


class BillingAccountCreate(BaseModel):
    reservation_id: int = Field(..., ge=1)
    notes: str | None = Field(default=None, max_length=1000)


class BillingChargeCreate(BaseModel):
    source_module: Literal[
        "bar",
        "beach",
        "dining_room",
        "housekeeping",
        "kitchen",
        "laundry",
        "leisure",
        "maintenance",
        "reception",
        "rooms",
        "security",
        "tourism",
        "transport",
    ] = Field(..., max_length=50)
    description: str = Field(..., min_length=2, max_length=250)
    amount_cents: int = Field(..., gt=0)

    @field_validator("source_module", mode="before")
    @classmethod
    def normalize_source_module(cls, value: str) -> str:
        if not isinstance(value, str):
            return value

        return value.strip().lower()

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        if not isinstance(value, str):
            return value

        return value.strip()


class BillingPaymentCreate(BaseModel):
    payment_method: Literal[
        "card",
        "cash",
        "transfer",
    ] = Field(..., max_length=50)
    amount_cents: int = Field(..., gt=0)
    reference: str | None = Field(default=None, max_length=150)

    @field_validator("payment_method", mode="before")
    @classmethod
    def normalize_payment_method(cls, value: str) -> str:
        if not isinstance(value, str):
            return value

        return value.strip().lower()

    @field_validator("reference", mode="before")
    @classmethod
    def normalize_reference(cls, value: str | None) -> str | None:
        if value is None:
            return None

        if not isinstance(value, str):
            return value

        normalized_reference = value.strip()
        if not normalized_reference:
            return None

        return normalized_reference


class BillingAccountCreated(BaseModel):
    message: str
    billing_account_id: int


class BillingChargeCreated(BaseModel):
    message: str
    charge_id: int


class BillingPaymentCreated(BaseModel):
    message: str
    payment_id: int


def get_account_or_404(account_id: int) -> dict:
    """
    Returns one billing account or raises HTTP 404.
    """
    account = repository.get_billing_account_by_id(account_id)

    if account is None:
        raise HTTPException(
            status_code=404,
            detail="Billing account not found.",
        )

    return account


def ensure_account_is_open(account: dict) -> None:
    """
    Raises HTTP 409 when the account no longer accepts movements.
    """
    if account["status"] != "open":
        raise HTTPException(
            status_code=409,
            detail="Billing account is not open.",
        )


@router.get("/status")
def get_billing_status() -> dict:
    return {
        "module": "billing",
        "status": "active",
        "message": "Billing module is running",
    }


@router.get("/accounts")
def list_billing_accounts() -> list[dict]:
    """
    Returns billing accounts with compact operational balances.
    """
    accounts = repository.list_billing_accounts()

    for account in accounts:
        account["currency"] = HOTEL_CONFIG["currency"]

    return accounts


@router.post(
    "/accounts",
    response_model=BillingAccountCreated,
    status_code=status.HTTP_201_CREATED,
)
def create_billing_account(
    account: BillingAccountCreate,
) -> dict:
    """
    Creates one billing account for a reservation.
    """
    if not repository.reservation_is_billable(
        account.reservation_id
    ):
        raise HTTPException(
            status_code=404,
            detail="Reservation not found or cancelled.",
        )

    try:
        account_id = repository.create_billing_account(
            reservation_id=account.reservation_id,
            notes=account.notes,
        )

    except Exception as error:
        if repository.is_unique_constraint_error(error):
            raise HTTPException(
                status_code=409,
                detail=(
                    "A billing account already exists "
                    "for this reservation."
                ),
            )

        raise

    return {
        "message": "Billing account created successfully",
        "billing_account_id": account_id,
    }


@router.get("/accounts/{account_id}")
def get_billing_account(account_id: int) -> dict:
    """
    Returns an account with its charges, payments and balance.
    """
    account = get_account_or_404(account_id)
    account["currency"] = HOTEL_CONFIG["currency"]

    return account


@router.get("/reservations/{reservation_id}/account")
def get_billing_account_by_reservation(
    reservation_id: int,
) -> dict:
    """
    Returns the billing account attached to one reservation.
    """
    account = repository.get_billing_account_by_reservation_id(
        reservation_id,
    )

    if account is None:
        raise HTTPException(
            status_code=404,
            detail="Billing account not found for reservation.",
        )

    account["currency"] = HOTEL_CONFIG["currency"]

    return account


@router.post(
    "/accounts/{account_id}/charges",
    response_model=BillingChargeCreated,
    status_code=status.HTTP_201_CREATED,
)
def add_billing_charge(
    account_id: int,
    charge: BillingChargeCreate,
) -> dict:
    """
    Adds a charge generated by a hotel module.
    """
    account = get_account_or_404(account_id)
    ensure_account_is_open(account)

    charge_data = charge.model_dump()

    charge_id = repository.create_charge(
        billing_account_id=account_id,
        charge_data=charge_data,
    )

    return {
        "message": "Billing charge created successfully",
        "charge_id": charge_id,
    }


@router.post(
    "/accounts/{account_id}/payments",
    response_model=BillingPaymentCreated,
    status_code=status.HTTP_201_CREATED,
)
def add_billing_payment(
    account_id: int,
    payment: BillingPaymentCreate,
) -> dict:
    """
    Registers a payment made by the guest.
    """
    account = get_account_or_404(account_id)
    ensure_account_is_open(account)

    payment_data = payment.model_dump()

    payment_id = repository.create_payment(
        billing_account_id=account_id,
        payment_data=payment_data,
    )

    return {
        "message": "Billing payment created successfully",
        "payment_id": payment_id,
    }
