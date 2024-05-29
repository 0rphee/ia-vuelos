module Main exposing (Model, Msg(..), init, main, subscriptions, update, view)

import Array exposing (Array)
import Browser
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


type Model
    = Model
        { continents : Maybe (Array Continent)
        , originAirport : AirportInfo
        , destinationAirport : AirportInfo
        , date : Maybe String
        }


type alias AirportInfo =
    { continent : Maybe Continent
    , country : Maybe Country
    , countryOptions : Maybe (Array Country)
    }


setOriginAirport : AirportInfo -> Model -> Model
setOriginAirport airportInfo (Model model) =
    Model
        { model | originAirport = airportInfo }


setDestinationAirport : AirportInfo -> Model -> Model
setDestinationAirport airportInfo (Model model) =
    Model
        { model | originAirport = airportInfo }


setAirportContinent : Continent -> AirportInfo -> AirportInfo
setAirportContinent continent model =
    { model | continent = Just continent }


setAirportCountry : Country -> AirportInfo -> AirportInfo
setAirportCountry country model =
    { model | country = Just country }


type Continent
    = Continent String


type Country
    = Country String


continentToString : Continent -> String
continentToString (Continent s) =
    s


arrayToString : Array a -> (a -> String) -> String
arrayToString arr toString =
    arr
        |> Array.toList
        |> List.map toString
        |> String.join ", "


init : () -> ( Model, Cmd Msg )
init _ =
    let
        emptyAirportInfo =
            { continent = Nothing, country = Nothing, countryOptions = Nothing }
    in
    ( Model { continents = Nothing, originAirport = emptyAirportInfo, destinationAirport = emptyAirportInfo, date = Nothing }
    , Http.get
        { url = "http://localhost:5000/get_continents"
        , expect = Http.expectJson GotContinents continentDecoder
        }
    )



-- UPDATE


type Msg
    = GotContinents (Result Http.Error (Array Continent))
    | UpdateOriginContinent String
    | UpdateDestinationContinent String
    | UpdateOriginCountry String
    | UpdateDestinationCountry String


continentDecoder : Decoder (Array Continent)
continentDecoder =
    array (Json.map Continent string)


update : Msg -> Model -> ( Model, Cmd Msg )
update msg (Model model) =
    case msg of
        GotContinents res ->
            case res of
                Ok contArray ->
                    ( Model { model | continents = Just contArray }, Cmd.none )

                Err _ ->
                    ( Model model, Cmd.none )

        UpdateOriginContinent selected ->
            let
                newAirportInfo =
                    setAirportContinent (Continent selected) model.originAirport

                finalModel =
                    Model model
                        |> setOriginAirport newAirportInfo
            in
            ( finalModel, Cmd.none )

        UpdateDestinationContinent selected ->
            let
                newAirportInfo =
                    setAirportContinent (Continent selected) model.destinationAirport

                finalModel =
                    Model model
                        |> setDestinationAirport newAirportInfo
            in
            ( finalModel, Cmd.none )

        UpdateOriginCountry selected ->
            let
                newAirportInfo =
                    setAirportCountry (Country selected) model.originAirport

                finalModel =
                    Model model
                        |> setOriginAirport newAirportInfo
            in
            ( finalModel, Cmd.none )

        UpdateDestinationCountry selected ->
            let
                newAirportInfo =
                    setAirportCountry (Country selected) model.destinationAirport

                finalModel =
                    Model model
                        |> setDestinationAirport newAirportInfo
            in
            ( finalModel, Cmd.none )



-- ( Model { model | destinationCountry = Just (Country selected) }, Cmd.none )
-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions _ =
    Sub.none



-- VIEW


view : Model -> Html Msg
view (Model model) =
    let
        airportOptionsHtml : Array Continent -> String -> (String -> Msg) -> Maybe Continent -> Html Msg
        airportOptionsHtml contArray nameStr appMsg currentCont =
            div []
                [ h1 [] [ text (nameStr ++ " Airport") ]
                , div [] [ text (nameStr ++ " Continent: "), continentSelector contArray appMsg ]
                , pre [] [ text "Selected Continent: ", text (maybeContinentToString currentCont) ]
                ]

        aiportsHtml : Html Msg
        aiportsHtml =
            case model.continents of
                Just contArray ->
                    div []
                        [ airportOptionsHtml contArray "Origin" UpdateOriginContinent model.originAirport.continent
                        , airportOptionsHtml contArray "Destination" UpdateDestinationContinent model.destinationAirport.continent
                        ]

                Nothing ->
                    pre [] [ text "Loading continents..." ]
    in
    aiportsHtml


continentSelector : Array Continent -> (String -> Msg) -> Html Msg
continentSelector continents msgConstructor =
    select [ onInput msgConstructor ]
        (option [ value "" ] [ text "Select a continent" ]
            :: List.map (\cont -> option [ value (continentToString cont) ] [ text (continentToString cont) ]) (Array.toList continents)
        )


maybeContinentToString : Maybe Continent -> String
maybeContinentToString maybeCont =
    case maybeCont of
        Just cont ->
            continentToString cont

        Nothing ->
            "None"
