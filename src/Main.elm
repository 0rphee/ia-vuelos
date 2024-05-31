module Main exposing (Model, Msg(..), init, main, subscriptions, update, view)

import Browser
import Date exposing (Date)
import Dict exposing (Dict)
import Html exposing (Html, button, div, h1, h2, h3, input, li, option, p, select, text, ul)
import Html.Attributes exposing (href, placeholder, rel, type_, value)
import Html.Events exposing (onClick, onInput)
import Http
import Json.Decode as Json exposing (Decoder)
import Time exposing (Month(..))
import Tuple exposing (first)



-- MAIN


main : Program () Model Msg
main =
    Browser.element
        { init = init
        , update = update
        , subscriptions = subscriptions
        , view = view
        }



-- MODEL


type alias Model =
    { originAirport : FinalNodesInfo
    , destinationAirport : FinalNodesInfo
    , date : ( String, Maybe Date.Date )
    , path : Maybe PathData
    }


type alias FinalNodesInfo =
    { selectedContinent : Maybe Continent
    , selectedCountry : Maybe Country
    , countryOptions : Maybe (Dict String Country) -- Int: id, String: name
    , airportOptions : Maybe (Dict Int Airport)
    , selectedAirport : Maybe Airport
    }


type Continent
    = Continent { code : String, name : String }


type Country
    = Country { code : String, name : String }


type alias Airport =
    { id : Int
    , ident : String
    , name : String
    }


type alias Flight =
    { flightId : String
    , model : String
    , priceBusiness : Float
    , priceEconomy : Float
    , departureTime : String
    , arrivalTime : String
    , departureAirportId : Int
    , arrivalAirportId : Int
    }


type alias PathItem =
    { airport : Airport
    , nextFlight : Flight
    }


type alias PathData =
    { finalAirport : Airport
    , path : List PathItem
    }


continentDictionary : Dict String Continent
continentDictionary =
    Dict.fromList
        [ ( "AS", Continent { code = "AS", name = "Asia" } )
        , ( "AN", Continent { code = "AN", name = "Antarctica" } )
        , ( "AF", Continent { code = "AF", name = "Africa" } )
        , ( "OC", Continent { code = "OC", name = "Oceania" } )
        , ( "EU", Continent { code = "EU", name = "Europe" } )
        , ( "NA", Continent { code = "NA", name = "North America" } )
        , ( "SA", Continent { code = "SA", name = "South America" } )
        ]


setOriginNode : FinalNodesInfo -> Model -> Model
setOriginNode airportInfo model =
    { model | originAirport = airportInfo }


setDestinationNode : FinalNodesInfo -> Model -> Model
setDestinationNode airportInfo model =
    { model | destinationAirport = airportInfo }


setNodeContinent : Maybe Continent -> FinalNodesInfo -> FinalNodesInfo
setNodeContinent continent airportInfo =
    { airportInfo | selectedContinent = continent }


setNodeCountry : Maybe Country -> FinalNodesInfo -> FinalNodesInfo
setNodeCountry country airportInfo =
    { airportInfo | selectedCountry = country }


setNodeCountryOptions : Maybe (Dict String Country) -> FinalNodesInfo -> FinalNodesInfo
setNodeCountryOptions countryOptions airportInfo =
    { airportInfo | countryOptions = countryOptions }


setNodeAirport : Maybe Airport -> FinalNodesInfo -> FinalNodesInfo
setNodeAirport country airportInfo =
    { airportInfo | selectedAirport = country }


setNodeAirportOptions : Maybe (Dict Int Airport) -> FinalNodesInfo -> FinalNodesInfo
setNodeAirportOptions airportOptions airportInfo =
    { airportInfo | airportOptions = airportOptions }


getNodeCountryOptions : FinalNodesInfo -> Maybe (Dict String Country)
getNodeCountryOptions node =
    node.countryOptions


getNodeAirportOptions : FinalNodesInfo -> Maybe (Dict Int Airport)
getNodeAirportOptions node =
    node.airportOptions


countryToString : Country -> String
countryToString (Country c) =
    c.name


airportToString : Airport -> String
airportToString c =
    c.name ++ " (" ++ c.ident ++ ")"


