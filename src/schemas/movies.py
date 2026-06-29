from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class CountryResponse(BaseModel):
    id: int
    code: str
    name: Optional[str] = None

    class Config:
        from_attributes = True


class GenreResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ActorResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class LanguageResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    movies: List[MovieListItemSchema]
    prev_page: Optional[str] = None
    next_page: Optional[str] = None
    total_pages: int
    total_items: int


class MovieCreateSchema(BaseModel):
    name: str = Field(..., max_length=255)
    date: date
    score: float = Field(..., ge=0.0, le=100.0)
    overview: str
    status: str
    budget: Decimal = Field(..., ge=Decimal("0.0"))
    revenue: Decimal = Field(..., ge=Decimal("0.0"))
    country: str = Field(..., min_length=2, max_length=3)
    genres: List[str]
    actors: List[str]
    languages: List[str]

    @field_validator("date")
    @classmethod
    def validate_date_future(cls, v: date) -> date:
        current_year = date.today().year
        if v.year > current_year + 1:
            raise ValueError("The date must not be more than one year in the future.")
        return v

    @field_validator("status")
    @classmethod
    def validate_status_enum(cls, v: str) -> str:
        allowed = {"Released", "Post Production", "In Production"}
        if v not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return v


class MovieDetailSchema(BaseModel):
    id: int
    name: str
    date: date
    score: float
    overview: str
    status: str
    budget: float
    revenue: float
    country: CountryResponse
    genres: List[GenreResponse]
    actors: List[ActorResponse]
    languages: List[LanguageResponse]

    class Config:
        from_attributes = True


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[date] = None
    score: Optional[float] = Field(None, ge=0.0, le=100.0)
    overview: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[Decimal] = Field(None, ge=Decimal("0.0"))
    revenue: Optional[Decimal] = Field(None, ge=Decimal("0.0"))

    @field_validator("date")
    @classmethod
    def validate_date_future(cls, v: Optional[date]) -> Optional[date]:
        if v is None:
            return v
        current_year = date.today().year
        if v.year > current_year + 1:
            raise ValueError("The date must not be more than one year in the future.")
        return v

    @field_validator("status")
    @classmethod
    def validate_status_enum(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"Released", "Post Production", "In Production"}
        if v not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return v


class MessageResponse(BaseModel):
    detail: str
