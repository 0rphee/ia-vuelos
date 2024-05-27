from sqlalchemy import (
    create_engine,
    select,
)
from sqlalchemy.orm import sessionmaker

from ia_vuelos.lib import a_star, print_camino
from ia_vuelos.sqlalchemy import Airport

#################################################################################################
#################################################################################################


def main():
    # Create an engine and a session
    # CONNECTION_URL = "mysql+mysqlconnector://username:password@localhost/fly_data"
    # CONNECTION_URL = "mysql+mysqlconnector://root:root@db:3306/fly_data"

    CONNECTION_URL = "mysql+mysqlconnector://root:root@localhost:3306/fly_data"
    engine = create_engine(CONNECTION_URL, echo=False)  # echo=True shows the sql statements
    # Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        # 4731 MMMX large_airport Aeropuerto Internacional Lic. Benito Juárez
        # 2434 EGLL large_airport London Heathrow Airport
        origin_airport_id = 4731
        destination_airport_id = 2434

        cdmx_benito_juarez = session.execute(
            select(Airport).where(Airport.id == origin_airport_id).limit(1)
        ).scalar_one()

        london_heathrow = session.execute(
            select(Airport).where(Airport.id == destination_airport_id).limit(1)
        ).scalar_one()

        camino_resultante, aeropuerto_final = a_star(
            session, cdmx_benito_juarez, london_heathrow, imprimir=False
        )
        print_camino(camino_resultante, aeropuerto_final)


if __name__ == "__main__":
    main()
