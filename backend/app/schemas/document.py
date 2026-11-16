from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class ExtractedFieldSchema(BaseModel):
    id: Optional[int] = None
    field_name: str
    field_value: Optional[str] = None
    confidence: float
    page_number: int = 1
    extraction_method: str = "regex"

    class Config:
        from_attributes = True

class DocumentUploadResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    category: str
    file_size: int
    mime_type: str
    upload_status: str
    page_count: int
    quality_score: float
    is_blurry: bool
    is_low_res: bool
    is_rotated: bool
    created_at: datetime
    extracted_fields: List[ExtractedFieldSchema] = []

    class Config:
        from_attributes = True

class DocumentListItem(BaseModel):
    id: int
    filename: str
    original_filename: str
    category: str
    file_size: int
    upload_status: str
    quality_score: float
    is_blurry: bool
    is_low_res: bool
    page_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentDetail(BaseModel):
    id: int
    filename: str
    original_filename: str
    category: str
    file_size: int
    mime_type: str
    upload_status: str
    quality_score: float
    is_blurry: bool
    is_low_res: bool
    is_rotated: bool
    page_count: int
    raw_text: Optional[str] = None
    created_at: datetime
    extracted_fields: List[ExtractedFieldSchema] = []

    class Config:
        from_attributes = True
