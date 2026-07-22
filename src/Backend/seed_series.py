import asyncio
import os
from api import create_container, models, ports

async def seed():
    container = create_container()
    uow_builder = container.get(ports.UnitOfWorkBuilder)
    async with uow_builder() as uow:
        series_data = [
            ("1º Ano", "1A"),
            ("2º Ano", "2A"),
            ("3º Ano", "3A"),
            ("4º Ano", "4A"),
            ("5º Ano", "5A"),
            ("6º Ano", "6A"),
            ("7º Ano", "7A"),
            ("8º Ano", "8A"),
            ("9º Ano", "9A"),
            ("1ª Série", "1S"),
            ("2ª Série", "2S"),
            ("3ª Série", "3S"),
        ]

        for name, code in series_data:
            series = models.Series(name=name, code=code)
            try:
                await uow.series_repository.create(series)
                print(f"Added series: {name}")
            except Exception as e:
                print(f"Error adding series {name}: {e}")

        try:
            await uow.commit()
            print("Successfully seeded series.")
        except Exception as e:
            print(f"Error committing series: {e}")
            await uow.rollback()

if __name__ == "__main__":
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k] = v.strip().strip('"').strip("'")

    asyncio.run(seed())
