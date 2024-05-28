import csv
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import sqlalchemy_utils
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ia_vuelos.sqlalchemy import Airport, Base


def convert_row(row):
    # Convertir "yes" a True y "no" a False para scheduled_service
    row[11] = True if row[11] == "yes" else False if row[11] == "no" else None
    # Convertir cadenas vacías a None
    return [None if field == "" else field for field in row]


def main():
    # Database connection string
    DATABASE_URI = "mysql+mysqlconnector://root:root@localhost:3306/fly_data"

    # Set up SQLAlchemy engine and session
    engine = create_engine(DATABASE_URI)
    Session = sessionmaker(bind=engine)

    if not sqlalchemy_utils.database_exists(engine.url):
        sqlalchemy_utils.create_database(engine.url)
    with Session() as session:

        # Create the tables if they don't exist
        Base.metadata.create_all(engine)
        print("Conexión lograda con mysql: insertando aeropuertos")

        # Leer el archivo CSV en modo streaming
        with open("data/airports.csv", "r") as csvfile:
            csvreader = csv.reader(csvfile)
            next(csvreader)  # Saltar la cabecera

            count = 0
            do_i_print = 24  # prints every 25 airports finished
            for row in csvreader:
                try:
                    # Ajustar la longitud de la fila a la cantidad de columnas esperadas
                    if len(row) < 18:
                        row += [None] * (18 - len(row))
                    # Convertir y limpiar la fila
                    cleaned_row = convert_row(row)

                    # Create an Airport object
                    airport = Airport(
                        cleaned_row[0],
                        cleaned_row[1],
                        cleaned_row[2],
                        cleaned_row[3],
                        cleaned_row[4],
                        cleaned_row[5],
                        cleaned_row[6],
                        cleaned_row[7],
                        cleaned_row[8],
                        cleaned_row[9],
                        cleaned_row[10],
                        cleaned_row[11],
                        cleaned_row[12],
                        cleaned_row[13],
                        cleaned_row[14],
                        cleaned_row[15],
                        cleaned_row[16],
                        cleaned_row[17],
                    )

                    # Add the Airport object to the session
                    session.add(airport)
                    session.commit()
                    count += 1
                    do_i_print += 1
                    if do_i_print == 25:
                        # Actualizar el contador en la misma línea
                        sys.stdout.write(f"\rFilas insertadas: {count}")
                        sys.stdout.flush()
                        do_i_print = 0
                except Exception as e:
                    session.rollback()
                    print(f"\nEXITING\nError row:\n{row}\nEXITING")
                    raise e

            sys.stdout.write(f"\rFilas insertadas: {count}")
            sys.stdout.flush()
        print()


if __name__ == "__main__":
    main()