countryDecoder : Decoder (Dict String Country)
countryDecoder =
    Json.map (\list -> Dict.fromList list)
        (Json.list <|
            Json.map2 (\code name -> ( code, Country { code = code, name = name } ))
                (Json.field "code" Json.string)
                (Json.field "name" Json.string)
        )


airportDecoder : Decoder (Dict Int Airport)
airportDecoder =
    Json.map (\list -> Dict.fromList list)
        (Json.list <|
            Json.map3 (\id ident name -> ( id, { id = id, ident = ident, name = name } ))
                (Json.field "id" Json.int)
                (Json.field "ident" Json.string)
                (Json.field "name" Json.string)
        )


airportDecoderSimple : Decoder Airport
airportDecoderSimple =
    Json.map3 (\id ident name -> { id = id, ident = ident, name = name })
        (Json.field "id" Json.int)
        (Json.field "ident" Json.string)
        (Json.field "name" Json.string)


flightDecoder : Decoder Flight
flightDecoder =
    Json.map8 Flight
        (Json.field "flight_id" Json.string)
        (Json.field "model" Json.string)
        (Json.field "price_business" Json.float)
        (Json.field "price_economy" Json.float)
        (Json.field "departure_time" Json.string)
        (Json.field "arrival_time" Json.string)
        (Json.field "departure_airport_id" Json.int)
        (Json.field "arrival_airport_id" Json.int)


pathItemDecoder : Decoder PathItem
pathItemDecoder =
    Json.map2 PathItem
        (Json.field "airport" airportDecoderSimple)
        (Json.field "next_flight" flightDecoder)


pathDataDecoder : Decoder PathData
pathDataDecoder =
    Json.map2 PathData
        (Json.field "final_airport" airportDecoderSimple)
        (Json.field "path" (Json.list pathItemDecoder))


init : () -> ( Model, Cmd Msg )
init _ =
    let
        defaultDate : Date
        defaultDate =
            Date.fromCalendarDate 2024 Jan 1

        emptyAirportInfo : FinalNodesInfo
        emptyAirportInfo =
            { selectedContinent = Nothing, selectedCountry = Nothing, countryOptions = Nothing, airportOptions = Nothing, selectedAirport = Nothing }
    in
    ( { originAirport = emptyAirportInfo, destinationAirport = emptyAirportInfo, date = ( Date.toIsoString defaultDate, Just defaultDate ), path = Nothing }
    , Cmd.none
    )



-- UPDATE


type WhichAirportChange
    = OriginChange
    | DestinationChange


