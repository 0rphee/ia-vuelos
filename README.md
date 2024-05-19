# ia-vuelos

> [!important]
 Se necesita Docker: <https://docs.docker.com/get-docker/>
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

