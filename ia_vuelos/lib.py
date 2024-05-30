from collections import OrderedDict
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from ia_vuelos.sqlalchemy import Airport, Flight


def print_camino(airport_flight_history: list[tuple[Airport, Flight]], aeropuerto_final: Airport):
    """
    Se imprime la visualización del camino
    """
    arrow_text = """
      ;;
    ..;;..
     '::'
      ''
    """
    string = (arrow_text + "\n").join(
        map(
            lambda x: f"Arrived to: {x[0].pretty_str()}, from: {x[1].pretty_str()}",
            airport_flight_history,
        )
    )

    string += string + f"{arrow_text}{'-'*18}\nFINAL DESTINATION: {aeropuerto_final.pretty_str()}"

    print(f"\n{'='*10}")
    print("RESULTADO DE LA BÚSQUEDA:")
    print(string)
    print("=" * 10)


def a_star(
    sqlalchemy_session: Session,
    aeropuerto_inical: Airport,
    aeropuerto_objetivo: Airport,
    salida_primer_vuelo: datetime = datetime(year=2024, month=1, day=1),
    imprimir=False,
) -> tuple[list[tuple[Airport, Flight]], Airport]:
    """
    Se devuelve el camino del aeropuerto inicial al final de forma:
    - `[(primer_aeropuerto, vuelo_que_sale_de_ahí), ..., (penúltimo_aeropuerto, vuelo_a_aeropuerto_objetivo)]`.

    Además de esta lista, se regresa también el aeropuerto objetivo (final/último), en una tupla:
    - `([(Airport, Flight)], Airport)`
    """

    def fun_costo_heuristico_h(orig_airport: Airport, destination_airport: Airport) -> float:
        return orig_airport.calc_distance_airports(destination_airport)

    def fun_costo_real_g(
        flight_to_current_airport: datetime | Flight, flight_to_next_airport: Flight
    ) -> timedelta:
        # si es datetime, estamos en los vecinos del primer aeropuerto de origen
        if isinstance(flight_to_current_airport, datetime):
            tiempo_espera_a_siguiente_vuelo: timedelta = timedelta(0)
            duracion_vuelo: timedelta = timedelta(0)
        else:
            tiempo_espera_a_siguiente_vuelo: timedelta = (
                flight_to_next_airport.departure_time
                - flight_to_current_airport.arrival_time  # pyright: ignore [reportAssignmentType]
            )
            duracion_vuelo: timedelta = (
                flight_to_next_airport.arrival_time
                - flight_to_next_airport.departure_time  # pyright: ignore [reportAssignmentType]
            )
        costo_g_adicional_actual = tiempo_espera_a_siguiente_vuelo + duracion_vuelo
        return costo_g_adicional_actual

    def make_ordered_list_of_states(
        origin_airport: Airport,
        destination_airport: Airport,
        # last_flight_to_destination_airport: Flight,
        came_from_dict: dict[Airport, tuple[Airport, Flight]],
    ) -> tuple[list[tuple[Airport, Flight]], Airport]:
        """
        Dada la lista de procedencias `came_from` y un estado inicial y final, se
        devuelve el camino del aeropuerto inicial al final de forma:
        - `[(primer_aeropuerto, vuelo_que_sale_de_ahí), ..., (penúltimo_aeropuerto, vuelo_a_aeropuerto_objetivo)]`.

        Además de esta lista, se regresa también el aeropuerto objetivo (final/último), en una tupla:
        - `([(Airport, Flight)], Airport)`
        """
        airport_origin_dest_list: list[tuple[Airport, Flight]] = []
        last_airport = destination_airport
        while last_airport != origin_airport:
            last_airport, flight = came_from_dict[last_airport]
            airport_origin_dest_list.append((last_airport, flight))
        airport_origin_dest_list = list(reversed(airport_origin_dest_list))
        return (airport_origin_dest_list, destination_airport)

    aeropuerto_inical = aeropuerto_inical
    aeropuerto_objetivo = aeropuerto_objetivo

    """
    Las llaves son los aeropuertos, y sus valores son:
    - Costo g: costo real, tiempo para llegar a ese aeropuerto
    - Costo f: costo_g.total_seconds() + costo_h
        - Costo h: costo heurístico, distancia con el aeropuerto final y el aeropuerto actual
    Aquellos aeropuertos en `open_list` son los nodos a explorar
    """
    open_list: OrderedDict[Airport, tuple[timedelta, float, datetime | Flight]] = OrderedDict(
        {
            aeropuerto_inical: (
                timedelta(0),  # g_score: costo real, timedelta
                0
                + fun_costo_heuristico_h(
                    aeropuerto_inical, aeropuerto_objetivo
                ),  # f_score (g + h score)
                salida_primer_vuelo,
            )
        }
    )

    # Diccionario de los costos reales (número de movientos, desde el tablero inicial) para llegar a cierto estado.
    # el costo real es el tiempo tomado
    g_scores: dict[Airport, timedelta] = {aeropuerto_inical: timedelta(0)}

    # Diccionario que almacena que airport es el anterior: {airport1: airport2}, el airport1 viene del airport2
    came_from: dict[Airport, tuple[Airport, Flight]] = {}

    while open_list:
        # Se ordena para que los elementos con menor coste estén al final del diccionario: {estado1: (1,1), estado2: (1,3)} -> {estado2: (1,3), estado1: (1,1)}
        open_list = OrderedDict(
            sorted(open_list.items(), key=lambda estado: estado[1][1], reverse=True)
        )

        current_airport, _current_airport_cost = open_list.popitem()
        _current_costo_g, _current_costo_h, current_vuelo_origen = _current_airport_cost

        if imprimir is True:
            print("----------------------")
            print("Estado actual:")
            print(current_airport.pretty_str())

        if current_airport == aeropuerto_objetivo:
            # Se reconstruye el caminio, terminando la iteración y regresamos el resultado final de la búsqueda
            return make_ordered_list_of_states(aeropuerto_inical, aeropuerto_objetivo, came_from)

        neighbors = map(
            lambda available_flight: available_flight,
            current_airport.get_neighboring_flights(
                sqlalchemy_session,
                (
                    current_vuelo_origen  # pyright: ignore [reportArgumentType]
                    if (isinstance(current_vuelo_origen, datetime))
                    else current_vuelo_origen.arrival_time
                ),
            ),
        )

        for flight_to_neighbor_airport, current_neighbor_airport in neighbors:
            # Costo (tentativo) de moverse al vecino
            # el costo es tomado como el tiempo de llegada

            # si es datetime, estamos en los vecinos del primer aeropuerto de origen
            costo_g_adicional: timedelta = fun_costo_real_g(
                current_vuelo_origen, flight_to_neighbor_airport
            )

            tentative_g_score_of_current_neighbor_airport: timedelta = (
                g_scores[current_airport] + costo_g_adicional
            )

            if (current_neighbor_airport not in g_scores) or (
                tentative_g_score_of_current_neighbor_airport < g_scores[current_neighbor_airport]
            ):
                # si (no se ha llegado a este estado antes) o (el costo de este camino
                # a esete estado es menor a costos encontrados antes), entonces:

                # añadimos a la lista de procedencia a los aeropuertos vecinos, indicando
                # que vendrían del current_airport y aunque compartan el mismo aeropuerto
                # de origen, el vuelo es distinto
                came_from[current_neighbor_airport] = (current_airport, flight_to_neighbor_airport)

                # añadimos el (hasta ahora) mejor costo encontrado para llegar a neighbor_state
                g_scores[current_neighbor_airport] = tentative_g_score_of_current_neighbor_airport

                # añadimos el vecino con su costo heurístico a la lista de estados por explorar
                f_score: (
                    float
                ) = tentative_g_score_of_current_neighbor_airport.total_seconds() + fun_costo_heuristico_h(
                    current_neighbor_airport, aeropuerto_objetivo
                )
                open_list[current_neighbor_airport] = (
                    tentative_g_score_of_current_neighbor_airport,
                    f_score,
                    flight_to_neighbor_airport,
                )

                if imprimir is True:
                    print("Estado vecino")
                    print(current_neighbor_airport.pretty_str())
                    print("Costo", f_score)
    return ([], aeropuerto_objetivo)
