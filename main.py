import pandas as pd

from solver import solver

# Input data
df = pd.read_excel('dane.xlsx', sheet_name='clients', header=0, index_col=0)
df = df.replace(',', '.').astype(float)

capacity = 15
iterations = 24
depot_coords = (0, 0)

if __name__ == "__main__":
    min_distance, best_routes, best_loads = solver(df, capacity, iterations, depot_coords)

    '''
    import plotly.graph_objects as go
    fig = go.Figure()
    for index, route in best_routes.items():
        x = [df.loc[point].x for point in route]
        y = [df.loc[point].y for point in route]

        x = [depot_coords[0]] + x + [depot_coords[0]]
        y = [depot_coords[1]] + y + [depot_coords[1]]

        fig.add_trace(go.Scatter(x=x, y=y,
                                 mode='lines+markers',
                                 name=index))
    fig.show()
    '''
    print(df)