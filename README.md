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

## Dependencias

Se usa `pipreqs`: <https://github.com/bndr/pipreqs>.

Para actualizar `requirements.txt` basado en las dependencias utilizadas en el código.

```sh
pipreqs --ignore .venv
```

Para installar localmente las dependencias:

```sh
pip3 install -r requirements.txt
```

## Datos

El dataset de los aeropuertos fue obtenido de <https://ourairports.com/data/>. (Los datos se importaron/modificaron inicialmente mediante la interfaz de phpMyAdmin).

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
