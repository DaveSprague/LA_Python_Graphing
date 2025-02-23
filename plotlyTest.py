import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import random
from datetime import datetime

# Initialize the Dash app
app = dash.Dash(__name__)

# Layout of the app
app.layout = html.Div([
    dcc.Graph(id='live-graph', animate=True),
    dcc.Interval(
        id='graph-update',
        interval=1000,  # Update every second
        n_intervals=0
    ),
    dcc.Store(id='data-store', data=[])
])

# Callback to update the graph
@app.callback(
    Output('live-graph', 'figure'),
    [Input('graph-update', 'n_intervals')],
    [State('data-store', 'data')]
)
def update_graph(n, data):
    new_data = {
        'timestamp': datetime.now(),
        'value': random.uniform(0, 10)
    }
    data.append((new_data['timestamp'], new_data['value']))
    data = data[-100:]  # Keep only the last 100 data points

    df = pd.DataFrame(data, columns=['Timestamp', 'Value'])
    df.set_index('Timestamp', inplace=True)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['Value'], mode='lines', name='Random Data'))
    fig.update_layout(title='Live Random Data', xaxis_title='Time', yaxis_title='Value')

    return fig

# Callback to update the data store
@app.callback(
    Output('data-store', 'data'),
    [Input('graph-update', 'n_intervals')],
    [State('data-store', 'data')]
)
def update_data_store(n, data):
    new_data = {
        'timestamp': datetime.now(),
        'value': random.uniform(0, 10)
    }
    data.append((new_data['timestamp'], new_data['value']))
    return data[-100:]  # Keep only the last 100 data points

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)