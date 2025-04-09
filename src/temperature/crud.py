from fastapi import Depends
from sqlalchemy.orm import Session

from src.database import get_db
from src.temperature.models import TemperatureModel


def get_temperatures(db: Session = Depends(get_db)):
    return db.query(TemperatureModel).all()


def get_temperatures_one_city(city_id: int, db: Session = Depends(get_db)):
    return db.query(
        TemperatureModel
    ).filter(TemperatureModel.city_id == city_id).first()
