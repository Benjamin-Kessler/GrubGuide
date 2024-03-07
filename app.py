'''
Code for the restaurant selection app 'GrubGuide'. Contains all the required code to run the dash application.
'''

# Import libraries
from typing import List, Union
import datetime
from dash import dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np

# Define dash application
app: dash.Dash = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
app.title = 'GrubGuide'

# Read data from local file and create new column for 'average' price
df: pd.DataFrame = pd.read_excel('restaurants.xlsx', sheet_name='Food').fillna('')
df['Preis'] = df['Preis min'] + df['Preis max'] / 2
df['Price range'] = [set(np.arange(i, j + 1, 0.5)) for i, j in df[['Preis min', 'Preis max']].values]

# Create list of all tags to enable corresponding filters below
all_tags: List[str] = list(set(', '.join(df['Tags'].unique()).split(', ')))
all_tags.remove('')
all_tags.sort()


def update_cards(  # pylint: disable=too-many-arguments
    tolerance_filter: str, tag_filter: str, takeaway_filter: str, price_filter: str, time_filter: str, sort_by: str
) -> List[Union[dbc.Card, html.A]]:
    '''
    Function that creates and returns the bootstrap components corresponding to the restaurants that
    satisfy the given filter values.
    '''
    filtered_df: pd.DataFrame = df
    try:
        # Filter by tolerance
        if tolerance_filter == 'Vegetarisch':
            filtered_df: pd.DataFrame = filtered_df[(filtered_df['Optionen'] != '')].reset_index(drop=True)
        elif tolerance_filter == 'Vegan':
            filtered_df: pd.DataFrame = filtered_df[(filtered_df['Optionen'] == 'Vegan')].reset_index(drop=True)

        # Filter by tags
        if tag_filter is not None:
            tags_filter_combined: str = '|'.join(tag_filter)
            filtered_df: pd.DataFrame = filtered_df[
                (filtered_df['Tags'].str.contains(tags_filter_combined))
            ].reset_index(drop=True)

        # Filter by takeaway
        if takeaway_filter == 'Take-Away':
            filtered_df: pd.DataFrame = filtered_df[filtered_df['Take-Away'] == 1].reset_index(drop=True)
        if takeaway_filter == 'Dine-In':
            filtered_df: pd.DataFrame = filtered_df[filtered_df['Dine-In'] == 1].reset_index(drop=True)

        # Filter by price
        price_range: set = set(np.arange(price_filter[0], price_filter[1] + 0.5, 0.5))
        price_filter = [bool(item & price_range) for item in filtered_df['Price range']]
        filtered_df: pd.DataFrame = filtered_df[price_filter].reset_index(drop=True)
        # filtered_df: pd.DataFrame = filtered_df[filtered_df['Preis min'] >= price_filter[0]].reset_index(drop=True)
        # filtered_df: pd.DataFrame = filtered_df[filtered_df['Preis max'] <= price_filter[1]].reset_index(drop=True)

        # Filter by time
        filtered_df: pd.DataFrame = filtered_df[filtered_df['Gesamtzeitaufwand (Zu Fuss)'] <= time_filter].reset_index(
            drop=True
        )

    except KeyError:
        pass

    # Compute weekday for displaying opening hours
    weekday_column: str = f"Open_{datetime.date.today().weekday() + 1}"

    # Sort dataframe
    if sort_by == 'Name (aufsteigend)':
        filtered_df: pd.DataFrame = filtered_df.sort_values(by='Name').reset_index(drop=True)
    elif sort_by == 'Name (absteigend)':
        filtered_df: pd.DataFrame = filtered_df.sort_values(by='Name', ascending=False).reset_index(drop=True)
    elif sort_by == 'Preis (aufsteigend)':
        filtered_df: pd.DataFrame = filtered_df.sort_values(by=['Preis', 'Preis min', 'Name']).reset_index(drop=True)
    elif sort_by == 'Preis (absteigend)':
        filtered_df: pd.DataFrame = filtered_df.sort_values(
            by=['Preis', 'Preis min', 'Name'], ascending=False
        ).reset_index(drop=True)
    elif sort_by == 'Wegzeit':
        filtered_df: pd.DataFrame = filtered_df.sort_values(by=['Wegzeit', 'Name']).reset_index(drop=True)
    elif sort_by == 'Gesamtzeitaufwand':
        filtered_df: pd.DataFrame = filtered_df.sort_values(by=['Gesamtzeitaufwand (Zu Fuss)', 'Name']).reset_index(
            drop=True
        )

    # Create a bootstrap component card for each restaurant satisfying the filters
    filtered_cards: List[Union[dbc.Card, html.A]] = []
    for i in range(len(filtered_df)):
        # Create hoverable text element
        hoverable_text = html.Div(
            f"Öffnungszeiten: {filtered_df[weekday_column][i]}",
            className="hoverable-text",
        )

        # Append hoverable text to card
        card_body = dbc.CardBody(
            [
                html.H4(filtered_df['Name'][i], className="card-title"),
                html.Div(f"{filtered_df['Adresse'][i]}", className="card-text"),
                html.Div(
                    [
                        html.Div(
                            f"{filtered_df['Tags'][i]}",
                            className="card-text",
                            style={"display": "inline-block", "width": "60%"},
                        ),
                        html.Div(
                            html.Div(
                                [html.I(className="fa-solid fa-leaf"), html.Span(f": {filtered_df['Optionen'][i]}")]
                            ),
                            className="card-text text-right",
                            style={"display": "inline-block", "width": "40%", "text-align": "right"},
                        ),
                    ],
                    className="card-text",
                ),
            ]
        )

        # Create footer displaying information
        card_footer = dbc.CardFooter(
            [
                html.Div(
                    [
                        html.I(className="fa-solid fa-person-walking"),
                        html.Span(
                            f": {filtered_df['Wegzeit'][i]} Min",
                            className="card-text",
                            style={'margin-right': '1.25em'},
                        ),
                        html.I(className="fa-solid fa-bicycle"),
                        html.Span(
                            f": {int((filtered_df['Wegzeit'][i] - 1) / 3 + 1)} Min",
                            className="card-text",
                            style={'margin-right': '1.25em'},
                        ),
                        html.I(className="fa-solid fa-utensils"),
                        html.Span(f": {filtered_df['Essenszeit'][i]} Min", className="card-text"),
                    ]
                ),
                html.Div(f'$: {filtered_df["Preis min"][i]:.2f} - {filtered_df["Preis max"][i]:.2f} CHF'),
            ]
        )

        card_with_hoverable_text = dbc.Card(
            [dbc.CardImg(src=filtered_df['Image'][i], top=True), card_body, card_footer, hoverable_text],
            style={"width": "100%", "margin": "10px"},
            className="hoverable-card",
        )

        # Transform the cards to be clickable links if one is provided
        card_with_link = card_with_hoverable_text
        if filtered_df['Website'][i] != '':
            card_with_link = html.A(
                href=filtered_df['Website'][i],
                children=[card_with_hoverable_text],
                target="_blank",
                style={'color': 'black', "text-decoration": "none"},
            )

        # Append card to list which will be returned
        filtered_cards.append(card_with_link)

    return filtered_cards


