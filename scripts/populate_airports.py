import csv
import mysql.connector
import sys

# Crear la tabla si no existe
create_table_query = """
CREATE TABLE IF NOT EXISTS airports (
    id INT PRIMARY KEY,
    ident VARCHAR(10),
    type VARCHAR(50),
    name VARCHAR(100),
    latitude_deg DOUBLE,
    longitude_deg DOUBLE,
    elevation_ft INT,
    continent VARCHAR(2),
    iso_country VARCHAR(2),
    iso_region VARCHAR(10),
    municipality VARCHAR(100),
    scheduled_service BOOL,
    gps_code VARCHAR(10),
    iata_code VARCHAR(10),
    local_code VARCHAR(10),
    home_link TEXT,
    wikipedia_link TEXT,
    keywords TEXT,
    INDEX (ident)
)
"""

# Definir la consulta de inserción
insert_query = """
    INSERT INTO airports (
        id, ident, type, name, latitude_deg, longitude_deg, elevation_ft, continent,
        iso_country, iso_region, municipality, scheduled_service, gps_code,
        iata_code, local_code, home_link, wikipedia_link, keywords
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


def convert_row(row):
    # Convertir "yes" a True y "no" a False para scheduled_service
    row[11] = True if row[11] == "yes" else False if row[11] == "no" else None
    # Convertir cadenas vacías a None
    return [None if field == "" else field for field in row]


def main():
    with mysql.connector.connect(
        host="localhost",  # en docker: host=db
        port="3306",
        user="root",
        password="root",
        database="fly_data",
    ) as db_connection:

        # Crear un cursor
        cursor = db_connection.cursor()

        print("Conexión lograda con mysql")
        cursor.execute(create_table_query)
        db_connection.commit()

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
                    cursor.execute(insert_query, cleaned_row)
                    db_connection.commit()
                    count += 1
                    do_i_print += 1
                    if do_i_print == 25:
                        # Actualizar el contador en la misma línea
                        sys.stdout.write(f"\rFilas insertadas: {count}")
                        sys.stdout.flush()
                        do_i_print = 0
                except Exception as e:
                    print(f"\nEXITING\nError row:\n{row}\nEXITING")
                    raise e

            sys.stdout.write(f"\rFilas insertadas: {count}")
            sys.stdout.flush()
        print()
        # Cerrar el cursor y la conexión
        cursor.close()
        db_connection.close()


if __name__ == "__main__":
    main()
