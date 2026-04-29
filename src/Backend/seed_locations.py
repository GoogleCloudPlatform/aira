import asyncio
import os
from api import create_container, models, ports


async def seed_locations():
    container = create_container()
    uow_builder = container.get(ports.UnitOfWorkBuilder)

    async with uow_builder() as uow:
        # Create Default Country
        countries = await uow.country_repository.list()
        country_model = next((c for c in countries if c.code == "BR"), None)

        if not country_model:
            country = models.Country(name="Brasil", code="BR", is_default=True)
            try:
                country_model = await uow.country_repository.create(country)
                print(f"Created country: {country_model.name}")
            except Exception as e:
                print(f"Error creating country: {e}")
                return
        else:
            print("Country Brasil already exists.")

        states_data = [
            {"code": "AC", "name": "Acre"},
            {"code": "AL", "name": "Alagoas"},
            {"code": "AP", "name": "Amapá"},
            {"code": "AM", "name": "Amazonas"},
            {"code": "BA", "name": "Bahia"},
            {"code": "CE", "name": "Ceará"},
            {"code": "DF", "name": "Distrito Federal"},
            {"code": "ES", "name": "Espírito Santo"},
            {"code": "GO", "name": "Goiás"},
            {"code": "MA", "name": "Maranhão"},
            {"code": "MT", "name": "Mato Grosso"},
            {"code": "MS", "name": "Mato Grosso do Sul"},
            {"code": "MG", "name": "Minas Gerais"},
            {"code": "PA", "name": "Pará"},
            {"code": "PB", "name": "Paraíba"},
            {"code": "PR", "name": "Paraná"},
            {"code": "PE", "name": "Pernambuco"},
            {"code": "PI", "name": "Piauí"},
            {"code": "RJ", "name": "Rio de Janeiro"},
            {"code": "RN", "name": "Rio Grande do Norte"},
            {"code": "RS", "name": "Rio Grande do Sul"},
            {"code": "RO", "name": "Rondônia"},
            {"code": "RR", "name": "Roraima"},
            {"code": "SC", "name": "Santa Catarina"},
            {"code": "SP", "name": "São Paulo"},
            {"code": "SE", "name": "Sergipe"},
            {"code": "TO", "name": "Tocantins"},
        ]

        for state_info in states_data:
            # Check if state exists
            states = await uow.state_repository.list(
                country_id=country_model.id
            )
            state_model = next(
                (s for s in states if s.code == state_info["code"]), None
            )

            if not state_model:
                state = models.State(
                    name=state_info["name"],
                    code=state_info["code"],
                    country_id=country_model.id,
                )
                try:
                    await uow.state_repository.create(state)
                    print(f"Created state: {state.name}")
                except Exception as e:
                    print(
                        f"Error creating state {state_info['name']}: {e}"
                    )
            else:
                print(f"State {state_info['name']} already exists.")

        await uow.commit()


if __name__ == "__main__":
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k] = v

    asyncio.run(seed_locations())
