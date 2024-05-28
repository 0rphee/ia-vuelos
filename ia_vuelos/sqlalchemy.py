from __future__ import annotations

from datetime import datetime, timedelta

from geopy.distance import geodesic
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Double,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship


# Define the base class
class Base(DeclarativeBase):
    pass


class Flight(Base):
    __tablename__ = "flights"

    flight_id = Column(String(10), primary_key=True)
    model = Column(String(50))
    price_business = Column(Float)
    price_economy = Column(Float)
    departure_time = Column(DateTime)
    arrival_time = Column(DateTime)
    departure_airport_id = Column(Integer, ForeignKey("airports.id"))
    arrival_airport_id = Column(Integer, ForeignKey("airports.id"))

    departure_airport = relationship(
        "Airport", foreign_keys=[departure_airport_id], back_populates="departures"
    )
    arrival_airport = relationship(
        "Airport", foreign_keys=[arrival_airport_id], back_populates="arrivals"
    )

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
        super().__init__(
            flight_id=flight_id,
            model=model,
            price_business=price_business,
            price_economy=price_economy,
            departure_time=departure_time,
            arrival_time=arrival_time,
            departure_airport_id=departure_airport_id,
            arrival_airport_id=arrival_airport_id,
        )

    def __repr__(self) -> str:
        return f"Flight(flight_id={self.flight_id!s}, model={self.model!s}, price_business={self.price_business!s}, price_economy={self.price_economy!s}, departure_time={self.departure_time!s}, arrival_time={self.arrival_time!s}, departure_airport_id={self.departure_airport_id!s}, arrival_airport_id={self.arrival_airport_id!s})"

    def pretty_str(self) -> str:
        return f"""
Flight:
    flight_id = {self.flight_id!s}
    model = {self.model!s}
    departure_time = {self.departure_time!s}
    arrival_time = {self.arrival_time!s}
    departure_airport_id = {self.departure_airport_id!s}
    arrival_airport_id = {self.arrival_airport_id}"""


