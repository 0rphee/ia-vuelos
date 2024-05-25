from datetime import datetime


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
