"""Link immutable run provenance to regenerated caches, with content hashes."""
import hashlib
import json
from pathlib import Path

def run(root: Path):
    runs={}
    for name in ['admet_ai','chemprop','vega','episuite','protox','maplight','admetsar']:
        path=root/'data/raw'/name/('attribution_metadata.json' if name=='chemprop' else 'run_metadata.json')
        if path.exists():runs[name]={'metadata':str(path.relative_to(root)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    files=[]
    for folder in ['data/raw/vega','data/raw/episuite','data/raw/ecosar','data/raw/protox','data/raw/maplight','data/raw/chemprop','data/raw/admetsar']:
        for path in sorted((root/folder).rglob('*')):
            if path.is_file():files.append({'path':str(path.relative_to(root)),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    result={'host':'Matvision / autodl','runs':runs,'files':files,'evidence_type':'PREDICTED','cache_rebuild_performs_inference':False,'cross_platform_probabilities_averaged':False}
    output=root/'results/summaries/fresh_execution_manifest.json'
    output.write_text(json.dumps(result,indent=2)+'\n')
    return output
