# ia-vuelos

> [!important]
> Se necesita Docker: <https://docs.docker.com/get-docker/>
> y Git <https://git-scm.com/downloads>

## Preview

...

## Lanzar el proyecto en Docker

Primero se clona el proyecto:

```sh
git clone https://github.com/0rphee/ia-vuelos.git
cd ia-vuelos
```

Una vez hecho esto, **se abre la aplicación de Docker Desktop** y se ejecuta esto en la terminal:

```sh
docker compose up --build
```

Alternativamente, se puede usar este comando para lanzarlos otra vez cada que se modifica algún archivo:

```sh
docker compose watch
```

- PhpMyAdmin (para el manejo de MySql) estará disponible en <http://localhost:8080/> (con usuario root, contraseña root).
- Y la aplicación estará en <http://localhost:8000/>.

## Dependencias

Para installar localmente las dependencias:

### Python: 

```sh
pip3 install -r requirements.txt
```

### Elm:

```
# Se necesita tener instalado node.
npm install -g elm

elm make src/Main.elm --optimize --output=static/index.html

# o se puede user `elm reactor` para tener un servidor interactivo de Elm.
```


## Datos

El dataset de los aeropuertos fue obtenido de <https://ourairports.com/data/>. (Los datos se importaron/modificaron inicialmente mediante la interfaz de phpMyAdmin).

### Llenar base de datos

```sh
# Se ejecuta esto en la misma terminal, si no funciona leer siguiente párrafo
mkdir data
curl 'https://davidmegginson.github.io/ourairports-data/airports.csv' -o data/airports.csv
curl 'https://davidmegginson.github.io/ourairports-data/countries.csv' -o data/countries.csv
curl 'https://davidmegginson.github.io/ourairports-data/regions.csv' -o data/regions.csv
```

Si el comando anterior no funciona, se descargan manualmente los archivos `airports.csv`, `countries.csv` y `regions.csv` de <https://ourairports.com/data/>, y colocarlos en `data/`. 

Una vez descargado, se debe el servicio de docker de mysql debe estar corriendo, y se insertan la información a la base de datos ejecutando (esto con la base de datos corriendo):

```sh
python3 scripts/populate_countries.py
python3 scripts/populate_regions.py
python3 scripts/populate_airports.py 
python3 scripts/populate_flights.py
```

### Generar datos de vuelos

De todos los aeropuertos disponibles, para generar los vuelos se usan solamente aquellos que cumplen las siguientes condiciones:

- Tienen servicio de aerolíneas/vuelos regular.
- Según su tamaño:
  - [x] "large_airport"
  - [x] "medium_airport"
  - [ ] "small_airport"
  - [ ] "balloonport"
  - [ ] "seaplane_base"
  - [ ] "heliport"
  - [ ] "closed"

La generación de rutas se hizo tomando en cuenta dos modelos de avión:

- Boeing 787-9:
  - Velocidad de crucero: `~903 km/h`.
  - Rango máximo: `14,140 km`.
- Airbus A320neo:
  - Velocidad de crucero: `~833 km/h`.
  - Rango máximo: `6,500 km`.

El código de generación de vuelos se encuentra en `scripts/gen_flights.py`, y solo es ejecutado una vez para popular la tabla `flights`.
