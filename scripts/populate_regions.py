import csv
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import sqlalchemy_utils
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ia_vuelos.sqlalchemy import Base, Region


def convert_row(row):
    # Convert empty strings to None
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
        print("Conexión lograda con mysql: insertando regiones")

        # Read the CSV file
        with open("data/regions.csv", "r") as csvfile:
            csvreader = csv.reader(csvfile)
            next(csvreader)  # Skip the header

            count = 0
            do_i_print = 24  # prints every 25 rows finished
            for row in csvreader:
                try:
                    # Adjust the length of the row to the number of columns expected
                    if len(row) < 8:
                        row += [None] * (8 - len(row))
                    # Convert and clean the row
                    cleaned_row = convert_row(row)

                    # Create a Region object
                    region = Region(
                        cleaned_row[0],
                        cleaned_row[1],
                        cleaned_row[2],
                        cleaned_row[3],
                        cleaned_row[4],
                        cleaned_row[5],
                        cleaned_row[6],
                        cleaned_row[7],
                    )

                    # Add the Region object to the session
                    session.add(region)
                    session.commit()
                    count += 1
                    do_i_print += 1
                    if do_i_print == 25:
                        # Update the counter on the same line
                        sys.stdout.write(f"\rFilas insertadas: {count}")
                        sys.stdout.flush()
                        do_i_print = 0
                except Exception as e:
                    session.rollback()
                    print(f"\nEXITING\nError {e} row:\n{row}\nEXITING")
                    raise e

            sys.stdout.write(f"\rFilas insertadas: {count}")
            sys.stdout.flush()
        print()


if __name__ == "__main__":
    main()
