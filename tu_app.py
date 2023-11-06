from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
import networkx as nx
app = Flask(__name__)
CORS(app)

# Cargar los datos y calcular las métricas una sola vez al iniciar la aplicación
data = pd.read_csv('globalairpollution.csv')
air_quality_columns = ['AQI Value', 'Ozone AQI Value', 'PM2.5 AQI Value']

G = nx.Graph()
city_air_quality = {}

def calculate_average(row):
    return sum([row[column] for column in air_quality_columns]) / len(air_quality_columns)

for i, row in data.iterrows():
    source_node = row['Country'] + '-' + row['City']
    G.add_node(source_node)
    city_air_quality[source_node] = calculate_average(row[air_quality_columns])

for source_node in G.nodes:
    for target_node in G.nodes:
        if source_node != target_node:
            difference = abs(city_air_quality[source_node] - city_air_quality[target_node])
            weight = 1 / (difference + 0.1)
            G.add_edge(source_node, target_node, weight=weight)

# Definir una función para calcular los resultados
def calcular_resultados(source_node):
    shortest_path = nx.shortest_path(G, source=source_node, weight='weight')
    
    # Calcular el camino más corto y su peso
    shortest_path_data = []
    for target in shortest_path:
        if source_node != target:
            weight = G[source_node][target]['weight']
            shortest_path_data.append({
                'target': target,
                'weight': round(weight, 4)
            })

    # Encontrar el país-ciudad con el menor peso
    min_weight = float('inf')
    min_weight_city = None
    for city in G.nodes:
        if city != source_node and city in shortest_path:
            weight = G[source_node][city]['weight']
            if weight < min_weight:
                min_weight = weight
                min_weight_city = city

    # Obtener la calidad del aire del nodo de origen
    air_quality_origin = city_air_quality.get(source_node, None)

    return {
        'shortest_path': shortest_path_data,
        'min_weight_city': min_weight_city,
        'min_weight': round(min_weight, 4),
        'air_quality_origin': round(air_quality_origin,4)
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calcular', methods=['POST'])
def calcular():
    data = request.get_json()
    source_node = data.get('source_node')  # Asegurar que esto coincida con los datos del formulario
    
    if source_node:
        resultados = calcular_resultados(source_node)
        return jsonify(resultados)
    else:
        return jsonify({'error': 'Falta el nodo de inicio en la solicitud'})

if __name__ == '__main__':
    app.run()
