import pandas as pd
import numpy as np
import sys
import os
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.chem_utils import lookup_compound, get_rdkit_properties
from src.analysis import MASTER_DB_PATH

def clean_desc(val):
    if pd.isna(val) or not isinstance(val, str):
        return ""
    # Strip whitespace, reduce multiple spaces/commas
    cleaned = ", ".join([v.strip() for v in val.split(',') if v.strip()])
    return cleaned

def enrich_database():
    print(f"Loading database from {MASTER_DB_PATH}...")
    if not os.path.exists(MASTER_DB_PATH):
        print("Master DB file not found.")
        return

    df = pd.read_csv(MASTER_DB_PATH)
    print(f"Loaded {len(df)} compounds.")

    # 1. Cleanup Descriptions
    print("Cleaning up descriptions...")
    df['Desc_Korean'] = df['Desc_Korean'].apply(clean_desc)
    df['Desc_English'] = df['Desc_English'].apply(clean_desc)
    df['Groups'] = df['Groups'].apply(clean_desc)

    # 2. Batch Update Properties
    print("Enriching properties from PubChem/RDKit (this may take a while)...")
    
    updated_count = 0
    for idx, row in df.iterrows():
        cas = str(row['CAS'])
        name = str(row['Name_Common'])
        
        # Determine if we need an update
        needs_update = (
            pd.isna(row.get('SMILES')) or str(row.get('SMILES')).strip() == "" or
            pd.isna(row.get('MW')) or float(row.get('MW')) == 0.0 or
            pd.isna(row.get('LogP')) or float(row.get('LogP')) == 0.0 or
            pd.isna(row.get('Groups')) or str(row.get('Groups')).strip() == ""
        )
        
        if needs_update:
            search_query = cas if cas and cas != 'nan' else name
            if not search_query or search_query == 'nan':
                continue
                
            print(f"[{idx+1}/{len(df)}] Fetching info for: {search_query} ({name})...")
            
            try:
                info = lookup_compound(search_query)
                if info and not info.get('error'):
                    smiles = info.get('smiles', row.get('SMILES'))
                    df.at[idx, 'SMILES'] = smiles
                    
                    if smiles:
                        props = get_rdkit_properties(smiles)
                        if not props.get('error'):
                            df.at[idx, 'MW'] = props.get('molecular_weight', row.get('MW'))
                            df.at[idx, 'LogP'] = props.get('log_p', row.get('LogP'))
                            # If groups is empty, update it
                            if pd.isna(row.get('Groups')) or str(row.get('Groups')).strip() == "":
                                df.at[idx, 'Groups'] = props.get('functional_groups', "")
                    
                    updated_count += 1
                
                # Throttling to be polite to PubChem
                time.sleep(0.2)
            except Exception as e:
                print(f"Error updating {name}: {e}")

    # 3. Save
    print(f"Saving enriched database. Total updated: {updated_count}")
    df.to_csv(MASTER_DB_PATH, index=False, encoding='utf-8-sig')
    print("Done.")

if __name__ == "__main__":
    enrich_database()
