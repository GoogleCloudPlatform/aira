"""
Module containing all endpoints related to location services
"""

from __future__ import annotations

import logging
import uuid

import fastapi
import fastapi_injector
import sqlalchemy as sa
from api import models, ports
from api.helpers import auth
from api.helpers import schemas as util_schemas

from . import schemas

router = fastapi.APIRouter(tags=["locations"])

logger = logging.getLogger(__name__)

# Countries


@router.get("/countries", response_model=schemas.CountryList)
async def list_countries(
    list_data: util_schemas.ListSchema = fastapi.Depends(),
    list_countries_query: ports.ListCountries = fastapi_injector.Injected(
        ports.ListCountries
    ),
) -> schemas.CountryList:
    result, pagination_metadata = await list_countries_query(
        page_size=list_data.page_size, page=list_data.page, query=list_data.q
    )
    return schemas.CountryList(
        items=result,
        current_page=pagination_metadata.current_page,
        total=pagination_metadata.total_items,
        pages=pagination_metadata.total_pages,
    )


@router.get(
    "/countries/{country_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
    response_model=schemas.CountryGet,
)
async def get_country(
    get_country_query: ports.GetCountry = fastapi_injector.Injected(ports.GetCountry),
    country_id: uuid.UUID = fastapi.Path(...),
) -> schemas.CountryGet:
    country = await get_country_query(country_id=country_id)
    return schemas.CountryGet.from_orm(country)


@router.post(
    "/countries",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
    response_model=schemas.CountryGet,
)
async def create_country(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    body: schemas.CountryCreate = fastapi.Body(...),
) -> schemas.CountryGet:
    country = models.Country(**body.dict())
    async with uow_builder() as uow:
        country_model = await uow.country_repository.create(country)
        await uow.commit()
    return schemas.CountryGet.from_orm(country_model)


@router.put(
    "/countries/{country_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
    response_model=schemas.CountryGet,
)
async def update_country(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    body: schemas.CountryCreate = fastapi.Body(...),
    country_id: uuid.UUID = fastapi.Path(...),
) -> schemas.CountryGet:
    async with uow_builder() as uow:
        country = await uow.country_repository.get(country_id)
        country.name = body.name
        country.code = body.code
        country.is_default = body.is_default
        await uow.commit()
    return schemas.CountryGet.from_orm(country)


@router.delete(
    "/countries/{country_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def delete_country(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    country_id: uuid.UUID = fastapi.Path(...),
) -> fastapi.Response:
    async with uow_builder() as uow:
        country = await uow.country_repository.get(country_id)
        await uow.country_repository.delete(country)
        await uow.commit()
    return fastapi.Response(status_code=fastapi.status.HTTP_204_NO_CONTENT)


# States


@router.get("/states", response_model=schemas.StateList)
async def list_states(
    country_id: uuid.UUID | None = fastapi.Query(default=None),
    list_data: util_schemas.ListSchema = fastapi.Depends(),
    list_states_query: ports.ListStates = fastapi_injector.Injected(ports.ListStates),
) -> schemas.StateList:
    result, pagination_metadata = await list_states_query(
        country_id=country_id,
        page_size=list_data.page_size,
        page=list_data.page,
        query=list_data.q,
    )
    return schemas.StateList(
        items=result,
        current_page=pagination_metadata.current_page,
        total=pagination_metadata.total_items,
        pages=pagination_metadata.total_pages,
    )


@router.get("/states/all", response_model=list[schemas.StateGet])
async def list_all_states(
    country_id: uuid.UUID | None = fastapi.Query(default=None),
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
) -> list[schemas.StateGet]:
    async with uow_builder() as uow:
        stmt = (
            sa.select(models.State)
            .options(sa.orm.joinedload(models.State.country))
            .order_by(models.State.name.asc())
        )
        if country_id:
            stmt = stmt.where(models.State.country_id == country_id)
        result = await uow._session.execute(stmt)
        states = result.scalars().unique().all()
        return [schemas.StateGet.from_orm(s) for s in states]


@router.get(
    "/states/{state_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
    response_model=schemas.StateGet,
)
async def get_state(
    get_state_query: ports.GetState = fastapi_injector.Injected(ports.GetState),
    state_id: uuid.UUID = fastapi.Path(...),
) -> schemas.StateGet:
    state = await get_state_query(state_id=state_id)
    return schemas.StateGet.from_orm(state)


