from datetime import datetime

from flask import Flask, app, render_template, request
from sqlalchemy import (
    create_engine,
    select,
)
from sqlalchemy.orm import sessionmaker

from ia_vuelos.lib import a_star, print_camino
from ia_vuelos.sqlalchemy import Airport

# sqlalchemy
DB_CONNECTION_URL = "mysql+mysqlconnector://root:root@localhost:3306/fly_data"
engine = create_engine(DB_CONNECTION_URL, echo=False)  # echo=True shows the sql statements
# Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, bind=engine)

# flask
app = Flask(__name__)


def get_airports():
    with SessionLocal() as session:
        airports = session.query(Airport).all()
    return airports


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    if request.method == "POST":
        departure_airport_id = request.form["departure_airport"]
        arrival_airport_id = request.form["arrival_airport"]
        date_str = request.form["date"]
        date = datetime.strptime(date_str, "%Y-%m-%d")

        with SessionLocal() as session:
            departure_airport = (
                session.query(Airport).filter(Airport.id == departure_airport_id).first()
            )
            arrival_airport = (
                session.query(Airport).filter(Airport.id == arrival_airport_id).first()
            )

            # Call the A* function
            path, final_airport = a_star(session, departure_airport, arrival_airport, date)

        print_camino(path, final_airport)
        return render_template("result.html", path=path, final_airport=final_airport)

    airports = get_airports()
    return render_template("index.html", airports=airports)


def main():
    app.run(debug=True)


# def main():
#     # Create an engine and a session
#     # CONNECTION_URL = "mysql+mysqlconnector://username:password@localhost/fly_data"
#     # CONNECTION_URL = "mysql+mysqlconnector://root:root@db:3306/fly_data"

#     with SessionLocal() as session:
#         # 4731 MMMX large_airport Aeropuerto Internacional Lic. Benito Juárez
#         # 2434 EGLL large_airport London Heathrow Airport
#         origin_airport_id = 4731
#         destination_airport_id = 2434

#         cdmx_benito_juarez = session.execute(
#             select(Airport).where(Airport.id == origin_airport_id).limit(1)
#         ).scalar_one()

#         london_heathrow = session.execute(
#             select(Airport).where(Airport.id == destination_airport_id).limit(1)
#         ).scalar_one()

#         camino_resultante, aeropuerto_final = a_star(
#             session, cdmx_benito_juarez, london_heathrow, imprimir=False
#         )
#         print_camino(camino_resultante, aeropuerto_final)


if __name__ == "__main__":
    main()
