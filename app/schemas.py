from typing import Dict, Optional

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    gender: str = "male"
    age_group: str = "adult"
    top: str = Field(default="", max_length=200)
    bottom: str = Field(default="", max_length=200)
    output_filename: Optional[str] = Field(default=None, max_length=120)


class GenerateResponse(BaseModel):
    status: str
    image_url: str
    selected_mannequin: str
    selected_clothes: Dict[str, Optional[str]]
    message: str
