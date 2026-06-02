from typing import Dict, Literal, Optional

from pydantic import BaseModel, Field


Gender = Literal["male", "female"]
AgeGroup = Literal["adult", "kids"]


class GenerateRequest(BaseModel):
    gender: Gender = "male"
    age_group: AgeGroup = "adult"
    top: str = Field(default="", max_length=200)
    bottom: str = Field(default="", max_length=200)
    accessory: str = Field(default="", max_length=200)
    output_filename: Optional[str] = Field(default=None, max_length=120)


class GenerateResponse(BaseModel):
    status: str
    image_url: str
    selected_mannequin: str
    selected_clothes: Dict[str, Optional[str]]
    message: str
