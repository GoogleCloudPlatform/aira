"""
Module containing schemas for all location endpoints
"""

import datetime
import uuid

import pydantic


class CountryBase(pydantic.BaseModel):
    name: str
    code: str
    is_default: bool = False

    class Config:
        orm_mode = True


class CountryCreate(CountryBase):
    pass


class CountryGet(CountryBase):
    id: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime


class CountryList(pydantic.BaseModel):
    items: list[CountryGet]
    pages: int
    current_page: int
    total: int


class StateBase(pydantic.BaseModel):
    name: str
    code: str
    country_id: uuid.UUID

    class Config:
        orm_mode = True


class StateCreate(StateBase):
    pass


class StateGet(StateBase):
    id: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
    country: CountryBase | None = None


class StateList(pydantic.BaseModel):
    items: list[StateGet]
    pages: int
    current_page: int
    total: int


class CityBase(pydantic.BaseModel):
    name: str
    state_id: uuid.UUID

    class Config:
        orm_mode = True


class CityCreate(CityBase):
    pass


class CityGet(CityBase):
    id: uuid.UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime
    state: StateBase | None = None


class CityList(pydantic.BaseModel):
    items: list[CityGet]
    pages: int
    current_page: int
    total: int
