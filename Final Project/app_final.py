import pandas as pd
import re
import json
import requests
import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go
import plotly.express as px
import base64
import io

################################################################################################################
################################################## PARAMETERS ##################################################
################################################################################################################

file = 'https://github.com/prattapong/DADS5001/blob/main/Final%20Project/association_file.csv?raw=True'
API_URL = 'https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1'
headers = {'Authorization': f'Bearer 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'}
# df = pd.read_csv(file)

################################################################################################################
################################################### FUNCTIONS ##################################################
################################################################################################################

################################################# I/O Functions ################################################ 

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

def format_instruction(prompt:str,
                       instruction: str):
    instruction_prompt = prompt
    instruction_text = "[INST] " + instruction_prompt + instruction + " [/INST]"
    return instruction_text

def format_output(output, instruction):
    output = output.replace(instruction, '').strip()
    return output

def generate_output(instruction: str,
                    prompt:str):
    instruction = format_instruction(instruction = instruction, prompt = prompt)
    data = query({"inputs": instruction,
                  "parameters" : {"max_length": 10000}})
    output = format_output(output = data, instruction = instruction)
    return output

################################################ Chart Handling ################################################

def get_chart_prompt():
    global df
    chart_prompt = f"""
    My data contains columns: {', '.join(df.columns)}.
    Chart options: Bar, Scatter, Pie, Line, Box plot 
    Please shortly suggest chart type and columns (based on column names provided) needed for the following question:
    
    """
    return chart_prompt

def get_column_needed(df:pd.DataFrame, generated_text:str):
    used_col = [col for col in df.columns if col.lower() in generated_text.replace('\\','').lower()]
    return used_col

def get_axis_promt():
    axis_prompt = f"""
    Return me this form {{"dimension": ["xxx"], "metrics": ["yyy"]}} from the column lists:
    """
    return axis_prompt

def extract_dimension_metrics(generated_text:str):
    # pattern = r'"dimension"\s*:\s*\["(.*?)"\]'
    dimension_pattern_1 = r'"dimension"\s*:\s*(\["([^xxx"]*)"])'
    dimension_pattern_2 = r'"dimension"\s*:\s*(\[.*?\])'
    metrics_pattern_1 = r'"metrics"\s*:\s*(\["([^yyy"]*)"])'
    metrics_pattern_2 = r'"metrics"\s*:\s*(\[.*?\])'

    dimension_match_1 = re.search(dimension_pattern_1, generated_text)
    dimension_match_2 = re.search(dimension_pattern_2, generated_text)
    metrics_match_1 = re.search(metrics_pattern_1, generated_text)
    metrics_match_2 = re.search(metrics_pattern_2, generated_text)

    if dimension_match_1:
        x = dimension_match_1.group(1).replace('\\','')
        x = json.loads(x)
    elif dimension_match_2:
        x = dimension_match_2.group(1).replace('\\','')
        x = json.loads(x)
    else:
        x = []
    if metrics_match_1:
        y = metrics_match_1.group(1).replace('\\','')
        y = json.loads(y)
    elif metrics_match_2:
        y = metrics_match_2.group(1).replace('\\','')
        y = json.loads(y)
    else:
        y = []
    
    return x, y

def get_chart_axis(df:pd.DataFrame, column:list, x, y):
    # x = []
    # y = []

    if x == [] and y ==[]:
        for col in column:
            if str(df[col].dtype) in ['object', 'str', 'string']:
                x.append(col)
            elif col.lower() in ['date', 'year', 'month', 'week']:
                x.append(col)
            else:
                y.append(col)
    elif x == [] and len(y) > 1:
        for col in column:
            if str(df[col].dtype) in ['object', 'str', 'string']:
                x.append(col)
                y.remove(col)
            elif col.lower() in ['date', 'year', 'month', 'week']:
                x.append(col)
                y.remove(col)
    elif y == [] and len(x) > 1:
        for col in column:
            if str(df[col].dtype) not in ['object', 'str', 'string'] and col.lower() in ['date', 'year', 'month', 'week']:
                y.append(col)
                x.remove(col)

    return x, y

