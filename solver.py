import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist


def create_distance_matrix(df):
    df_coords = df[["x", "y"]]

    coords = df_coords.to_numpy()
    dist_matrix = cdist(coords, coords)
    return dist_matrix


def create_depot_distance_array(df, depot_coords):
    df_coords = df[["x", "y"]]

    coords = df_coords.to_numpy()
    dist_matrix = cdist([depot_coords], coords)
    return dist_matrix[0]


def sweep_algorithm(df, capacity):
    k = 1
    loads = {}
    loads[k] = 0
    roads = {}
    roads[k] = []
    index = 0
    for index, row in df.iterrows():
        if (loads[k] + row["demand"]) <= capacity:
            loads[k] += row["demand"]
            roads[k].append(index)
        else:
            k += 1
            loads[k] = row["demand"]
            roads[k] = [index]
    return loads, roads


def count_vehicle_distances(roads, distance_matrix, depot_distance_array):

    distances = {}
    k = 1
    for road in roads.values():
        road_distance = 0
        for i in range(len(road) - 1):
            point1 = road[i]
            point2 = road[i + 1]
            road_distance += distance_matrix[point1 - 1, point2 - 1]

        # from and to depot
        road_distance += depot_distance_array[road[0] - 1]
        road_distance += depot_distance_array[road[-1] - 1]
        distances[k] = round(road_distance, 2)
        k = k + 1

    return distances


def sort_by_angle(df, start_angle=0):
    df["angle"] = np.arctan2(df["y"], df["x"])
    df["angle"] = df["angle"] * 180 / np.pi + 180
    sorted_df = df.sort_values("angle")

    # shift by number of rows greater than start angle
    shift = len(sorted_df[sorted_df["angle"] >= start_angle])
    sorted_df = sorted_df.apply(np.roll, shift=shift)
    return sorted_df


def solver(df, capacity, iterations, depot_coords):
    distance_matrix = create_distance_matrix(df)
    depot_distance_array = create_depot_distance_array(df, depot_coords)

    min_distance = float("inf")
    best_routes = {}
    best_loads = {}

    # for start angles
    for start_angle in np.linspace(0, 360, iterations):
        sorted_df = sort_by_angle(df, start_angle)
        loads, roads = sweep_algorithm(sorted_df, capacity)
        distances = count_vehicle_distances(
            roads, distance_matrix, depot_distance_array
        )
        # print(f'Start angle: {start_angle}, Distance: {distance}')
        total_distance = sum(distances)
        if total_distance < min_distance:
            min_distance = total_distance
            best_routes = roads
            best_loads = loads
            best_distances = distances
    # print(f'\n\nBEST RESULT: {min_distance}\n'
    #       f'ROUTES: {best_routes}\n'
    #       f'VEHICLES CAPACITY: {best_loads})')

    return min_distance, best_routes, best_loads, best_distances
