import random
import string
from datetime import datetime, timedelta
from typing import Generator

import mysql.connector
from geopy.distance import geodesic
from mysql.connector.cursor import MySQLCursor
from mysql.connector.types import RowType

"""
Rows in 'airports' table, in 'fly_data'
"id","ident","type","name","latitude_deg","longitude_deg","elevation_ft","continent","iso_country","iso_region","municipality","scheduled_service","gps_code","iata_code","local_code","home_link","wikipedia_link","keywords"
"""


class Airport:
    def __init__(self, row: RowType) -> None:
        self.id: int = int(row[0])
        self.ident: str = str(row[1])
        self.type: str = str(row[2])
        self.name: str = str(row[3])
        self.lat: float = float(row[4])
        self.lon: float = float(row[5])


class Flight:
    def __init__(
        self,
        flight_id: str,
        model: str,
        price_business: float,
        price_economy: float,
        departure_time: datetime,
        arrival_time: datetime,
        departure_airport_id: int,
        arrival_airport_id: int,
    ) -> None:
        self.flight_id: str = flight_id
        self.model: str = model
        self.price_business: float = price_business
        self.price_economy: float = price_economy
        self.departure_time: datetime = departure_time
        self.arrival_time: datetime = arrival_time
        self.departure_airport_id: int = departure_airport_id
        self.arrival_airport_id: int = arrival_airport_id


def get_airports(cursor: MySQLCursor) -> list[Airport]:
    """
    Obtener todos los aeropuertos 'válidos' para generarles sus rutas.
    """
    cursor.execute(
        """
        SELECT id, ident, type, name, latitude_deg, longitude_deg
        FROM airports
        WHERE 
            type IN ('medium_airport', 'large_airport')
                AND
            scheduled_service IS TRUE
        ;
    """
    )

    return list(map(Airport, cursor.fetchall()))


def generate_flight_id() -> str:
    """
    Obtener un id al azar único (esperemos) para un vuelo.
    """
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def calculate_duration(distance_km: int, speed_kmh: int) -> float:
    return distance_km / speed_kmh


# Generate flight prices
def generate_prices(distance_km: int) -> tuple[float, float]:
    base_price_economy = distance_km * 0.1  # Example base price per km
    price_economy = base_price_economy * random.uniform(0.85, 1.15)
    price_business = price_economy * random.uniform(1.15, 1.25)
    return round(price_business, 2), round(price_economy, 2)


# Generate dates for all days in 2024
def generate_dates_for_2024() -> Generator[datetime, None, None]:
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    delta = end_date - start_date
    return (start_date + timedelta(days=i) for i in range(delta.days + 1))


def generate_flights(cursor: MySQLCursor) -> list[Flight]:
    airports = get_airports(cursor)
    flights = []

    plane_models = [
        {"model": "Boeing 787-9", "speed": 903, "range": 14140},
        {"model": "Airbus A320neo", "speed": 833, "range": 6500},
    ]

    dates = generate_dates_for_2024()

    for orig_airport in airports:
        # the daily flight number is greater for large airports
        num_flights_per_day = (
            random.randint(5, 15) if orig_airport.type == "large_airport" else random.randint(1, 5)
        )

        for date in dates:
            long_haul_flights_count = 0
            short_haul_flights_count = 0

            for _ in range(num_flights_per_day):
                # Determine if this flight should be long-haul or short-haul
                if orig_airport.type == "large_airport":
                    use_long_haul = long_haul_flights_count < num_flights_per_day * 0.5
                else:
                    use_long_haul = long_haul_flights_count < num_flights_per_day * 0.2

                plane = plane_models[0] if use_long_haul else plane_models[1]

                # we keep searching for destination airports if the destination == origin, or if
                # the distance to said airport is greater than the range provided by the current
                # plane
                dest_airport = random.choice(airports)
                distance_km = geodesic(
                    (orig_airport.lat, orig_airport.lon),
                    (dest_airport.lat, dest_airport.lon),
                ).km

                while (dest_airport.id == orig_airport.id) and (distance_km > plane["range"]):
                    dest_airport = random.choice(airports)
                    distance_km = geodesic(
                        (orig_airport.lat, orig_airport.lon),
                        (dest_airport.lat, dest_airport.lon),
                    ).km

                flight_id = generate_flight_id()
                duration_hours = calculate_duration(distance_km, plane["speed"])
                # the departure time is at a random time in the day
                departure_time = date + timedelta(
                    hours=random.randint(0, 23), minutes=random.randint(0, 59)
                )
                arrival_time = departure_time + timedelta(hours=duration_hours)
                price_business, price_economy = generate_prices(distance_km)

                flight = Flight(
                    flight_id,
                    plane["model"],
                    price_business,
                    price_economy,
                    departure_time,
                    arrival_time,
                    orig_airport.id,
                    dest_airport.id,
                )
                flights.append(flight)

                # Update counts of each type of flight for the current airport
                if use_long_haul:
                    long_haul_flights_count += 1
                else:
                    short_haul_flights_count += 1

    return flights


def main():
    db_connection = mysql.connector.connect(
        host="localhost",  # in docker: host=db
        port="3306",
        user="root",
        password="root",
        database="fly_data",
    )

    cursor: MySQLCursor = db_connection.cursor()
    flights = generate_flights(cursor)
    cursor.close()
    db_connection.close()

    # Print some of the generated flights
    for flight in flights[:10]:  # Just printing first 10 for brevity
        print(vars(flight))


if __name__ == "__main__":
    main()
