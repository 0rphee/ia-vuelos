from datetime import datetime

from flask import Flask, app, jsonify, render_template, request
from flask_cors import CORS, cross_origin
from sqlalchemy import (
    create_engine,
    select,
)
from sqlalchemy.orm import sessionmaker

from ia_vuelos.lib import a_star, print_camino
from ia_vuelos.sqlalchemy import Airport, Country

# sqlalchemy
DB_CONNECTION_URL = "mysql+mysqlconnector://root:root@localhost:3306/fly_data"
engine = create_engine(DB_CONNECTION_URL, echo=False)  # echo=True shows the sql statements
# Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, bind=engine)

# flask
app = Flask(__name__)
cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"


@app.route("/", methods=["GET", "POST"])
@cross_origin()
def index():
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
        return render_template("res.html", path=path, final_airport=final_airport)

    with SessionLocal() as session:
        continents = session.query(Country.continent).distinct().all()
    return render_template("ind.html", continents=continents)


@cross_origin()
@app.route("/get_continents", methods=["GET"])
def get_continents():
    with SessionLocal() as session:
        continents = session.query(Country.continent).distinct().all()
    return jsonify([str(continent[0]) for continent in continents])


@app.route("/get_countries", methods=["POST"])
@cross_origin()
def get_countries():
    continent = request.json["continent"]
    with SessionLocal() as session:
        countries = session.query(Country).filter_by(continent=continent).all()
    return jsonify([country.name for country in countries])


@app.route("/get_airports", methods=["POST"])
@cross_origin()
def get_airports():
    country = request.json["country"]
    with SessionLocal() as session:
        airports = session.query(Airport).filter_by(iso_country=country).all()
    return jsonify([{"id": airport.id, "name": airport.name} for airport in airports])


def main():
    app.run(debug=True)  # , ssl_context="adhoc")


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