type Msg
    = UpdateContinent WhichAirportChange String
    | GotCountries WhichAirportChange (Result Http.Error (Dict String Country))
    | UpdateCountry WhichAirportChange String -- country iso_code
    | GotAirports WhichAirportChange (Result Http.Error (Dict Int Airport))
    | UpdateAirport WhichAirportChange Int -- airport id id
    | UpdateDate String
    | SendRequest { origAirport : Airport, destAirport : Airport, date : Date.Date }
    | GotPath (Result Http.Error PathData)


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    let
        resToMaybeWithLog : Result a b -> Maybe b
        resToMaybeWithLog res =
            Result.toMaybe <| res

        gotFinalModel : (Maybe good -> FinalNodesInfo -> FinalNodesInfo) -> WhichAirportChange -> Result e good -> Model
        gotFinalModel setter originOrDestinationChange dictRes =
            case originOrDestinationChange of
                OriginChange ->
                    setOriginNode (setter (resToMaybeWithLog dictRes) model.originAirport) model

                DestinationChange ->
                    setDestinationNode (setter (resToMaybeWithLog dictRes) model.destinationAirport) model

        updateFinalModel : WhichAirportChange -> comparable -> (Maybe v -> FinalNodesInfo -> FinalNodesInfo) -> (FinalNodesInfo -> Maybe (Dict comparable v)) -> Model
        updateFinalModel originOrDestinationChange selectedValue setter dictGetter =
            let
                updateNodeInfo : FinalNodesInfo -> FinalNodesInfo
                updateNodeInfo node =
                    let
                        valueToSet : Maybe v
                        valueToSet =
                            Maybe.andThen (\dict -> Dict.get selectedValue dict) (dictGetter node)
                    in
                    setter valueToSet node
            in
            case originOrDestinationChange of
                OriginChange ->
                    setOriginNode (updateNodeInfo model.originAirport) model

                DestinationChange ->
                    setDestinationNode (updateNodeInfo model.destinationAirport) model
    in
    case msg of
        GotCountries originOrDestinationChange countryDictRes ->
            ( gotFinalModel setNodeCountryOptions originOrDestinationChange countryDictRes, Cmd.none )

        GotAirports originOrDestinationChange airportDictRes ->
            ( gotFinalModel setNodeAirportOptions originOrDestinationChange airportDictRes, Cmd.none )

        GotPath pathRes ->
            ( { model | path = resToMaybeWithLog pathRes }, Cmd.none )

        UpdateContinent originOrDestinationChange selectedContinentCode ->
            ( updateFinalModel originOrDestinationChange selectedContinentCode setNodeContinent (\_ -> Just continentDictionary)
            , Http.get
                { url = "http://localhost:5000/get_countries?continent=" ++ selectedContinentCode
                , expect = Http.expectJson (GotCountries originOrDestinationChange) countryDecoder
                }
            )

        UpdateCountry originOrDestinationChange selectedCountryIsoCode ->
            ( updateFinalModel originOrDestinationChange selectedCountryIsoCode setNodeCountry getNodeCountryOptions
            , Http.get
                { url = "http://localhost:5000/get_airports?iso_country=" ++ selectedCountryIsoCode
                , expect = Http.expectJson (GotAirports originOrDestinationChange) airportDecoder
                }
            )

        UpdateAirport originOrDestinationChange selectedAirportId ->
            ( updateFinalModel originOrDestinationChange selectedAirportId setNodeAirport getNodeAirportOptions
            , Cmd.none
            )

        UpdateDate dateStr ->
            let
                validateLength : String -> Maybe String
                validateLength str =
                    if String.length str > 10 then
                        Just dateStr

                    else
                        Nothing

                validateChars : String -> String
                validateChars str =
                    String.filter (\ch -> Char.isDigit ch || ch == '-') str

                newDateTuple : ( String, Maybe Date )
                newDateTuple =
                    let
                        newDateStr =
                            Maybe.withDefault dateStr <| Maybe.map validateChars (validateLength dateStr)
                    in
                    ( newDateStr, Result.toMaybe <| Date.fromIsoString newDateStr )
            in
            ( { model | date = newDateTuple }
            , Cmd.none
            )

        SendRequest data ->
            ( model
            , Http.get
                { url =
                    let
                        destination_id =
                            "destination_id=" ++ String.fromInt data.destAirport.id

                        origin_id =
                            "origin_id=" ++ String.fromInt data.origAirport.id

                        date =
                            "date=" ++ Date.toIsoString data.date
                    in
                    "http://localhost:5000/get_path?" ++ origin_id ++ "&" ++ destination_id ++ "&" ++ date
                , expect = Http.expectJson GotPath pathDataDecoder
                }
            )



-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions _ =
    Sub.none



-- VIEW


