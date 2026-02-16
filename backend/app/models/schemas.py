from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class Building(BaseModel):
    id: UUID
    address: str
    quartu_frazione: str
    risk_score: float
    status: str

class Violation(BaseModel):
    id: UUID
    building_id: UUID
    violation_type: str
    unauthorized_area_m2: Optional[float] = None
    detected_date: Optional[str] = None
    status: Optional[str] = None
    severity: Optional[str] = None
    description: Optional[str] = None
    regulatory_norm: Optional[str] = None

class Document(BaseModel):
    id: UUID
    building_id: UUID
    file_name: str
    file_url: str
    document_type: Optional[str] = None
    extracted_text: Optional[str] = None
    upload_date: Optional[str] = None
