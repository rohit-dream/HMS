"""OPD module router — aggregates visit, queue, vitals, notes, and prescription stubs."""

from fastapi import APIRouter

from app.api.v1.opd import notes, prescriptions, queue, visits, vitals

router = APIRouter(prefix="/opd", tags=["OPD"])
router.include_router(visits.router)
router.include_router(queue.router)
router.include_router(vitals.router)
router.include_router(notes.router)
router.include_router(prescriptions.router)