view : Model -> Html Msg
view model =
    let
        toInt : String -> Int
        toInt s =
            -- it should be impossible for this to fail
            Maybe.withDefault 0 (String.toInt s)

        continentSelector : (String -> Msg) -> Html Msg
        continentSelector msgConstructor =
            select [ onInput msgConstructor ]
                (option [ value "" ] [ text "Select a continent" ]
                    :: List.map (\(Continent cont) -> option [ value cont.code ] [ text cont.name ]) (Dict.values continentDictionary)
                )

        countrySelector : Dict String Country -> (String -> Msg) -> Html Msg
        countrySelector countries msgConstructor =
            select [ onInput msgConstructor ]
                (option [ value "" ] [ text "Select a country" ]
                    :: List.map (\( isoCode, cont ) -> option [ value isoCode ] [ text (countryToString cont) ]) (Dict.toList countries)
                )

        airportSelector : Dict Int Airport -> (Int -> Msg) -> Html Msg
        airportSelector airports msgConstructor =
            select [ onInput (\s -> msgConstructor (toInt s)) ]
                (option [ value "" ] [ text "Select an airport" ]
                    :: List.map (\( id, cont ) -> option [ value (String.fromInt id) ] [ text (airportToString cont) ]) (Dict.toList airports)
                )

        nodeOptionsHtml : String -> (String -> Msg) -> (String -> Msg) -> (Int -> Msg) -> FinalNodesInfo -> Html Msg
        nodeOptionsHtml nameStr continentUpdateMsg countryUpdateMsg airportUpdateMsg airportInfo =
            let
                countriesHtml : List (Html Msg)
                countriesHtml =
                    case airportInfo.countryOptions of
                        Just countries ->
                            [ div [] [ text "Country: ", countrySelector countries countryUpdateMsg ] ]

                        Nothing ->
                            []

                airportsHtml : List (Html Msg)
                airportsHtml =
                    case airportInfo.airportOptions of
                        Just airports ->
                            [ div [] [ text "Airport: ", airportSelector airports airportUpdateMsg ] ]

                        Nothing ->
                            []

                divChildren : List (Html Msg)
                divChildren =
                    [ h1 [] [ text (nameStr ++ " Airport") ]
                    , div [] [ text (nameStr ++ " Continent: "), continentSelector continentUpdateMsg ]
                    ]
                        ++ countriesHtml
                        ++ airportsHtml
            in
            div [] divChildren

        dateHtml : Html Msg
        dateHtml =
            input
                [ type_ "text"
                , placeholder "YYYY-MM-DD"
                , onInput UpdateDate
                , value <| first model.date
                ]
                []

        buttonHtml : List (Html Msg)
        buttonHtml =
            case ( model.originAirport.selectedAirport, model.destinationAirport.selectedAirport, model.date ) of
                ( Just origAirport, Just destAirport, ( _, Just date ) ) ->
                    [ button [ onClick (SendRequest { origAirport = origAirport, destAirport = destAirport, date = date }) ] [ text "Ask for a path" ]
                    ]

                _ ->
                    []

        pathHtml : List (Html msg)
        pathHtml =
            case model.path of
                Just a ->
                    [ viewPathData a ]

                Nothing ->
                    []

        aiportsHtml : Html Msg
        aiportsHtml =
            div [] <|
                [ nodeOptionsHtml "Origin" (UpdateContinent OriginChange) (UpdateCountry OriginChange) (UpdateAirport OriginChange) model.originAirport
                , nodeOptionsHtml "Destination" (UpdateContinent DestinationChange) (UpdateCountry DestinationChange) (UpdateAirport DestinationChange) model.destinationAirport
                , dateHtml
                , Html.node "link"
                    [ href "https://cdn.jsdelivr.net/npm/bootstrap@4.3.1/dist/css/bootstrap.min.css"
                    , rel "stylesheet"
                    , type_ "text/css"
                    ]
                    []
                ]
                    ++ buttonHtml
                    ++ pathHtml
    in
    aiportsHtml


viewAirport : Airport -> Html msg
viewAirport airport =
    div []
        [ h2 [] [ text <| airport.name ++ " (" ++ airport.ident ++ ")" ]
        ]


viewFlight : Flight -> Html msg
viewFlight flight =
    div []
        [ p [] [ text ("Flight ID: " ++ flight.flightId) ]
        , p [] [ text ("Model: " ++ flight.model) ]
        , p [] [ text ("Price (Business): $" ++ String.fromFloat flight.priceBusiness) ]
        , p [] [ text ("Price (Economy): $" ++ String.fromFloat flight.priceEconomy) ]
        , p [] [ text ("Departure Time: " ++ flight.departureTime) ]
        , p [] [ text ("Arrival Time: " ++ flight.arrivalTime) ]
        ]


viewPathItem : PathItem -> Html msg
viewPathItem pathItem =
    div []
        [ viewAirport pathItem.airport
        , viewFlight pathItem.nextFlight
        ]


viewPathData : PathData -> Html msg
viewPathData pathData =
    div []
        [ h2 [] [ text "Path" ]
        , ul []
            (List.map (\item -> li [] [ viewPathItem item ]) pathData.path)
        , h3 [] [ text "Final Airport" ]
        , viewAirport pathData.finalAirport
        ]
