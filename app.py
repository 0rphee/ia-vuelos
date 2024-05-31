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
engine = create_engine(DB_CONNECTION_URL, echo=False)  # echo="debug" shows the sql statements
# Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, bind=engine)

# flask
app = Flask(__name__)
cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"


@app.route("/", methods=["GET", "POST"])
@cross_origin()
def index():
    return app.send_static_file("index.html")


@cross_origin()
@app.route("/get_continents", methods=["GET"])
def get_continents():
    with SessionLocal() as session:
        continents = session.query(Country.continent).distinct().all()
    return jsonify([str(continent[0]) for continent in continents])


@app.route("/get_countries", methods=["GET"])
@cross_origin()
def get_countries():
    # Extract the continent from the query parameters
    continent = request.args.get("continent")

    if not continent:
        return jsonify({"error": "'continent' parameter is required"}), 400

    # Query the database for countries in the specified continent
    with SessionLocal() as session:
        countries = session.query(Country).filter_by(continent=continent).all()

    # Return the list of country names as a JSON response
    return jsonify([{"code": country.code, "name": country.name} for country in countries])


@app.route("/get_airports", methods=["GET"])
@cross_origin()
def get_airports():
    # Extract the continent from the query parameters
    country = request.args.get("iso_country")

    if not country:
        return jsonify({"error": "'iso_country' parameter is required"}), 400

    # Query the database for airports in the specified country
    with SessionLocal() as session:
        airports = (
            session.query(Airport)
            .where(
                Airport.type.in_(("large_airport", "medium_airport"))
                & (Airport.iso_country == country)
            )
            .all()
        )

    # Return the list of country names as a JSON response
    return jsonify(
        [{"id": airport.id, "ident": airport.ident, "name": airport.name} for airport in airports]
    )


@app.route("/get_path", methods=["GET"])
@cross_origin()
def get_path():
    origin_id = request.args.get("origin_id")
    destination_id = request.args.get("destination_id")
    date_str = request.args.get("date")

    if not origin_id or not destination_id or not date_str:
        return (
            jsonify({"error": "origin_id, destination_id, and date parameters are required"}),
            400,
        )

    try:
        # Parse the date parameter
        date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

    with SessionLocal() as session:
        departure_airport = session.query(Airport).filter(Airport.id == origin_id).first()
        arrival_airport = session.query(Airport).filter(Airport.id == destination_id).first()
        print(departure_airport.pretty_str())
        print(arrival_airport.pretty_str())

        if not departure_airport or not arrival_airport:
            return jsonify({"error": "Invalid origin_id or destination_id"}), 404

        path, final_airport = a_star(session, departure_airport, arrival_airport, date)

    print_camino(path, final_airport)
    path = [
        {"airport": airport.to_dict(), "next_flight": flight.to_dict()} for airport, flight in path
    ]

    return jsonify({"path": path, "final_airport": final_airport.to_dict()})


def main_alt():
    def search(session, orig, dest):
        fst = session.execute(select(Airport).where(Airport.id == orig).limit(1)).scalar_one()

        snd = session.execute(select(Airport).where(Airport.id == dest).limit(1)).scalar_one()

        print(fst.pretty_str())
        print(snd.pretty_str())

        camino_resultante, aeropuerto_final = a_star(session, fst, snd, imprimir=True)
        print_camino(camino_resultante, aeropuerto_final)

    with SessionLocal() as session:
        search(session, 3, 26955)


def main():
    app.run(debug=True)  # , ssl_context="adhoc")


if __name__ == "__main__":
    main()
    # main_alt()