def suggest_chart_type(df:pd.DataFrame, generated_text:str):
    if 'scatter' in generated_text.lower():
        return 'scatter'
    elif 'pie' in generated_text.lower():
        return 'pie'
    elif 'line' in generated_text.lower():
        return 'line'
    else:
        return 'bar'

def parse_contents(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    if 'csv' in content_type:
        # Decode CSV
        df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))

    elif 'xls' in content_type:
        # Decode Excel
        df = pd.read_excel(io.StringIO(decoded.decode('utf-8')))
        # decoded = pd.read_excel(io.BytesIO(content_string))

    return df

################################################ Chart Functions ###############################################

def pie_chart(df:pd.DataFrame,
              x:list,
              y:list):
              
    fig = px.pie(df, 
                 names = x[0],
                 values = y[0],
                 color_discrete_sequence = px.colors.sequential.Plasma_r,
                 hole = 0.4)
    return fig

def bar_chart(df:pd.DataFrame,
              x:list,
              y:list):
    bar_df = df.copy()
    bar_df[x[0]] = bar_df[x[0]].astype('object')
    fig = px.bar(df, 
                 x = x[0], 
                 y = y[0],
                 color_discrete_sequence = px.colors.sequential.Plasma)
    return fig

def line_chart(df:pd.DataFrame,
               x:list,
               y:list):
    fig = px.line(df, 
                  x = x, 
                  y = y,
                  color_discrete_sequence = px.colors.sequential.Plasma)
    return fig

def scatter_chart(df:pd.DataFrame,
                  x:list,
                  y:list):
    scatter_df = df.copy()
    scatter_df[y].fillna(0, inplace = True)
    scatter_df[x[0]].fillna('NA', inplace = True)
    try:
        scatter_df[x[1]].fillna('NA', inplace = True)
    except:
        pass
    
    if len(x) == 1:
        fig = px.scatter(scatter_df, 
                         x = x[0], 
                         y = y[0],
                         color_discrete_sequence = px.colors.sequential.Plasma)
    elif scatter_df[x[0]].nunique() > scatter_df[x[1]].nunique():
        fig = px.scatter(scatter_df, 
                         x = x[0], 
                         y = y[0],
                         color = x[1],
                         color_discrete_sequence = px.colors.sequential.Plasma)
    else:
        fig = px.scatter(scatter_df, 
                         x = x[1], 
                         y = y[0],
                         color = x[0],
                         color_discrete_sequence = px.colors.sequential.Plasma)
    return fig

def box_plot(df:pd.DataFrame,
             x:list,
             y:list):
    fig = px.box(df, 
                 x = x[0], 
                 y = y,
                 color_discrete_sequence = px.colors.sequential.Plasma)
    return fig

def table_chart(df):
    fig = go.Figure(
        data = [
            go.Table(
                header = dict(values = list(df.columns),
                              fill_color = 'lightblue',
                              line_color = 'black',
                              align = 'left'),
                cells = dict(values = [df[col] for col in df.columns],
                             fill_color = 'white',
                             line_color = 'black',
                             align = 'left')
            )
        ]
    )
    return fig

