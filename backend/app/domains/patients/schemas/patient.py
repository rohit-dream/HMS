"""Pydantic schemas for patient CRUD."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.domains.patients.schemas.allergy import AllergyResponse
from app.domains.patients.schemas.chronic_condition import ChronicConditionResponse
from app.domains.patients.schemas.contact import ContactResponse

Gender = Literal["male", "female", "other"]
ConsentMethod = Literal["written", "verbal", "digital"]
VALID_GENDERS = frozenset({"male", "female", "other"})
VALID_CONSENT_METHODS = frozenset({"written", "verbal", "digital"})
VALID_BLOOD_GROUPS = frozenset({"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"})


class PatientCreateRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    date_of_birth: date
    gender: Gender
    phone: str = Field(min_length=10, max_length=10)
    email: EmailStr | None = None
    blood_group: str | None = Field(default=None, max_length=5)
    address_line1: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    photo_url: str | None = None
    id_proof_type: str | None = Field(default=None, max_length=50)
    id_proof_number: str | None = Field(default=None, max_length=50)
    marital_status: str | None = Field(default=None, max_length=20)
    occupation: str | None = Field(default=None, max_length=100)
    location_id: uuid.UUID | None = None
    acknowledge_duplicate: bool = False
    data_processing_consent: bool
    consent_method: ConsentMethod

    @model_validator(mode="after")
    def validate_consent(self) -> PatientCreateRequest:
        if not self.data_processing_consent:
            raise ValueError("data_processing_consent must be true to register a patient")
        return self

    @field_validator("consent_method")
    @classmethod
    def validate_consent_method(cls, value: str) -> str:
        if value not in VALID_CONSENT_METHODS:
            raise ValueError("consent_method must be written, verbal, or digital")
        return value

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_names(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        digits = value.strip()
        if not digits.isdigit() or len(digits) != 10:
            raise ValueError("phone must be exactly 10 digits")
        return digits

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value: str) -> str:
        if value not in VALID_GENDERS:
            raise ValueError("gender must be male, female, or other")
        return value

    @field_validator("blood_group")
    @classmethod
    def validate_blood_group(cls, value: str | None) -> str | None:
        if value is not None and value not in VALID_BLOOD_GROUPS:
            raise ValueError("invalid blood_group")
        return value

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob_not_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        return value


class PatientUpdateRequest(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    date_of_birth: date | None = None
    gender: Gender | None = None
    phone: str | None = Field(default=None, min_length=10, max_length=10)
    email: EmailStr | None = None
    blood_group: str | None = Field(default=None, max_length=5)
    address_line1: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=100)
    state: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    photo_url: str | None = None
    id_proof_type: str | None = Field(default=None, max_length=50)
    id_proof_number: str | None = Field(default=None, max_length=50)
    marital_status: str | None = Field(default=None, max_length=20)
    occupation: str | None = Field(default=None, max_length=100)
    location_id: uuid.UUID | None = None

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_names(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        digits = value.strip()
        if not digits.isdigit() or len(digits) != 10:
            raise ValueError("phone must be exactly 10 digits")
        return digits

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, value: str | None) -> str | None:
        if value is not None and value not in VALID_GENDERS:
            raise ValueError("gender must be male, female, or other")
        return value

    @field_validator("blood_group")
    @classmethod
    def validate_blood_group(cls, value: str | None) -> str | None:
        if value is not None and value not in VALID_BLOOD_GROUPS:
            raise ValueError("invalid blood_group")
        return value

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob_not_future(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("date_of_birth cannot be in the future")
        return value


class PatientListItem(BaseModel):
    id: uuid.UUID
    mrn: str
    first_name: str
    last_name: str | None = None
    date_of_birth: date
    gender: str
    phone: str
    email: str | None = None
    blood_group: str | None = None
    last_visit_date: date | None = None
    created_at: datetime


class PatientDetailResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    mrn: str
    first_name: str
    last_name: str | None = None
    date_of_birth: date
    gender: str
    blood_group: str | None = None
    phone: str
    email: str | None = None
    address_line1: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    photo_url: str | None = None
    id_proof_type: str | None = None
    id_proof_number: str | None = None
    marital_status: str | None = None
    occupation: str | None = None
    consent_given_at: datetime | None = None
    consent_method: str | None = None
    location_id: uuid.UUID | None = None
    chronic_conditions: list[ChronicConditionResponse] = Field(default_factory=list)
    allergies: list[AllergyResponse] = Field(default_factory=list)
    contacts: list[ContactResponse] = Field(default_factory=list)
    last_visit_date: date | None = None
    version: int
    created_at: datetime
    updated_at: datetime | None = None
