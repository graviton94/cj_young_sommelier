"""
Chemical utility functions for retrieving compound information and properties.
Uses PubChemPy for lookup and RDKit for property calculation and structure generation.
"""

import logging

try:
    import pubchempy as pcp
except ImportError:
    pcp = None

try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, Draw, AllChem, Crippen
except ImportError:
    Chem = None

def lookup_compound(query_string):
    """
    Search for a compound by Name or CAS number using PubChem.
    
    Args:
        query_string (str): The name or CAS number of the compound.
        
    Returns:
        dict: A dictionary containing compound details, or None if not found.
    """
    if not pcp:
        return {"error": "PubChemPy is not installed."}
        
    try:
        compounds = pcp.get_compounds(query_string, 'name')
        if not compounds:
            # Try searching as if it might be a CAS (PubChem doesn't usually distinguish strict CAS search well via get_compounds(name) but often works)
            # Or assume it was a name input
            pass
            
        if not compounds:
            return None
            
        cmpd = compounds[0]
        
        info = {
            'name': cmpd.synonyms[0] if cmpd.synonyms else query_string,
            'iupac_name': cmpd.iupac_name,
            'cas_number': None, # PubChemPy doesn't always easily give CAS. We rely on user input often or parse synonyms.
            'smiles': cmpd.isomeric_smiles,
            'molecular_formula': cmpd.molecular_formula,
            'molecular_weight': float(cmpd.molecular_weight) if cmpd.molecular_weight else 0.0,
            'cid': cmpd.cid
        }
        
        # Try to extract a CAS-like string from synonyms if possible (simple heuristic)
        # Note: CAS parsing is complex, we might just leave blank if user didn't provide
        import re
        cas_pattern = re.compile(r'\d{1,7}-\d{2}-\d')
        for syn in cmpd.synonyms[:50]: # Check first 50 synonyms
            if cas_pattern.match(syn):
                info['cas_number'] = syn
                break
                
        return info
        
    except Exception as e:
        print(f"Error looking up compound: {e}")
        return None

# Functional Group Patterns (SMARTS)
FUNCTIONAL_GROUP_PATTERNS = {
    'Alcohol': '[OX2H]',
    'Aldehyde': '[CX3H1](=O)[#6]',
    'Ester': '[#6][CX3](=O)[OX2H0][#6]',
    'Ketone': '[#6][CX3](=O)[#6]',
    'Carboxylic Acid': '[CX3](=O)[OX2H1]',
    'Ether': '[OD2]([#6])[#6]',
    'Phenol': '[OX2H][c]',
    'Amine': '[NX3;H2,H1;!$(NC=O)]',
    'Amide': '[NX3][CX3](=O)[#6]',
    'Thiol': '[#16X2H]',
    'Alkene': '[CX3]=[CX3]',
    'Alkyne': '[CX2]#[CX2]',
    'Aromatic': 'a'
}

def get_functional_groups(mol):
    """Identify functional groups using SMARTs patterns"""
    if not mol: return []
    
    found_groups = set()
    for name, smarts in FUNCTIONAL_GROUP_PATTERNS.items():
        try:
            patt = Chem.MolFromSmarts(smarts)
            if mol.HasSubstructMatch(patt):
                found_groups.add(name)
        except:
            continue
            
    return list(found_groups)

def get_rdkit_properties(smiles):
    """
    Calculate properties using RDKit from a SMILES string.
    
    Args:
        smiles (str): The SMILES string.
        
    Returns:
        dict: Properties derived from RDKit.
    """
    if not Chem:
        return {"error": "RDKit is not installed."}
        
    try:
        mol = Chem.MolFromSmiles(smiles)
        if not mol:
            return {"error": "Invalid SMILES string."}
            
        # fingerprint = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=1024)
        # We don't store fingerprint in this simple dict, but we could return it if needed
        # For now, just confirming validity and basic props
        
        log_p = Crippen.MolLogP(mol)
        groups = get_functional_groups(mol)
        
        return {
            'molecular_weight': Descriptors.MolWt(mol),
            'molecular_formula': cancel_chem_formula(mol),
            'log_p': log_p,
            'functional_groups': ", ".join(groups),
            'valid': True
        }
    except Exception as e:
        return {"error": str(e)}

def cancel_chem_formula(mol):
    # RDKit doesn't have a direct 'GetFormula' in basic Descriptors usually,
    # often provided by rdMolDescriptors or calculating manually.
    # For now, rely on PubChem for formula if possible, or fallback.
    # Actually, Formula is usually better from PubChem.
    try:
        from rdkit.Chem.rdMolDescriptors import CalcMolFormula
        return CalcMolFormula(mol)
    except:
        return ""

def get_molecule_image(smiles):
    """
    Generate an image of the molecule.
    
    Args:
        smiles (str): SMILES string.
        
    Returns:
        bytes: PNG image bytes.
    """
    if not Chem:
        return None
        
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol:
            img = Draw.MolToImage(mol)
            import io
            bio = io.BytesIO()
            img.save(bio, format='PNG')
            return bio.getvalue()
    except:
        pass
    return None
