import json
import csv

with open('./static/data/graph_full_cleaned.json', 'r', encoding='utf-8') as f:
     data = json.load(f)



movie_lookup = {n["id"]: n for n in data["nodes"] if n["type"] == "movie"}
person_lookup = {n["id"]: n for n in data["nodes"] if n["type"] == "person"}

with open('./static/data/radial_people.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow([
        "personId", "personName", "movieId", "movieTitle", "year",
        "averageRating", "numVotes", "oscarNominations", "oscarWins", "role", "country_origin"
    ])

    for link in data["links"]:
        person_id = link["source"]
        movie_id = link["target"]
        role = link["role"]
        

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
            role,
            movie.get("country_origin", "")
            
        ])
