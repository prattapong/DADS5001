import pandas as pd
import re
import json
import requests
import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import plotly.express as px

################################################################################################################
################################################## PARAMETERS ##################################################
################################################################################################################

API_URL = 'https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1'
headers = {'Authorization': f'Bearer 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'}
file = 'C:/Users/Rattapong.Pojpatin/Downloads/association_file.xlsx'

################################################################################################################
################################################### FUNCTIONS ##################################################
################################################################################################################

##### I/O Functions

# def query(payload):
#     response = requests.post(API_URL,
#                              headers = headers,
#                              json = payload)
#     return dict(response.json()[0])['generated_text']

def query(payload, max_chars_per_request=1000):
    text = payload['inputs']
    num_chunks = (len(text) + max_chars_per_request - 1) // max_chars_per_request
    
    responses = []
    for i in range(num_chunks):
        start = i * max_chars_per_request
        end = min((i + 1) * max_chars_per_request, len(text))
        chunk_payload = {'inputs': text[start:end]}
        
        response = requests.post(API_URL,
                                 headers=headers,
                                 json=chunk_payload)
        
        response_text = response.json()[0]['generated_text']
        responses.append(response_text)
    
    return ''.join(responses)

def format_instruction(instruction: str):
    instruction_prompt = """
    My data contains columns: product_name_lhs, product_name_rhs, Support, Confidence, Lift. 
    Extract Entities strictly as instructed below: 
    1. chart_type: The type of chart that is recommend for the question (Choose on of these options: Bar Chart, Line Chart, Pie Chart)
    2. x: The column for x-axis (for Pie Chart, this is the name of dimension column). Note that it has to match with column names given above.
    3. y: The column for y-axis (for Pie Chart, this is the name of metrics column) Note that it has to match with column names given above.
    4. filter: The slicing of data (column: The column name to filter, value: The value of the column to filter)

    STRICTLY Expected Output JSON:
    {"chart_type": "Bar Chart", "x": "product_name_rhs", "y": "Confidence", "filter": {"column": "product_name_lhs", "value": ["milk"]}}

    Question: Now, extract the entities for the instruction below:
    
    """
    instruction_text = "[INST] " + instruction_prompt + instruction + " [/INST]"
    return instruction_text

def format_output(output, instruction):
    output = output.replace(instruction, '').strip()
    return output

def generate_output(instruction: str):
    instruction = format_instruction(instruction = instruction)
    data = query({"inputs": instruction,
                  "parameters" : {"max_length": 10000}})
    output = format_output(output = data, instruction = instruction)
    return output

def get_chart_json(input_text: str):
    pattern = re.compile(r'``json(.+?)``', re.DOTALL)
    match = pattern.search(input_text)

    json_string = match.group(1).strip()
    json_data = json.loads(json_string)
    return json_data

##### Chart Functions

def pie_chart(df, chart_json):
    fig = px.pie(df, 
                 names=chart_json['x'], 
                 values=chart_json['y'],
                 color_discrete_sequence=px.colors.sequential.Plasma_r,
                 hole=0.4)
    return fig

def bar_chart(df, chart_json):
    fig = px.bar(df, 
                 x=chart_json['x'], 
                 y=chart_json['y'],
                 color_discrete_sequence=px.colors.sequential.Plasma)
    return fig

def table_chart(df):
    fig = go.Figure(
        data = [
            go.Table(
                header = dict(values = list(df.columns),
                              fill_color = 'paleturquoise',
                              align = 'left'),
                cells = dict(values = [df[col] for col in df.columns],
                             fill_color = 'lavender',
                             align = 'left')
            )
        ]
    )
    return fig

def generate_chart(df, chart_json):
    filtered_data = df[df[chart_json['filter']['column']].isin(chart_json['filter']['value'])]

    if chart_json['chart_type'] == 'Pie Chart':
        fig = pie_chart(df = filtered_data, chart_json = chart_json)

    elif chart_json['chart_type'] == 'Bar Chart':
        fig = bar_chart(df = filtered_data, chart_json = chart_json)

    else:
        fig = table_chart(df = filtered_data)

    return fig

################################################################################################################
##################################################### PLOT #####################################################
################################################################################################################

# Create Dash app
app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY])
fig = go.Figure()

# Define custom CSS style for the font
custom_css = {
    'fontFamily': 'Open Sans, sans-serif'
}

