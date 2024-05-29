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
        , originContinent : Maybe Continent
        , destinationContinent : Maybe Continent
        , originCountry : Maybe Country
        , destinationCountry : Maybe Country
        , date : Maybe String
        }


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
    ( Model { continents = Nothing, originContinent = Nothing, destinationContinent = Nothing, originCountry = Nothing, destinationCountry = Nothing, date = Nothing }
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
            ( Model { model | originContinent = Just (Continent selected) }, Cmd.none )

        UpdateDestinationContinent selected ->
            ( Model { model | destinationContinent = Just (Continent selected) }, Cmd.none )

        UpdateOriginCountry selected ->
            ( Model { model | originCountry = Just (Country selected) }, Cmd.none )

        UpdateDestinationCountry selected ->
            ( Model { model | destinationCountry = Just (Country selected) }, Cmd.none )



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
                        [ airportOptionsHtml contArray "Origin" UpdateOriginContinent model.originContinent
                        , airportOptionsHtml contArray "Destination" UpdateDestinationContinent model.destinationContinent
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
