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

file = 'https://github.com/prattapong/DADS5001/blob/main/Final%20Project/association_file.csv?raw=True'
API_URL = 'https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1'
headers = {'Authorization': f'Bearer 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'}
df = pd.read_csv(file)

################################################################################################################
################################################### FUNCTIONS ##################################################
################################################################################################################

##### I/O Functions

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

def format_instruction(instruction: str, df:pd.DataFrame):
    instruction_prompt = f"""
    My data contains columns: {', '.join(df.columns)}.
    Please shortly suggest chart type and columns needed for the following question:
    
    """
    instruction_text = "[INST] " + instruction_prompt + instruction + " [/INST]"
    return instruction_text

def format_output(output, instruction):
    output = output.replace(instruction, '').strip()
    return output

def generate_output(instruction: str, df:pd.DataFrame = df):
    instruction = format_instruction(instruction = instruction, df = df)
    data = query({"inputs": instruction,
                  "parameters" : {"max_length": 10000}})
    output = format_output(output = data, instruction = instruction)
    return output

def get_column_needed(df:pd.DataFrame, generated_text:str):
    used_col = [col for col in df.columns if col in generated_text.replace('\\','')]
    return used_col

def get_chart_axis(df:pd.DataFrame, column:list):
    x = []
    y = []
    for col in column:
        if str(df[col].dtype) in ['object', 'str', 'string']:
            x.append(col)
        else:
            y.append(col)
    return x, y

def suggest_chart_type(df:pd.DataFrame, generated_text:str):
    if len(df.columns) == 2:
        return 'bar'
    elif 'scatter' in generated_text.lower():
        return 'scatter'
    elif 'pie' in generated_text.lower():
        return 'pie'
    elif 'line' in generated_text.lower():
        return 'line'
    else:
        return 'bar'

##### Chart Functions

def pie_chart(df:pd.DataFrame,
              x:list,
              y:list):
              
    fig = px.pie(df, 
                 names = x[0],
                 values = y[0],
                 color_discrete_sequence=px.colors.sequential.Plasma_r,
                 hole=0.4)
    return fig

def bar_chart(df:pd.DataFrame,
              x:list,
              y:list):
    fig = px.bar(df, 
                 x = x, 
                 y = y,
                 color_discrete_sequence=px.colors.sequential.Plasma)
    return fig

def line_chart(df:pd.DataFrame,
               x:list,
               y:list):
    fig = px.line(df, 
                  x = x, 
                  y = y,
                  color_discrete_sequence=px.colors.sequential.Plasma)
    return fig

def scatter_chart(df:pd.DataFrame,
                  x:list,
                  y:list):
    fig = px.scatter(df, 
                     x = x, 
                     y = y,
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

def generate_chart(df, chart_type, x, y):
    # filtered_data = df[df[chart_json['filter']['column']].isin(chart_json['filter']['value'])]
    filtered_data = df.copy()

    if chart_type == 'pie':
        fig = pie_chart(df = filtered_data,
                        x = x,
                        y = y)
    elif chart_type == 'line':
        fig = line_chart(df = filtered_data,
                         x = x,
                         y = y)
    elif chart_type == 'bar':
        fig = bar_chart(df = filtered_data,
                        x = x[0],
                        y = y)
    elif chart_type == 'scatter':
        fig = scatter_chart(df = filtered_data,
                            x = x,
                            y = y)
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
        print(f'Output: {output}')
        used_col = get_column_needed(df = df, generated_text = output)
        print(f'Columns: {used_col}')
        x, y = get_chart_axis(df = df, column = used_col)
        chart_type = suggest_chart_type(df = df, generated_text = output)

        # Generate chart
        try:
            fig = generate_chart(df = df,
                                 chart_type = chart_type,
                                 x = x,
                                 y = y)
        except:
            fig = generate_chart(df = df,
                                 chart_type = 'table',
                                 x = x,
                                 y = y)

        return fig
    else:
        # Return an empty figure
        return go.Figure()

# Run the app
if __name__ == '__main__':
    df = pd.read_csv(file)
    app.run_server(debug=True)