@router.post(
    "/states",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
    response_model=schemas.StateGet,
)
async def create_state(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    body: schemas.StateCreate = fastapi.Body(...),
) -> schemas.StateGet:
    state = models.State(**body.dict())
    async with uow_builder() as uow:
        state_model = await uow.state_repository.create(state)
        await uow.commit()
        # Populate relationship to avoid DetachedInstanceError
        country = await uow.country_repository.get(body.country_id)
        state_model.country = country
        return schemas.StateGet.from_orm(state_model)


@router.put(
    "/states/{state_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
    response_model=schemas.StateGet,
)
async def update_state(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    body: schemas.StateCreate = fastapi.Body(...),
    state_id: uuid.UUID = fastapi.Path(...),
) -> schemas.StateGet:
    async with uow_builder() as uow:
        state = await uow.state_repository.get(state_id)
        state.name = body.name
        state.code = body.code
        state.country_id = body.country_id
        await uow.commit()
        # Populate relationship to avoid DetachedInstanceError
        country = await uow.country_repository.get(body.country_id)
        state.country = country
        return schemas.StateGet.from_orm(state)


@router.delete(
    "/states/{state_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def delete_state(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    state_id: uuid.UUID = fastapi.Path(...),
) -> fastapi.Response:
    async with uow_builder() as uow:
        state = await uow.state_repository.get(state_id)
        await uow.state_repository.delete(state)
        await uow.commit()
    return fastapi.Response(status_code=fastapi.status.HTTP_204_NO_CONTENT)


# Cities


@router.get("/cities", response_model=schemas.CityList)
async def list_cities(
    state_id: uuid.UUID | None = fastapi.Query(default=None),
    list_data: util_schemas.ListSchema = fastapi.Depends(),
    list_cities_query: ports.ListCities = fastapi_injector.Injected(ports.ListCities),
) -> schemas.CityList:
    result, pagination_metadata = await list_cities_query(
        state_id=state_id,
        page_size=list_data.page_size,
        page=list_data.page,
        query=list_data.q,
    )
    return schemas.CityList(
        items=result,
        current_page=pagination_metadata.current_page,
        total=pagination_metadata.total_items,
        pages=pagination_metadata.total_pages,
    )


@router.get(
    "/cities/{city_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
    response_model=schemas.CityGet,
)
async def get_city(
    get_city_query: ports.GetCity = fastapi_injector.Injected(ports.GetCity),
    city_id: uuid.UUID = fastapi.Path(...),
) -> schemas.CityGet:
    city = await get_city_query(city_id=city_id)
    return schemas.CityGet.from_orm(city)


@router.post(
    "/cities",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
    response_model=schemas.CityGet,
)
async def create_city(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    body: schemas.CityCreate = fastapi.Body(...),
) -> schemas.CityGet:
    city = models.City(**body.dict())
    async with uow_builder() as uow:
        city_model = await uow.city_repository.create(city)
        await uow.commit()
        # Populate relationship to avoid DetachedInstanceError
        state = await uow.state_repository.get(body.state_id)
        city_model.state = state
        return schemas.CityGet.from_orm(city_model)


@router.put(
    "/cities/{city_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
    response_model=schemas.CityGet,
)
async def update_city(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    body: schemas.CityCreate = fastapi.Body(...),
    city_id: uuid.UUID = fastapi.Path(...),
) -> schemas.CityGet:
    async with uow_builder() as uow:
        city = await uow.city_repository.get(city_id)
        city.name = body.name
        city.state_id = body.state_id
        await uow.commit()
        # Populate relationship to avoid DetachedInstanceError
        state = await uow.state_repository.get(body.state_id)
        city.state = state
        return schemas.CityGet.from_orm(city)


@router.delete(
    "/cities/{city_id}",
    dependencies=[fastapi.Security(auth.get_token, scopes=["admin"])],
)
async def delete_city(
    uow_builder: ports.UnitOfWorkBuilder = fastapi_injector.Injected(
        ports.UnitOfWorkBuilder
    ),
    city_id: uuid.UUID = fastapi.Path(...),
) -> fastapi.Response:
    async with uow_builder() as uow:
        city = await uow.city_repository.get(city_id)
        await uow.city_repository.delete(city)
        await uow.commit()
    return fastapi.Response(status_code=fastapi.status.HTTP_204_NO_CONTENT)
