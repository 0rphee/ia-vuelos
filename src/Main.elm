module Main exposing (Model, Msg(..), init, main, subscriptions, update, view)

import Browser
import Debug exposing (todo)
import Dict exposing (Dict)
import Html exposing (Html, div, h1, option, select, text)
import Html.Attributes exposing (value)
import Html.Events exposing (onInput)
import Http
import Json.Decode as Json exposing (Decoder)



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
    , date : Maybe String
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


type Airport
    = Airport
        { id : Int
        , ident : String
        , name : String
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


countryToString : Country -> String
countryToString (Country c) =
    c.name


airportToString : Airport -> String
airportToString (Airport c) =
    c.name


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
            Json.map3 (\id ident name -> ( id, Airport { id = id, ident = ident, name = name } ))
                (Json.field "id" Json.int)
                (Json.field "ident" Json.string)
                (Json.field "name" Json.string)
        )


init : () -> ( Model, Cmd Msg )
init _ =
    let
        emptyAirportInfo : FinalNodesInfo
        emptyAirportInfo =
            { selectedContinent = Nothing, selectedCountry = Nothing, countryOptions = Nothing, airportOptions = Nothing, selectedAirport = Nothing }
    in
    ( { originAirport = emptyAirportInfo, destinationAirport = emptyAirportInfo, date = Nothing }
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


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    let
        toMaybeWithLog : Result a b -> Maybe b
        toMaybeWithLog res =
            Result.toMaybe <| Result.mapError (Debug.log "Request error") res
    in
    case msg of
        GotCountries originOrDestinationChange countryDictRes ->
            let
                updateNodeInfo : FinalNodesInfo -> FinalNodesInfo
                updateNodeInfo node =
                    let
                        countryOptions : Maybe (Dict String Country)
                        countryOptions =
                            toMaybeWithLog countryDictRes
                    in
                    setNodeCountryOptions countryOptions node

                finalModel : Model
                finalModel =
                    case originOrDestinationChange of
                        OriginChange ->
                            setOriginNode (updateNodeInfo model.originAirport) model

                        DestinationChange ->
                            setDestinationNode (updateNodeInfo model.destinationAirport) model
            in
            ( finalModel, Cmd.none )

        GotAirports originOrDestinationChange airportDictRes ->
            let
                updateNodeInfo : FinalNodesInfo -> FinalNodesInfo
                updateNodeInfo node =
                    let
                        airportOptions : Maybe (Dict Int Airport)
                        airportOptions =
                            toMaybeWithLog airportDictRes
                    in
                    setNodeAirportOptions airportOptions node

                finalModel : Model
                finalModel =
                    case originOrDestinationChange of
                        OriginChange ->
                            setOriginNode (updateNodeInfo model.originAirport) model

                        DestinationChange ->
                            setDestinationNode (updateNodeInfo model.destinationAirport) model
            in
            ( finalModel, Cmd.none )

        UpdateContinent originOrDestinationChange selectedContinentCode ->
            let
                updateNodeInfo : FinalNodesInfo -> FinalNodesInfo
                updateNodeInfo airport =
                    setNodeContinent (Dict.get selectedContinentCode continentDictionary) airport

                -- (Just (Continent selectedContinentCode)) airport
                finalModel : Model
                finalModel =
                    case originOrDestinationChange of
                        OriginChange ->
                            setOriginNode (updateNodeInfo model.originAirport) model

                        DestinationChange ->
                            setDestinationNode (updateNodeInfo model.destinationAirport) model
            in
            ( finalModel
            , Http.get
                { url = "http://localhost:5000/get_countries?continent=" ++ selectedContinentCode
                , expect = Http.expectJson (GotCountries originOrDestinationChange) countryDecoder
                }
            )

        UpdateCountry originOrDestinationChange selectedCountryIsoCode ->
            let
                updateNodeInfo : FinalNodesInfo -> FinalNodesInfo
                updateNodeInfo airport =
                    case airport.countryOptions of
                        Just countriesAvailable ->
                            let
                                country : Maybe Country
                                country =
                                    Dict.get selectedCountryIsoCode countriesAvailable
                            in
                            setNodeCountry country airport

                        Nothing ->
                            Debug.log "impossible"
                                airport

                finalModel : Model
                finalModel =
                    case originOrDestinationChange of
                        OriginChange ->
                            setOriginNode (updateNodeInfo model.originAirport) model

                        DestinationChange ->
                            setDestinationNode (updateNodeInfo model.destinationAirport) model
            in
            ( finalModel
            , Http.get
                { url = "http://localhost:5000/get_airports?iso_country=" ++ selectedCountryIsoCode
                , expect = Http.expectJson (GotAirports originOrDestinationChange) airportDecoder
                }
            )

        UpdateAirport originOrDestinationChange selectedAirportId ->
            let
                updateNodeInfo : FinalNodesInfo -> FinalNodesInfo
                updateNodeInfo node =
                    case node.airportOptions of
                        Just countriesAvailable ->
                            let
                                airport : Maybe Airport
                                airport =
                                    Dict.get selectedAirportId countriesAvailable
                            in
                            setNodeAirport airport node

                        Nothing ->
                            Debug.log "impossible"
                                node

                finalModel : Model
                finalModel =
                    case originOrDestinationChange of
                        OriginChange ->
                            setOriginNode (updateNodeInfo model.originAirport) model

                        DestinationChange ->
                            setDestinationNode (updateNodeInfo model.destinationAirport) model
            in
            ( finalModel, Cmd.none )



-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions _ =
    Sub.none



-- VIEW


view : Model -> Html Msg
view model =
    let
        _ =
            Debug.log "model " model

        toInt : String -> Int
        toInt s =
            case String.toInt s of
                Just v ->
                    v

                Nothing ->
                    todo "toInt failure"

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

        aiportsHtml : Html Msg
        aiportsHtml =
            div []
                [ nodeOptionsHtml "Origin" (UpdateContinent OriginChange) (UpdateCountry OriginChange) (UpdateAirport OriginChange) model.originAirport
                , nodeOptionsHtml "Destination" (UpdateContinent DestinationChange) (UpdateCountry DestinationChange) (UpdateAirport DestinationChange) model.destinationAirport
                ]
    in
    aiportsHtml
