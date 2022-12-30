from dash import Dash, dash_table, dcc, html
from dash.dependencies import Input, Output, State
from solver import solver

import dash_cytoscape as cyto
import plotly.express as px
import pandas as pd
import numpy as np
import base64
import datetime
import io

import pandas as pd

df = pd.DataFrame(
    {"localization": ["Magazine", "L1"], "x": [0, 1], "y": [0, 3], "demand": [4, 1]}
)

output_df = pd.DataFrame(
    {
        "vehicle": ["V1", "V2"],
        "route": [[0, 1, 2, 0], [0, 3, 4, 0]],
        "load": [0.80, 0.3],
    }
)

# MAIN

app = Dash(__name__)

app.layout = html.Div(
    [
        dcc.Tabs(
            [
                dcc.Tab(
                    id="data-tab",
                    label="Data",
                    children=[
                        dcc.Upload(
                            id="upload-data",
                            children=html.Div(
                                ["Drag and Drop or ", html.A("Select Files")]
                            ),
                            style={
                                "width": "100%",
                                "height": "120px",
                                "lineHeight": "60px",
                                "borderWidth": "1px",
                                "borderStyle": "dashed",
                                "borderRadius": "5px",
                                "textAlign": "center",
                                "margin": "10px",
                            },
                            multiple=False,
                        ),
                        dash_table.DataTable(
                            id="adding-rows-table",
                            columns=[
                                {
                                    "id": "localization",
                                    "name": "Localization",
                                    "type": "text",
                                },
                                {"id": "x", "name": "X", "type": "numeric"},
                                {"id": "y", "name": "Y", "type": "numeric"},
                                {"id": "demand", "name": "Demand", "type": "numeric"},
                            ],
                            data=df.to_dict("records"),
                            editable=True,
                            row_deletable=True,
                        ),
                        html.Button(
                            "Add localization", id="editing-rows-button", n_clicks=0
                        ),
                        html.Div(
                            [
                                html.Br(),
                                html.B("Capacity limit for one vehicle:"),
                                dcc.Input(
                                    id="capacity_limit_input", type="number", value=20
                                ),
                            ]
                        ),
                        dcc.Graph(id="adding-rows-graph"),
                    ],
                ),
                dcc.Tab(
                    id="alogorithm-tab",
                    label="Sweep Algorithm",
                    children=[
                        html.Div(
                            [
                                html.Br(),
                                html.B("Number of iterations"),
                                dcc.Input(
                                    id="iterations_number_input",
                                    type="number",
                                    value=50,
                                ),
                            ],
                        ),
                        html.Button(
                            "Start algorithm", id="start-algorithm-button", n_clicks=0
                        ),
                        html.Div(
                            id="output-state", children="Enter a value and press submit"
                        ),
                    ],
                ),
            ]
        )
    ]
)


@app.callback(
    Output("adding-rows-table", "data"),
    Input("editing-rows-button", "n_clicks"),
    State("adding-rows-table", "data"),
    State("adding-rows-table", "columns"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    State("upload-data", "last_modified"),
)
def add_row(n_clicks, rows, columns, contents, filename, date):
    global df
    if n_clicks > 0:
        rows.append({c["id"]: "" for c in columns})

    if contents:
        df = parse_contents(contents, filename, date)
        rows = df.to_dict("records")
    return rows


@app.callback(
    Output("adding-rows-graph", "figure"),
    Input("adding-rows-table", "data"),
    Input("adding-rows-table", "columns"),
)
def display_output(rows, columns):
    global df

    plot_df = pd.DataFrame(rows).replace("", np.nan).dropna()
    plot_df["type"] = ["Magazine"] + (len(plot_df) - 1) * ["Localization"]
    fig = px.scatter(
        plot_df,
        x="x",
        y="y",
        labels="localiztion",
        size=[5] * len(plot_df),
        color="type",
    )
    df = plot_df[["demand", "localization", "x", "y"]].copy()

    return fig


@app.callback(
    Output("output-state", "children"),
    Input("start-algorithm-button", "n_clicks"),
    Input("capacity_limit_input", "value"),
    Input("iterations_number_input", "value"),
)
def update_output(n_clicks, capacity, iterations):
    if n_clicks == 0:
        return ""
    else:
        # depot_coords = (0, 0)
        # df[['x', 'y']].iloc[0] -> depot coordinates
        iterations = int(iterations)
        min_distance, best_routes, best_loads = solver(
            df[1:], capacity, iterations, df[["x", "y"]].iloc[0]
        )
        print(
            pd.DataFrame(
                {
                    "vehicle": list(range(1, len(best_loads) + 1)),
                    "route": best_routes.values(),
                    "load": best_loads.values(),
                }
            ).to_dict("records")
        )

        output_df = pd.DataFrame(
            {
                "vehicle": list(range(1, len(best_loads) + 1)),
                "route": best_routes.values(),
                "load": best_loads.values(),
            }
        )

        # create data for graph
        ls1 = [{"data": {"id": a, "label": a}} for a in df["localization"]]
        ls2 = []
        for route in output_df["route"]:
            route.append("Magazine")
            route.insert(0, "Magazine")
            for a, b in zip(route[:-1], route[1:]):
                if a != "Magazine":
                    a = f"L{a}"
                if b != "Magazine":
                    b = f"L{b}"
                ls2.append({"data": {"source": a, "target": b}})
        graph_elements = ls1 + ls2

        return html.Div(
            id="output-state",
            children=[
                dash_table.DataTable(
                    id="output-table",
                    columns=[
                        {"id": "vehicle", "name": "Vehicle", "type": "numeric"},
                        {"id": "route", "name": "Route", "type": "text"},
                        {"id": "load", "name": "Load", "type": "numeric"},
                    ],
                    data=output_df.astype(str).to_dict("records"),
                ),
                cyto.Cytoscape(
                    id="cytoscape",
                    elements=graph_elements,
                    layout={"name": "cose"},
                    style={"width": "1080px", "height": "720px"},
                ),
            ],
        )


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(",")

    decoded = base64.b64decode(content_string)
    try:
        if "csv" in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
            return df
        elif "xls" in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
            return df
    except Exception as e:
        print(e, "There was an error processing this file.")


if __name__ == "__main__":
    app.run_server(debug=True)
