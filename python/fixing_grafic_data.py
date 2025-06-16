import csv
import json
from collections import defaultdict

with open('../static/data/graph_full_cleaned.json', encoding='utf-8') as f:
    graph_data = json.load(f)
    
def parse_list_field(raw):
    """
    Garante que o resultado seja uma lista, mesmo se for uma string simples.
    """
    raw = raw.strip()
    if not raw:
        return []

    try:
        value = ast.literal_eval(raw)
        if isinstance(value, list):
            return value
        else:
            return [str(value)]
    except (ValueError, SyntaxError):
        return [raw]


movie_country = {}
for node in graph_data["nodes"]:
    if node.get("type") == "movie":
        movie_country[node["id"]] = node.get("country_origin", "Unknown")

csv_file = '../static/data/radial_people.csv'
nodes_dict = {}
movie_to_people = defaultdict(list)
movie_title_year_map = {}

with open(csv_file, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        pid = row['personId']
        name = row['personName']
        role = row['role']
        movieId = row['movieId']
        movie = row['movieTitle']
        year = row['year']
        country_list = parse_list_field(row.get('country_origin', ''))
        country = country_list[0] if country_list else None

        if pid not in nodes_dict:
            nodes_dict[pid] = {
                "id": pid,
                "name": name,
                "roles": set(),
                "years": [],
                "country": country
            }
        nodes_dict[pid]["roles"].add(role)
        if year not in nodes_dict[pid]["years"]:
            nodes_dict[pid]["years"].append(year)

        movie_to_people[movieId].append(pid)
        movie_title_year_map[movieId] = (movie, year)

nodes = []
for pid, info in nodes_dict.items():
    nodes.append({
        "id": pid,
        "name": info["name"],
        "type": ", ".join(sorted(info["roles"])),
        "years": sorted(info["years"]),
        "country": info["country"]
    })

links_dict = defaultdict(lambda: {"filmes": set(), "years": set(), "countries": set()})

for movieId, people in movie_to_people.items():
    title, year = movie_title_year_map[movieId]
    country = movie_country.get(movieId, "Unknown")

    for i in range(len(people)):
        for j in range(i + 1, len(people)):
            source, target = sorted([people[i], people[j]])
            key = (source, target)
            links_dict[key]["filmes"].add(title)
            links_dict[key]["years"].add(year)
            links_dict[key]["countries"].add(country)

links = []
for (source, target), info in links_dict.items():
    links.append({
        "source": source,
        "target": target,
        "filmes": list(info["filmes"]),
        "year": ", ".join(sorted(info["years"])),
        "country": ", ".join(sorted(info["countries"]))
    })

output = {
    "nodes": nodes,
    "links": links
}

with open('../static/data/graphic_person.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

