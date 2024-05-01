import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

# Create Dash app
app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY])

# Define custom CSS style for the font
custom_css = {
    'fontFamily': 'Open Sans, sans-serif'
}

# Define app layout
app.layout = html.Div(
    style = {'backgroundColor': '#c6d3e3', 
             'borderRadius': '15px', 
             **custom_css}, 
    children = [

        # Header row
        html.Div(
            style = {'backgroundColor': '#304674', 
                    'padding': '15px',
                    'marginBottom': '20px'}, 
            children = [
                html.H1('Dashboard', style = {'color': 'white', 
                                              'margin-top': 'auto',
                                              'margin-bottom': 'auto'}
                )
            ]
        ),

        # Filters row
        dbc.Row(
            html.Div(
                style = {'display': 'flex', 
                        'backgroundColor': '#d8e1e8', 
                        'padding': '15px 20px', 
                        'borderRadius': '7px', 
                        'marginBottom': '20px'}, 
                children = [
                    html.Div(
                        style = {'flex': '1', **custom_css}, 
                        children = [
                            html.Label('Filter 1'),
                            dcc.Dropdown(
                                id = 'filter-1-dropdown',
                                options = [
                                    {'label': 'Option 1', 'value': 'opt1'},
                                    {'label': 'Option 2', 'value': 'opt2'}
                                ],
                                value = 'opt1'
                            )
                        ]
                    ),
                    html.Div(
                        style = {'flex': '1', 'marginLeft': '20px'}, 
                        children = [
                            html.Label('Filter 2'),
                            dcc.Dropdown(
                                id = 'filter-2-dropdown',
                                options = [
                                    {'label': 'Option A', 'value': 'optA'},
                                    {'label': 'Option B', 'value': 'optB'}
                                ],
                                value = 'optA'
                            )
                        ]
                    )
                ]
            ),
            style = {'margin-left': '15px', 'margin-right': '15px'}
        ),

        # Main content row
        html.Div(
            style = {'display': 'flex', 'marginBottom': '30px'}, 
            children = [

                # Left column
                html.Div(
                    style = {'flex': '1',
                            'padding': '15px',
                            'borderRadius': '15px',
                            'backgroundColor': 'white',
                            'marginRight': '20px'}, 
                    children = [
                        html.Div(
                            style = {'height': '300px'},
                            children = [
                                html.H2('Description')
                            ]
                        ),
                        html.Div(
                            style = {'padding': '15px', 'marginTop': '20px'},
                            children = [
                                dcc.Input(
                                    id = 'text-input',
                                    type = 'text',
                                    placeholder = 'Enter text here...',
                                    style = {'borderRadius': '5px', **custom_css}
                                )
                            ]
                        )
                    ]
                ),

                # Right column
                html.Div(
                    style = {'flex': '2',
                            'padding': '15px',
                            'borderRadius': '15px',
                            'backgroundColor': 'white'},
                    children = [
                        dcc.Graph(
                            id='plot',
                            figure = {
                                'data': [
                                    go.Scatter(
                                        x=[1, 2, 3],
                                        y=[4, 1, 2],
                                        mode='lines',
                                        marker=dict(color='red'),
                                        name='Plot'
                                    )
                                ],
                                'layout': go.Layout(
                                    title = 'Plot',
                                    showlegend = True,
                                    margin = {'l': 40, 'b': 40, 't': 40, 'r': 40},
                                    hovermode = 'closest'
                                )
                            }
                        )
                    ]
                )
            ]
        )
    ]
)

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
