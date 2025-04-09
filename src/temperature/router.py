import asyncio
import os
from datetime import datetime

import httpx
from dotenv import load_dotenv
from fastapi import APIRouter, Depends
from httpx import AsyncClient
from sqlalchemy.orm import Session

from src.city.crud import get_cities
from src.city.models import CityModel
from src.database import get_db
from src.temperature.crud import get_temperatures, get_temperatures_one_city
from src.temperature.models import TemperatureModel

load_dotenv()
temperature_router = APIRouter()


async def send_request(
        city: CityModel,
        client: AsyncClient,
        db: Session
):
    response = await client.get(
        f"{os.getenv("BASE_URL")}?key={os.getenv("API_KEY")}&q={city.name}"
    )
    temperature = response.json().get("current", {}).get("temp_c")

    db_temperature = db.query(
        TemperatureModel
    ).filter(TemperatureModel.city_id == city.id).first()
    if db_temperature:
        db_temperature.temperature = temperature
        db_temperature.date_time = datetime.now()
    else:
        new_temperature = TemperatureModel(
            city_id=city.id,
            date_time=datetime.now(),
            temperature=temperature
        )
        db.add(new_temperature)
    return city


@temperature_router.post("/temperatures/update", status_code=200)
async def update_city_temperatures(db: Session = Depends(get_db)):
    cities = get_cities(db)

    async with httpx.AsyncClient() as client:
        tasks = [send_request(city, client, db) for city in cities]

        updated_cities = await asyncio.gather(*tasks)

    db.commit()
    for updated_city in updated_cities:
        db.refresh(updated_city)


@temperature_router.get("/temperatures/")
def get_temperatures_of_cities(db: Session = Depends(get_db)):
    return get_temperatures(db)


@temperature_router.get("/temperatures/?city_id={city_id}")
def get_temperatures_of_city(city_id: int, db: Session = Depends(get_db)):
    return get_temperatures_one_city(city_id, db)
