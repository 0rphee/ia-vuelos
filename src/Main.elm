module Main exposing (Model, Msg(..), init, main, subscriptions, update, view)

import Array exposing (Array)
import Browser
import Debug exposing (todo)
import Dict exposing (Dict)
import Html exposing (Html, div, h1, option, pre, select, text)
import Html.Attributes exposing (value)
import Html.Events exposing (onInput)
import Http
import Json.Decode as Json exposing (Decoder, array, string)



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
    { continents : Maybe (Array Continent)
    , originAirport : AirportInfo
    , destinationAirport : AirportInfo
    , date : Maybe String
    }


type alias AirportInfo =
    { continent : Maybe Continent
    , country : Maybe Country
    , countryOptions : Maybe (Dict Int Country) -- Int: id, String: name
    }


setOriginAirport : AirportInfo -> Model -> Model
setOriginAirport airportInfo model =
    { model | originAirport = airportInfo }


setDestinationAirport : AirportInfo -> Model -> Model
setDestinationAirport airportInfo model =
    { model | destinationAirport = airportInfo }


setAirportContinent : Maybe Continent -> AirportInfo -> AirportInfo
setAirportContinent continent airportInfo =
    { airportInfo | continent = continent }


setAirportCountry : Maybe Country -> AirportInfo -> AirportInfo
setAirportCountry country airportInfo =
    { airportInfo | country = country }


setAirportCountryOptions : Maybe (Dict Int Country) -> AirportInfo -> AirportInfo
setAirportCountryOptions countryOptions airportInfo =
    { airportInfo | countryOptions = countryOptions }


type Continent
    = Continent String


continentToString : Continent -> String
continentToString (Continent s) =
    s


type Country
    = Country { id : Int, name : String }


countryToString : Country -> String
countryToString (Country c) =
    c.name


countryDecoder : Decoder (Dict Int Country)
countryDecoder =
    Json.map (\list -> Dict.fromList list)
        (Json.list <|
            Json.map2 (\id name -> ( id, Country { id = id, name = name } ))
                (Json.field "id" Json.int)
                (Json.field "name" Json.string)
        )


init : () -> ( Model, Cmd Msg )
init _ =
    let
        emptyAirportInfo =
            { continent = Nothing, country = Nothing, countryOptions = Nothing }
    in
    ( { continents = Nothing, originAirport = emptyAirportInfo, destinationAirport = emptyAirportInfo, date = Nothing }
    , Http.get
        { url = "http://localhost:5000/get_continents"
        , expect = Http.expectJson GotContinents continentDecoder
        }
    )



-- UPDATE


type WhichAirportChange
    = OriginChange
    | DestinationChange


type Msg
    = GotContinents (Result Http.Error (Array Continent))
    | UpdateContinent WhichAirportChange String
    | GotCountries WhichAirportChange (Result Http.Error (Dict Int Country))
    | UpdateCountry WhichAirportChange Int -- country id


