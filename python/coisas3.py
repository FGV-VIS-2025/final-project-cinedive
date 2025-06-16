import json
import csv

# Carga tu JSON (ejemplo)
with open('/home/lenovo/Documentos/repos/final-project-cinedive/static/data/graph_full_cleaned.json', 'r') as f:
     data = json.load(f)

# Suponiendo que tu variable es:
# data = {...}

# 1. Crea diccionarios para lookup rápido
movie_lookup = {n["id"]: n for n in data["nodes"] if n["type"] == "movie"}
person_lookup = {n["id"]: n for n in data["nodes"] if n["type"] == "person"}

# 2. Abre archivo CSV y escribe cabecera
with open('/home/lenovo/Documentos/repos/final-project-cinedive/static/data/radial_people.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow([
        "personId", "personName", "movieId", "movieTitle", "year",
        "averageRating", "numVotes", "oscarNominations", "oscarWins", "role"
    ])

    # 3. Recorre links y escribe fila para cada relación persona-película
    for link in data["links"]:
        person_id = link["source"]
        movie_id = link["target"]
        role = link["role"]

        # Puede que haya links entre personas, filtra si hace falta
        if person_id not in person_lookup or movie_id not in movie_lookup:
            continue

        person_name = person_lookup[person_id].get("name", "")
        movie = movie_lookup[movie_id]

        writer.writerow([
            person_id,
            person_name,
            movie_id,
            movie.get("title", ""),
            movie.get("year", ""),
            movie.get("averageRating", ""),
            movie.get("numVotes", ""),
            movie.get("oscarNominations", ""),
            movie.get("oscarWins", ""),
            role
        ])