def generate_chart(chart_type, x, y):
    global df
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
                        x = x,
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
                    'DADS5001', 
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

        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            dcc.Upload(
                                id = 'upload-data',
                                children=html.Div(
                                    [
                                        'Drag and Drop or ',
                                        html.A('Select Files')
                                    ],
                                    style = {'width': '100%'}
                                ),
                                style = {'width': '100%',
                                         'height': '60px',
                                         'lineHeight': '60px',
                                         'borderWidth': '1px',
                                         'borderStyle': 'dashed',
                                         'borderRadius': '5px',
                                         'textAlign': 'center',
                                         'margin': '10px'
                                },
                                multiple = False
                            ),
                            html.Div(id = 'output-data-upload')
                        ]
                    )
                )
            ]
        ),

        # Filter 1
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            html.P(
                                'Filter Field', 
                                style = {'margin-top': '8px', 
                                         'margin-bottom': '4px',
                                         **custom_css}, 
                                className = 'font-weight-bold',
                            ),
                            dcc.Dropdown(
                                id = 'filter-1',
                                multi = False,
                                # options = [{'label': x, 'value': x} for x in ['option1','option2']],
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
                                'Filter Value', 
                                style = {'margin-top': '16px', 'margin-bottom': '4px'}, 
                                className = 'font-weight-bold'
                            ),
                            dcc.Dropdown(
                                id = 'filter-2',
                                multi = True,
                                # options = [{'label': x, 'value': x} for x in ['option1','option2']],
                                style = {'width': '100%'}
                            ),
                            # html.Button(
                            #     id = 'my-button', 
                            #     n_clicks = 0, 
                            #     children = 'Apply',
                                #     style = {'width': '100%',
                                #              'height': '5vh',
                                #              'margin-top': '25px',
                                #              'margin-bottom': '6px',
                                #              'border': '1px',
                                #              'border-radius': '8px'},
                            #     className = 'bg-primary text-white font-italic'),
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
                                 'width': '85%',
                                 **custom_css}
                    ),
                    html.Button(
                        'Send', 
                        id='my-button', 
                        n_clicks=0,
                        style = {
                            'border-radius': '8px',
                            'margin-left': '3px',
                            'width': '80px'
                        },
                        className = 'bg-primary text-white font-italic'
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

################################################################################################################
################################################### CALLBACK ###################################################
################################################################################################################

################################################ File Uploading ################################################

@app.callback(
        [Output('output-data-upload', 'children'),
         Output('filter-1', 'options')],
        [Input('upload-data', 'contents')])
def update_output(contents):
    global df
    if contents is None:
        raise PreventUpdate
    
    df = parse_contents(contents)
    print(df.head())

    dimension_col = [col for col in df.columns if str(df[col].dtype) in ('object', 'str', 'string')]
    options = [{'label': x, 'value': x} for x in dimension_col]

    return html.Div(
        [
            html.H6('Columns:'),
            html.P(', '.join(df.columns)),
        
        ],
        style = {'margin-top': '20px'}
    ), options


################################################# Select Filter ################################################

@app.callback(
         Output('filter-2', 'options'),
        [Input('filter-1', 'value')])
def update_filter(selected_field):
    global df
    if selected_field is None:
        return []
    else:
        filter_value = df[selected_field].dropna().unique()
        print(filter_value)
        options = [{'label': x, 'value': x} for x in filter_value]
        print(options)
        return options


################################################# Update Chart #################################################

@app.callback(
    Output('dynamic-plot', 'figure'),
    Input('my-button', 'n_clicks'),
    [State('text-input', 'value'),
     State('filter-1', 'value'),
     State('filter-2', 'value')]
)

def update_dynamic_plot(n_clicks, input_text, filter_column, filter_value):
    global df
    print(filter_column)
    print(filter_value)
    print(input_text)
    if n_clicks > 0:
        # Generate output
        output = generate_output(instruction = input_text, prompt = get_chart_prompt())
        print(f'Output: {output}')
        print(df.columns)

        used_col = get_column_needed(df = df, generated_text = output)
        print(f'Columns: {used_col}')

        dimension_metrics_text = generate_output(instruction = ', '.join(used_col), prompt = get_axis_promt())
        print(f'Dimension Metrics Text: {dimension_metrics_text}')

        dimension, metrics = extract_dimension_metrics(generated_text = dimension_metrics_text)
        print(f'Dimension Metrics: {dimension, metrics}')

        x, y = get_chart_axis(df = df,
                              column = used_col,
                              x = dimension,
                              y = metrics)
        print(f'X = {x} | Type: {type(x)}')
        print(f'Y = {y} | Type: {type(y)}')
        chart_type = suggest_chart_type(df = df, generated_text = output)
        print(f'Chart Type = {chart_type}')

        # Generate chart
        try:
            fig = generate_chart(chart_type = chart_type,
                                 x = x,
                                 y = y)
            print('Plot Success')
        except:
            fig = generate_chart(chart_type = 'table',
                                 x = x,
                                 y = y)
            print('Plot Failed')

        return fig
    else:
        # Return an empty figure
        return go.Figure()

################################################################################################################
##################################################### MAIN #####################################################
################################################################################################################

if __name__ == '__main__':
    app.run_server(debug=True)
