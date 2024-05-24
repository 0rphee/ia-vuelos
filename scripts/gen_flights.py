import random
import string
import sys
from datetime import datetime, timedelta
from math import floor

import mysql.connector
from geopy.distance import geodesic
from mysql.connector.cursor import MySQLCursor

"""
Rows in 'airports' table, in 'fly_data'
"id","ident","type","name","latitude_deg","longitude_deg","elevation_ft","continent","iso_country","iso_region","municipality","scheduled_service","gps_code","iata_code","local_code","home_link","wikipedia_link","keywords"
"""


class Airport:
    def __init__(self, row: tuple[int, str, str, str, float, float]) -> None:
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

    return list(map(lambda x: Airport(tuple(x)), cursor.fetchall()))


def generate_flight_id() -> str:
    """
    Obtener un id al azar único (esperemos) para un vuelo.
    """
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def calculate_duration(distance_km: float, speed_kmh: int) -> float:
    return distance_km / speed_kmh


# Generate flight prices
def generate_prices(distance_km: float) -> tuple[float, float]:
    base_price_economy = distance_km * 0.1  # Example base price per km
    price_economy = base_price_economy * random.uniform(0.85, 1.15)
    price_business = price_economy * random.uniform(1.15, 1.25)
    return round(price_business, 2), round(price_economy, 2)


# Generate dates for all days in 2024
def generate_all_dates() -> list[datetime]:
    start_date: datetime = datetime(2024, 1, 1)
    end_date: datetime = datetime(2024, 2, 1)  # flights for just one month
    delta: timedelta = end_date - start_date
    return [start_date + timedelta(days=i) for i in range(delta.days + 1)]


def generate_dest_airport(
    all_airports: list[Airport], orig_airport: Airport
) -> tuple[Airport, float]:
    dest_airport = random.choice(all_airports)
    distance_km: float = geodesic(
        (orig_airport.lat, orig_airport.lon),
        (dest_airport.lat, dest_airport.lon),
    ).km

    return (dest_airport, distance_km)


def build_single_flight(
    plane, orig_airport: Airport, dest_airport: Airport, date: datetime, distance_km: float
) -> Flight:
    flight_id: str = generate_flight_id()
    duration_hours: float = calculate_duration(distance_km, plane["speed"])
    # the departure time is at a random time in the day
    departure_time: datetime = date + timedelta(
        hours=random.randint(0, 23), minutes=random.randint(0, 59)
    )
    arrival_time: datetime = departure_time + timedelta(hours=duration_hours)
    price_business, price_economy = generate_prices(distance_km)

    return Flight(
        flight_id,
        plane["model"],
        price_business,
        price_economy,
        departure_time,
        arrival_time,
        orig_airport.id,
        dest_airport.id,
    )


def generate_flights(cursor: MySQLCursor) -> list[Flight]:
    all_airports: list[Airport] = get_airports(cursor)
    dates = generate_all_dates()
    flights: list[Flight] = []

    plane_models = [
        {"model": "Boeing 787-9", "speed": 903, "range": 14140},
        {"model": "Airbus A320neo", "speed": 833, "range": 6500},
    ]

    count = 0
    do_i_print = 24  # prints every 25 airports finished
    for curr_orig_airport in all_airports:
        flights_per_day: int = 0
        if curr_orig_airport.type == "large_airport":
            flights_per_day = random.randint(5, 10)
            long_haul_fligths = floor(flights_per_day * 0.5)
        else:
            flights_per_day = random.randint(1, 5)
            long_haul_fligths = floor(flights_per_day * 0.2)
        short_haul_fligths = flights_per_day - long_haul_fligths

        flight_indexes = ([0] * long_haul_fligths) + ([1] * short_haul_fligths)
        for date in dates:
            for plane_index in flight_indexes:
                plane = plane_models[plane_index]

                dest_airport, distance_km = generate_dest_airport(
                    all_airports,
                    curr_orig_airport,
                )
                while (dest_airport.id == curr_orig_airport.id) or (distance_km > plane["range"]):
                    dest_airport, distance_km = generate_dest_airport(
                        all_airports,
                        curr_orig_airport,
                    )

                flight = build_single_flight(
                    plane, curr_orig_airport, dest_airport, date, distance_km
                )

                flights.append(flight)

        count += 1
        do_i_print += 1
        if do_i_print == 25:
            # Actualizar el contador en la misma línea
            sys.stdout.write(f"\rAeropuertos terminados de generar: {count}")
            sys.stdout.flush()
            do_i_print = 0
    sys.stdout.write(f"\rAeropuertos terminados de generar: {count}\n")
    sys.stdout.flush()

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
