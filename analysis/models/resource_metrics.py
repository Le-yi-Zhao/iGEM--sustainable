"""Batch resource accounting with explicit completeness and purity correction."""
from __future__ import annotations
import csv
import math
from pathlib import Path

MASS_TO_G={'g':1.,'mg':.001,'kg':1000.}
VOLUME_TO_L={'l':1.,'ml':.001,'ul':.000001}
POWER_TO_KW={'kw':1.,'w':.001}

def _read(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def number(value,positive=False):
    try:n=float(value)
    except (ValueError,TypeError):return None
    return n if math.isfinite(n) and (n>0 if positive else n>=0) else None
def yes(value):return str(value).strip().lower() in ('true','yes','1','是')
def key(r):return tuple(r.get(k,'') for k in ('experiment_id','group','replicate'))

def run(root:Path):
    output=root/'results/tables/resource_metrics.csv';output.parent.mkdir(parents=True,exist_ok=True)
    materials=_read(root/'data/wetlab/material_inventory_template.csv')
    equipment=_read(root/'data/wetlab/equipment_usage_template.csv')
    batches=_read(root/'data/wetlab/batch_summary_template.csv')
    fields=['experiment_id','group','replicate','pure_product_mass_g','pmi_g_per_g','water_l_per_g',
        'solvent_l_per_g','energy_kwh_per_g','energy_basis','evidence_type','status']
    results=[]
    for batch in batches:
        if not batch.get('experiment_id'):continue
        row=dict(zip(fields[:3],key(batch)));row.update({k:'' for k in fields[3:]})
        row.update(evidence_type=batch.get('source_type',''),status='MISSING_PURITY_OR_PRODUCT')
        mass=number(batch.get('isolated_product_mass_g'),True);purity=number(batch.get('purity_fraction'),True)
        if mass is None or purity is None or purity>1:
            results.append(row);continue
        product=mass*purity;row['pure_product_mass_g']=f'{product:.6g}'
        matched=[r for r in materials if key(r)==key(batch)]
        pmi_ok=volume_ok=yes(batch.get('material_inventory_complete')) and bool(matched)
        total=water=solvent=0.
        for r in matched:
            n=number(r.get('amount'));unit=r.get('unit','').lower().strip()
            density=number(r.get('density_g_per_ml'),True)
            if density is not None and not r.get('density_source','').strip():density=None
            category=r.get('material_type','').strip().lower()
            if category not in ('water','solvent','other'):volume_ok=False
            if n is None or unit not in {*MASS_TO_G,*VOLUME_TO_L}:
                pmi_ok=volume_ok=False;continue
            if unit in MASS_TO_G:
                grams=n*MASS_TO_G[unit];total+=grams
                liters=grams/density/1000 if density else None
            else:
                liters=n*VOLUME_TO_L[unit]
                if density:total+=liters*1000*density
                else:pmi_ok=False
            if category in ('water','solvent'):
                if liters is None:volume_ok=False
                elif category=='water':water+=liters
                else:solvent+=liters
        if pmi_ok:row['pmi_g_per_g']=f'{total/product:.6g}'
        if volume_ok:row.update(water_l_per_g=f'{water/product:.6g}',solvent_l_per_g=f'{solvent/product:.6g}')
        matched=[r for r in equipment if key(r)==key(batch)]
        energy_ok=yes(batch.get('equipment_inventory_complete')) and bool(matched)
        energy=0.;bases=set()
        for r in matched:
            power=number(r.get('power_value'));hours=number(r.get('use_time_h'));allocation=number(r.get('batch_samples'),True)
            unit=r.get('power_unit','').lower().strip();source=r.get('power_source','').strip()
            if None in (power,hours,allocation) or allocation<1 or unit not in POWER_TO_KW or not source:
                energy_ok=False;continue
            energy+=power*POWER_TO_KW[unit]*hours/allocation
            bases.add('MEASURED_POWER' if source.lower() in ('measured','meter','实测') else 'ESTIMATED_POWER')
        if energy_ok:
            row['energy_kwh_per_g']=f'{energy/product:.6g}'
            row['energy_basis']='MIXED' if len(bases)>1 else next(iter(bases))
        row['status']='COMPLETE' if pmi_ok and volume_ok and energy_ok else 'PARTIAL'
        results.append(row)
    with output.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(results)
    return output
