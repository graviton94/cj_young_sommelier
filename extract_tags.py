import pandas as pd
from pathlib import Path

db_path = Path("c:/cj_young_sommelier/data/master_flavor_db.csv")
df = pd.read_csv(db_path)

def get_unique_tags(series):
    tags = set()
    for val in series.dropna():
        # Split by comma and strip whitespace
        parts = [p.strip() for p in str(val).split(',') if p.strip()]
        tags.update(parts)
    return sorted(list(tags))

ko_tags = get_unique_tags(df['Desc_Korean'])
en_tags = get_unique_tags(df['Desc_English'])

with open("final_tags.txt", "w", encoding="utf-8-sig") as f:
    f.write("--- KOREAN DESC TAGS ---\n")
    f.write(", ".join(ko_tags))
    f.write("\n\n--- ENGLISH DESC TAGS ---\n")
    f.write(", ".join(en_tags))