# Define the app layout
app.layout = html.Div(
    [
        # Title
        html.H1("GrubGuide", style={"font-weight": "bold", "font-size": "60px"}),
        # Horizontal line followed by various filters (arranged in one row)
        html.Hr(),
        html.Div(
            [
                dbc.Row(
                    [
                        # Dropdown to filter by tags
                        dbc.Col(
                            [
                                html.Label('Tags'),
                                dcc.Dropdown(id='tag_filter', options=all_tags, placeholder='Wähle Tags', multi=True),
                            ],
                            width=2,
                        ),
                        # Dropdown to filter by vegan/vegetarian options
                        dbc.Col(
                            [
                                html.Label('Veträglichkeiten'),
                                dcc.Dropdown(
                                    id="tolerance_filter",
                                    options=['Alle', 'Vegan', 'Vegetarisch'],
                                    value='Alle',
                                    clearable=False,
                                ),
                            ],
                            width=2,
                        ),
                        # Dropdown to filter by take-away / dine-in availability
                        dbc.Col(
                            [
                                html.Label('Take-Away / Dine-In'),
                                dcc.Dropdown(
                                    id="takeaway_filter",
                                    options=['Beides', 'Take-Away', 'Dine-In'],
                                    value='Beides',
                                    clearable=False,
                                ),
                            ],
                            width=2,
                        ),
                        # Rangeslider to filter by price
                        dbc.Col(
                            [html.Label('Preisspanne'), dcc.RangeSlider(5, 50, 5, value=[5, 50], id="price_filter")],
                            width=2,
                        ),
                        # Slider to filter by desired max time used
                        dbc.Col(
                            [html.Label('Gesamtzeitaufwand'), dcc.Slider(15, 90, 15, value=90, id="time_filter")],
                            width=2,
                        ),
                        # Dropdown to sort displayed cards
                        dbc.Col(
                            [
                                html.Label('Sortieren nach:'),
                                dcc.Dropdown(
                                    id="sort_by",
                                    options=[
                                        'Name (aufsteigend)',
                                        'Name (absteigend)',
                                        'Preis (aufsteigend)',
                                        'Preis (absteigend)',
                                        'Wegzeit',
                                        'Gesamtzeitaufwand',
                                    ],
                                    value='Name (aufsteigend)',
                                    clearable=False,
                                ),
                            ],
                            width=2,
                        ),
                    ]
                ),
                # html.Link(href='/assets/custom.css', rel='stylesheet'),
            ],
            style={'marginBottom': 30, 'marginTop': 30},
        ),
        # Horizontal line followed by the filtered cards.
        html.Hr(),
        html.Div(id='filtered-cards', children=[]),
    ],
    style={"margin": "20px"},
)


@app.callback(
    Output('filtered-cards', 'children'),
    Input('tolerance_filter', 'value'),
    Input('tag_filter', 'value'),
    Input('takeaway_filter', 'value'),
    Input('price_filter', 'value'),
    Input('time_filter', 'value'),
    Input('sort_by', 'value'),
)
def display_filtered_cards(
    tolerance_filter, tag_filter, takeaway_filter, price_filter, time_filter, sort_by
):  # pylint: disable=too-many-arguments
    '''
    Funktion that takes the current values of the given filters and returns rows with cards corresponding to
    the restaurants that satisfy the filter.
    '''
    filtered_cards = update_cards(tolerance_filter, tag_filter, takeaway_filter, price_filter, time_filter, sort_by)
    cards = [dbc.Col(card, width=3) for card in filtered_cards]
    return dbc.Row(cards, justify="left")


if __name__ == '__main__':
    app.run_server(debug=True)