continentDecoder : Decoder (Array Continent)
continentDecoder =
    array (Json.map Continent string)


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        GotContinents res ->
            case res of
                Ok contArray ->
                    ( { model | continents = Just contArray }, Cmd.none )

                Err _ ->
                    ( model, Cmd.none )

        GotCountries originOrDestinationChange countryDictRes ->
            let
                updateAirportInfo : AirportInfo -> AirportInfo
                updateAirportInfo airport =
                    let
                        countryOptions : Maybe (Dict Int Country)
                        countryOptions =
                            case countryDictRes of
                                Ok countries ->
                                    Just countries

                                Err e ->
                                    Nothing
                    in
                    setAirportCountryOptions countryOptions airport

                finalModel : Model
                finalModel =
                    case originOrDestinationChange of
                        OriginChange ->
                            setOriginAirport (updateAirportInfo model.originAirport) model

                        DestinationChange ->
                            setDestinationAirport (updateAirportInfo model.destinationAirport) model
            in
            ( finalModel, Cmd.none )

        UpdateContinent originOrDestinationChange selectedContinent ->
            let
                updateAirportInfo : AirportInfo -> AirportInfo
                updateAirportInfo airport =
                    setAirportContinent (Just (Continent selectedContinent)) airport

                finalModel : Model
                finalModel =
                    case originOrDestinationChange of
                        OriginChange ->
                            setOriginAirport (updateAirportInfo model.originAirport) model

                        DestinationChange ->
                            setDestinationAirport (updateAirportInfo model.destinationAirport) model
            in
            ( finalModel
            , Http.get
                { url = "http://localhost:5000/get_countries?continent=" ++ selectedContinent
                , expect = Http.expectJson (GotCountries originOrDestinationChange) countryDecoder
                }
            )

        UpdateCountry originOrDestinationChange selectedCountryId ->
            let
                updateAirportInfo : AirportInfo -> AirportInfo
                updateAirportInfo airport =
                    -- setAirportContinent (Just (Continent selectedContinent)) airport
                    case airport.countryOptions of
                        Just countriesAvailable ->
                            let
                                country : Maybe Country
                                country =
                                    Dict.get selectedCountryId countriesAvailable
                            in
                            setAirportCountry country airport

                        Nothing ->
                            Debug.log "impossible"
                                airport

                finalModel : Model
                finalModel =
                    case originOrDestinationChange of
                        OriginChange ->
                            setOriginAirport (updateAirportInfo model.originAirport) model

                        DestinationChange ->
                            setDestinationAirport (updateAirportInfo model.destinationAirport) model
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
        debugModel =
            Debug.log "model " model
    in
    let
        continentSelector : Array Continent -> (String -> Msg) -> Html Msg
        continentSelector continents msgConstructor =
            select [ onInput msgConstructor ]
                (option [ value "" ] [ text "Select a continent" ]
                    :: List.map (\cont -> option [ value (continentToString cont) ] [ text (continentToString cont) ]) (Array.toList continents)
                )

        countrySelector : Dict Int Country -> (Int -> Msg) -> Html Msg
        countrySelector countries msgConstructor =
            let
                toInt s =
                    case String.toInt s of
                        Just v ->
                            v

                        Nothing ->
                            todo "toInt failure"
            in
            select [ onInput (\s -> msgConstructor (toInt s)) ]
                (option [ value "" ] [ text "Select a country" ]
                    :: List.map (\( id, cont ) -> option [ value (String.fromInt id) ] [ text (countryToString cont) ]) (Dict.toList countries)
                )

        maybeContinentToString : Maybe Continent -> String
        maybeContinentToString maybeCont =
            case maybeCont of
                Just cont ->
                    continentToString cont

                Nothing ->
                    "None"

        airportOptionsHtml : Array Continent -> String -> (String -> Msg) -> (Int -> Msg) -> AirportInfo -> Html Msg
        airportOptionsHtml contArray nameStr continentUpdateMsg countryUpdateMsg airportInfo =
            let
                countriesHtml : List (Html Msg)
                countriesHtml =
                    case airportInfo.countryOptions of
                        Just c ->
                            [ div [] [ text "Country: ", countrySelector c countryUpdateMsg ] ]

                        Nothing ->
                            []

                divChildren : List (Html Msg)
                divChildren =
                    [ h1 [] [ text (nameStr ++ " Airport") ]
                    , div [] [ text (nameStr ++ " Continent: "), continentSelector contArray continentUpdateMsg ]
                    , pre [] [ text "Selected Continent: ", text (maybeContinentToString airportInfo.continent) ]
                    ]
                        ++ countriesHtml
            in
            div [] divChildren

        aiportsHtml : Html Msg
        aiportsHtml =
            case model.continents of
                Just contArray ->
                    div []
                        [ airportOptionsHtml contArray "Origin" (UpdateContinent OriginChange) (UpdateCountry OriginChange) model.originAirport
                        , airportOptionsHtml contArray "Destination" (UpdateContinent DestinationChange) (UpdateCountry DestinationChange) model.destinationAirport
                        ]

                Nothing ->
                    pre [] [ text "Loading continents..." ]
    in
    aiportsHtml
