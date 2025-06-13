import csv
import json
import re
import gzip
from pathlib import Path

# Archivos
CSV_PATH = Path("/home/ximena/Documentos/repos/final-project-cinedive/static/data/title_oscar_con_country.tsv")
NAMES_GZ = Path("/home/ximena/Documentos/repos/final-project-cinedive/static/data/name.basics.tsv.gz")
OUTPUT_PATH = Path("/home/ximena/Documentos/repos/final-project-cinedive/static/data/graph_full_cleaned.json")

# Cargar nombres de personas
def load_names(path: Path):
    names = {}
    with gzip.open(path, "rt", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            names[row["nconst"]] = row["primaryName"]
    return names

# Parser manual del campo `person`
def parse_person_field(text):
    matches = re.findall(r'\((nm\d+),(actor|actress),(\[.*?\])\)', text)
    result = []
    for pid, role, chars in matches:
        try:
            # eval seguro: convierte el string de lista a lista real
            characters = json.loads(chars.replace("'", '"'))
        except Exception:
            characters = []
        result.append((pid, role, characters))
    return result

# Inicializar estructura de grafo
graph = {"nodes": [], "links": []}
person_ids = set()
movie_ids = set()
name_map = load_names(NAMES_GZ)

# Procesar CSV
with CSV_PATH.open(encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        movie_id = row["tconst"]
        if movie_id in movie_ids:
            continue
        movie_ids.add(movie_id)

        # Nodo de película
        graph["nodes"].append({
            "id": movie_id,
            "type": "movie",
            "title": row["primaryTitle"],
            "year": int(row["startYear"]) if row["startYear"].isdigit() else None,
            "genres": [g.strip() for g in row["genres"].split(",")] if row["genres"] else [],
            "averageRating": float(row["averageRating"]) if row["averageRating"] else None,
            "numVotes": int(row["numVotes"]) if row["numVotes"] else None,
            "oscarNominations": int(row["oscarNominations"]) if row["oscarNominations"] else 0,
            "oscarWins": int(row["oscarWins"]) if row["oscarWins"] else 0,
            "country_origin": row["country_origin"]
        })

        year = int(row["startYear"]) if row["startYear"].isdigit() else None

        # Directores
        for d in row["directors"].split(","):
            if d.startswith("nm"):
                person_ids.add(d)
                graph["links"].append({
                    "source": d,
                    "target": movie_id,
                    "role": "director",
                    "year": year
                })

        # Escritores
        for w in row["writers"].split(","):
            if w.startswith("nm"):
                person_ids.add(w)
                graph["links"].append({
                    "source": w,
                    "target": movie_id,
                    "role": "writer",
                    "year": year
                })

        # Actores/actrices
        for pid, role, characters in parse_person_field(row["person"]):
            person_ids.add(pid)
            graph["links"].append({
                "source": pid,
                "target": movie_id,
                "role": role,
                "characters": characters,
                "year": year
            })

# Nodos de personas
for pid in sorted(person_ids):
    if pid not in movie_ids:
        graph["nodes"].append({
            "id": pid,
            "type": "person",
            "name": name_map.get(pid, "")
        })

# Guardar grafo
with OUTPUT_PATH.open("w", encoding="utf-8") as f:
    json.dump(graph, f, indent=2, ensure_ascii=False)

print(f" Grafo creado con {len(graph['nodes'])} nodos y {len(graph['links'])} enlaces.")
