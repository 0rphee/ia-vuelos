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
    plane, all_airports: list[Airport], orig_airport: Airport, date: datetime
) -> Flight:

    dest_airport, distance_km = generate_dest_airport(
        all_airports,
        orig_airport,
    )
    while (dest_airport.id == orig_airport.id) or (distance_km > plane["range"]):
        dest_airport, distance_km = generate_dest_airport(
            all_airports,
            orig_airport,
        )

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


def insert_flight(cursor: MySQLCursor, flight: Flight):
    insert_query = """
    INSERT INTO flights (
        flight_id, model, price_business, price_economy, departure_time, arrival_time,
        departure_airport_id, arrival_airport_id
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(
        insert_query,
        (
            flight.flight_id,
            flight.model,
            flight.price_business,
            flight.price_economy,
            flight.departure_time,
            flight.arrival_time,
            flight.departure_airport_id,
            flight.arrival_airport_id,
        ),
    )


def generate_flights(cursor: MySQLCursor):
    all_airports: list[Airport] = get_airports(cursor)
    dates = generate_all_dates()

    plane_models = [
        {"model": "Boeing 787-9", "speed": 903, "range": 14140},
        {"model": "Airbus A320neo", "speed": 833, "range": 6500},
    ]

    PRINT_INTERVAL = 1
    count = 0
    do_i_print = PRINT_INTERVAL - 1  # prints every 25 airports finished
    for curr_orig_airport in all_airports:
        flights_per_day: int = 0
        if curr_orig_airport.type == "large_airport":
            flights_per_day = random.randint(5, 10)
            long_haul_flights = floor(flights_per_day * 0.5)
        else:
            flights_per_day = random.randint(1, 5)
            long_haul_flights = floor(flights_per_day * 0.2)
        short_haul_flights = flights_per_day - long_haul_flights

        flight_indexes = [0 for _ in range(long_haul_flights)] + [
            1 for _ in range(short_haul_flights)
        ]
        for date in dates:
            for plane_index in flight_indexes:
                plane = plane_models[plane_index]


                while True:
                    flight = build_single_flight(plane, all_airports, curr_orig_airport, date)
                    try:
                        insert_flight(cursor, flight)
                        break  # Exit the loop if insert is successful
                    except mysql.connector.errors.IntegrityError as e:
                        print("\n\nIntegrityError: Probably duplicate key:", e)
                        print(f"\nIn Error Flight:\n{vars(flight)}\n")
                    except Exception as e:
                        print(f"\nEXITING\nError Flight:\n{vars(flight)}\nEXITING")
                        raise e

        count += 1
        do_i_print += 1
        if do_i_print == PRINT_INTERVAL:
            # Actualizar el contador en la misma línea
            sys.stdout.write(f"\rAeropuertos terminados de generar: {count}")
            sys.stdout.flush()
            do_i_print = 0
    sys.stdout.write(f"\rAeropuertos terminados de generar: {count}\n")
    sys.stdout.flush()


def create_flights_table(cursor: MySQLCursor):
    create_table_query = """
    CREATE TABLE IF NOT EXISTS flights (
        flight_id VARCHAR(10) PRIMARY KEY,
        model VARCHAR(50),
        price_business FLOAT,
        price_economy FLOAT,
        departure_time DATETIME,
        arrival_time DATETIME,
        departure_airport_id INT,
        arrival_airport_id INT,
        FOREIGN KEY (departure_airport_id) REFERENCES airports(id),
        FOREIGN KEY (arrival_airport_id) REFERENCES airports(id)
    )
    """
    cursor.execute(create_table_query)


def main():
    db_connection = mysql.connector.connect(
        host="localhost",  # in docker: host=db
        port="3306",
        user="root",
        password="root",
        database="fly_data",
    )

    cursor: MySQLCursor = db_connection.cursor()
    create_flights_table(cursor)
    db_connection.commit()

    generate_flights(cursor)
    db_connection.commit()

    cursor.close()
    db_connection.close()


if __name__ == "__main__":
    main()