class Airport(Base):
    __tablename__ = "airports"

    id = Column(Integer, primary_key=True)
    ident = Column(String(10), unique=True)
    type = Column(String(50))
    name = Column(String(100))
    latitude_deg = Column(Double)
    longitude_deg = Column(Double)
    elevation_ft = Column(Integer)
    continent = Column(String(2))
    iso_country = Column(String(2), ForeignKey("countries.code"))
    iso_region = Column(String(10), ForeignKey("regions.code"))
    municipality = Column(String(100))
    scheduled_service = Column(Boolean)
    gps_code = Column(String(10))
    iata_code = Column(String(10))
    local_code = Column(String(10))
    home_link = Column(Text)
    wikipedia_link = Column(Text)
    keywords = Column(Text)

    departures = relationship(
        "Flight", foreign_keys="Flight.departure_airport_id", back_populates="departure_airport"
    )
    arrivals = relationship(
        "Flight", foreign_keys="Flight.arrival_airport_id", back_populates="arrival_airport"
    )

    country = relationship("Country", back_populates="airports")
    region = relationship("Region", back_populates="airports")

    def __init__(
        self,
        id: int,
        ident: int,
        type: int,
        name: int,
        latitude_deg: int,
        longitude_deg: int,
        elevation_ft: int | None = None,
        continent: int | None = None,
        iso_country: int | None = None,
        iso_region: int | None = None,
        municipality: int | None = None,
        scheduled_service: int | None = None,
        gps_code: int | None = None,
        iata_code: int | None = None,
        local_code: int | None = None,
        home_link: int | None = None,
        wikipedia_link: int | None = None,
        keywords: int | None = None,
    ) -> None:
        super().__init__(
            id=id,
            ident=ident,
            type=type,
            name=name,
            latitude_deg=latitude_deg,
            longitude_deg=longitude_deg,
            elevation_ft=elevation_ft,
            continent=continent,
            iso_country=iso_country,
            iso_region=iso_region,
            municipality=municipality,
            scheduled_service=scheduled_service,
            gps_code=gps_code,
            iata_code=iata_code,
            local_code=local_code,
            home_link=home_link,
            wikipedia_link=wikipedia_link,
            keywords=keywords,
        )

    def __repr__(self) -> str:
        return f"Airport(id={self.id!r}, ident={self.ident!r}, type={self.type!r}, name={self.name!r}, latitude_deg={self.latitude_deg!r}, longitude_deg={self.longitude_deg!r}, elevation_ft={self.elevation_ft!r}, continent={self.continent!r}, iso_country={self.iso_country!r}, iso_region={self.iso_region!r}, municipality={self.municipality!r}, scheduled_service={self.scheduled_service!r}, gps_code={self.gps_code!r}, iata_code={self.iata_code!r}, local_code={self.local_code!r}, home_link={self.home_link!r}, wikipedia_link={self.wikipedia_link!r}, keywords={self.keywords!r})"

    def pretty_str(self) -> str:
        return f"""
Airport:
    id = {self.id!s}
    ident = {self.ident!s}
    type = {self.type!s}
    name = {self.name!s}
    continent = {self.continent!s}
    iso_country = {self.iso_country!s}
    iso_region = {self.iso_region!s}
    municipality = {self.municipality!s}
    iata_code = {self.iata_code!s}
    local_code = {self.local_code!s} """

    def get_neighboring_flights(
        self,
        session: Session,
        start_date: datetime,  # pyright: ignore [reportRedeclaration]
    ) -> list[tuple[Flight, Airport]]:
        # dates available from 2024-01-01 to 2024-02-01

        start_date: datetime = datetime(start_date.year, start_date.month, start_date.day)
        end_date = start_date + timedelta(days=1)

        # Query for flights (and the destination airpor) departing from the
        # specified airport on the specified date
        results = (
            session.execute(
                select(Flight, Airport).where(
                    Flight.departure_airport_id == self.id,
                    Flight.arrival_airport_id == Airport.id,
                    Flight.departure_time >= start_date,
                    Flight.departure_time < end_date,
                )
            )
            .tuples()
            .fetchall()
        )

        # Convert results to a list
        flights = list(results)

        return flights

    def calc_distance_airports(self, airport2: Airport) -> float:
        return float(
            geodesic(
                (self.latitude_deg, self.longitude_deg),
                (airport2.latitude_deg, airport2.longitude_deg),
            ).km
        )


class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True)
    code = Column(String(2), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    continent = Column(String(2), nullable=False)
    wikipedia_link = Column(Text)
    keywords = Column(Text)

    regions = relationship("Region", back_populates="country")
    airports = relationship("Airport", back_populates="country")

    def __init__(
        self, id: int, code: str, name: str, continent: str, wikipedia_link: str, keywords: str
    ):
        super().__init__(
            id=id,
            code=code,
            name=name,
            continent=continent,
            wikipedia_link=wikipedia_link,
            keywords=keywords,
        )


class Region(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False)
    local_code = Column(String(10), nullable=False)
    name = Column(String(100), nullable=False)
    continent = Column(String(2), nullable=False)
    iso_country = Column(String(2), ForeignKey("countries.code"), nullable=False)
    wikipedia_link = Column(Text)
    keywords = Column(Text)

    country = relationship("Country", back_populates="regions")
    airports = relationship("Airport", back_populates="region")

    def __init__(
        self,
        id: int,
        code: str,
        local_code: str,
        name: str,
        continent: str,
        iso_country: str,
        wikipedia_link: str,
        keywords: str,
    ):
        super().__init__(
            id=id,
            code=code,
            local_code=local_code,
            name=name,
            continent=continent,
            iso_country=iso_country,
            wikipedia_link=wikipedia_link,
            keywords=keywords,
        )
