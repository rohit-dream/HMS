"""clinical schema ORM models."""

from app.models.clinical.appointment import Appointment
from app.models.clinical.opd import (
    OpdClinicalNote,
    OpdPrescription,
    OpdPrescriptionItem,
    OpdQueue,
    OpdReferral,
    OpdVitals,
    OpdVisit,
)

__all__ = [
    "Appointment",
    "OpdClinicalNote",
    "OpdPrescription",
    "OpdPrescriptionItem",
    "OpdQueue",
    "OpdReferral",
    "OpdVitals",
    "OpdVisit",
]