sidebar = html.Div(
    [
        # Header
        dbc.Row(
            [
                html.H5(
                    'BALL is AI', 
                    style = {'margin-top': 'auto',
                             'margin-bottom': 'auto',
                             'margin-left': 'auto',
                             'margin-right': 'auto', 
                             'width': '100%',
                             **custom_css}
                )
            ],
            style = {"height": "10vh"}
        ),

        # Filter 1
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            html.P(
                                'Filter 1', 
                                style = {'margin-top': '8px', 
                                         'margin-bottom': '4px',
                                         **custom_css}, 
                                className = 'font-weight-bold',
                            ),
                            dcc.Dropdown(
                                id = 'filter-1',
                                multi = True,
                                options = [{'label': x, 'value': x} for x in ['option1','option2']],
                                style = {'width': '100%'}
                            )
                        ]
                    )
                )
            ]
        ),

        # Filter 2
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            html.P(
                                'Filter 2', 
                                style = {'margin-top': '16px', 'margin-bottom': '4px'}, 
                                className = 'font-weight-bold'
                            ),
                            dcc.Dropdown(
                                id = 'filter-2',
                                multi = True,
                                options = [{'label': x, 'value': x} for x in ['option1','option2']],
                                style = {'width': '100%'}
                            ),
                            html.Button(
                                id = 'my-button', 
                                n_clicks = 0, 
                                children = 'Apply',
                                style = {'width': '100%',
                                         'height': '5vh',
                                         'margin-top': '25px',
                                         'margin-bottom': '6px',
                                         'border': '1px',
                                         'border-radius': '8px'},
                                className = 'bg-primary text-white font-italic'),
                            html.Hr()
                        ]
                    )
                )
            ]
        )

        # Filter 3
    ],
    style={'height': '100vh', 'border-radius': '15px'}
)

content = html.Div(
    [
        # Header
        dbc.Row(
            html.Div(
                style = {'padding': '15px', 'marginBottom': '20px'}, 
                children = [
                    html.H1(
                        'Generative AI Dashboard', 
                        style = {'color': 'black',
                                 'margin-top': '10px',
                                 'margin-left': '20px',
                                 'margin-bottom': 'auto',
                                 'height': '5px',
                                 'font-size': '20px'}
                    )
                ]
            ), 
        ),

        # Chart and Description
        dbc.Row(
            [
                # Chart
                dbc.Col(
                    [
                        html.Div(
                            [
                                dcc.Graph(
                                    id = "dynamic-plot",
                                    figure = fig,
                                    className = 'bg-light',
                                    style = {'width': '100%', 
                                             'height': '100%', 
                                             'padding': '0px'}
                                )
                            ]
                        ),
                    ],
                    style = {'margin-left': '35px',
                             'border': '1px solid lightgrey', 
                             'border-radius': '10px'},
                    xs=12, sm=12, md=6, lg=6, xl=6
                )
            ],
            style = {'height': '70vh'}
        ),

        dbc.Row(
            html.Div(
                style = {'padding': '20px', 'marginTop': '10px'},
                children = [
                    dcc.Input(
                        id = 'text-input',
                        type = 'text',
                        placeholder = 'Enter text here...',
                        style = {'border-radius': '10px lightgrey', 
                                 'margin-left': '15px',
                                 'width': '95%',
                                 **custom_css}
                    )
                ]
            )
        )
    ],
    style={'margin-top': '20px', 
           'margin-bottom': '0px', 
           'margin-left': '5px', 
           'margin-right': '10px',
           'backgroundColor': '#FFFFFF',
           'height': '95vh',
           'border-radius': '25px'}
)

# Define app layout
app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    sidebar,
                    width = 2,
                    style = {'backgroundColor': '#EDF2FA'}
                ),
                dbc.Col(content, width=10)
            ],
            style = {"height": "100vh"}
        ),
    ],
    fluid = True,
    style = {'backgroundColor': '#EDF2FA', 
             'border-radius': '15px', 
             **custom_css}
)

# Callback to generate and update chart
@app.callback(
    Output('dynamic-plot', 'figure'),
    Input('my-button', 'n_clicks'),
    State('text-input', 'value')
)
def update_dynamic_plot(n_clicks, input_text):
    print(input_text)
    if n_clicks > 0:
        # Generate output
        output = generate_output(input_text)
        print(output)
        # Parse JSON data
        chart_json = get_chart_json(input_text = output)
        print(chart_json)
        # Generate chart
        fig = generate_chart(df = df, chart_json = chart_json)
        print('done')
        return fig
    else:
        # Return an empty figure
        return go.Figure()

# Run the app
if __name__ == '__main__':
    df = pd.read_excel(file)
    app.run_server(debug=True)
