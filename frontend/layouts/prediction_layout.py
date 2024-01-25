from dash import dcc, dash_table, html

from frontend.data.remote_data import fetch_user_balance, fetch_prediction_history
from frontend.ui_kit.components.user_balance import user_balance
from frontend.ui_kit.styles import table_style, table_header_style, table_cell_style, input_style, \
    dropdown_style, secondary_button_style, text_style, heading5_style, primary_button_style
from frontend.ui_kit.utils import format_timestamp


# Components
def create_merchant_cluster_pair(index):
    return html.Div([
        dcc.Input(id={'type': 'input-merchant', 'index': index}, type='number', placeholder='Merchant ID',
                  style={**input_style, 'marginRight': '10px'}),
        dcc.Input(id={'type': 'input-cluster', 'index': index}, type='number', placeholder='Cluster ID',
                  style=input_style),
        html.Button('Remove', id={'type': 'remove-pair', 'index': index}, n_clicks=0, style=secondary_button_style)
    ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '5px'})


def prediction_form():
    return html.Div([
        dcc.Dropdown(
            id='model-dropdown',
            options=[],
            placeholder='Select a prediction model',
            style={**dropdown_style, 'marginBottom': '20px'}
        ),
        # html.Div(id='merchant-cluster-pairs', children=[create_merchant_cluster_pair(0)]),
        html.Div([
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files')
                ]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px'
                },
                # Allow multiple files to be uploaded
                multiple=True
            ),
            html.Div(id='output-data-upload'),
        ]),
        
        html.Div([
            # html.Button('Add Pair', id='add-pair-button', n_clicks=0,
            #             style={**secondary_button_style, 'marginRight': '10px', 'marginLeft': '0px'}),
            html.Button('Predict', id='predict-button', n_clicks=0,
                        style=primary_button_style)
        ], style={'display': 'flex', 'justifyContent': 'flex-start', 'marginBottom': '20px'}),
        html.Div(estimated_cost(None), id='estimated-cost'),
    ], style={'marginBottom': '40px'})


def prediction_history_table(predictions):
    if not predictions:
        return html.Div("No prediction history available", style=text_style)

    batches = {}
    for prediction in predictions:
        batch_key = (prediction["model_name"], prediction["timestamp"], prediction["cost"], prediction["id"])
        if batch_key not in batches:
            batches[batch_key] = []
        batches[batch_key].extend(prediction.get('predictions', []))

    batch_tables = []
    for (model_name, timestamp, cost, _), preds in batches.items():
        data = [
            {
                "N_Days": pred["features"]["N_Days"],
                "Drug": pred["features"]["Drug"],
                "Age": pred["features"]["Age"],
                "Sex": pred["features"]["Sex"],
                "Bilirubin": pred["features"]["Bilirubin"],
                "predicted_category": pred["target"]["answer"],
            }
            for pred in preds
        ]

        columns = [
            {"name": "N_Days", "id": "N_Days"},
            {"name": "Drug", "id": "Drug"},
            {"name": "Age", "id": "Age"},
            {"name": "Sex", "id": "Sex"},
            {"name": "Bilirubin", "id": "Bilirubin"},
            {"name": "Predicted Category", "id": "predicted_category"},
        ]

        batch_info = html.Div([
            html.H5(f"{model_name}, {format_timestamp(timestamp)}, Cost: {abs(cost)}", style=heading5_style),
            dash_table.DataTable(
                columns=columns,
                data=data,
                style_table=table_style,
                style_cell=table_cell_style,
                style_header=table_header_style
            )
        ])

        batch_tables.append(batch_info)

    return html.Div(batch_tables)


def estimated_cost(total_cost):
    if total_cost is None:
        return html.Div("Select a model, enter parameters and press the button to get prediction.",
                        style=text_style)
    return html.Div(f"Estimated cost: {total_cost}", style=text_style)


# Layout
def prediction_layout(user_session):
    balance = fetch_user_balance(user_session)
    predictions = fetch_prediction_history(user_session)
    return html.Div([
        html.Div(user_balance(balance), id='current-balance-predictions'),
        prediction_form(),
        html.Div(prediction_history_table(predictions), id='prediction-history-table')
    ])
