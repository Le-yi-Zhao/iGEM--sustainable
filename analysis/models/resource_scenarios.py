"""Dimensionless, conditional resource analysis. No measured performance is implied."""
import csv
import json
import math
from pathlib import Path

def relative_intensity(resource_ratio, pure_product_ratio):
    if not all(math.isfinite(v) and v > 0 for v in (resource_ratio, pure_product_ratio)):
        raise ValueError('Ratios must be finite and positive')
    return resource_ratio / pure_product_ratio

def run(root: Path):
    rows = []
    for product in (0.8,1.0,1.1,1.2,1.5,2.0,3.0):
        for resource in (0.8,1.0,1.1,1.2,1.5,2.0):
            intensity = relative_intensity(resource,product)
            rows.append(dict(pure_product_ratio=product,resource_ratio=resource,
                relative_intensity=intensity,reduction_percent=100*(1-intensity),evidence_type='SCENARIO'))
    dest=root/'results/tables/resource_scenarios.csv'; dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    (root/'results/summaries/resource_scenarios.json').write_text(json.dumps({
        'evidence_type':'SCENARIO','functional_unit_zh':'1 g 经纯度校正的分离光甘草定',
        'boundary_zh':'匹配批次的培养、分离纯化及废物处理；上游原料和设备制造未纳入，不能称为完整生命周期评价。',
        'formula':'relative_intensity = resource_ratio / pure_product_ratio',
        'denominator_zh':'分离样品质量 × 光甘草定质量分数；已用该分离质量时不再乘回收率。',
        'actual_project_resource_intensity':None,
        'limitations_zh':'分别应用于水、溶剂、总投入质量、电耗或成本，不跨单位求总分；碳排放另需排放因子。',
        'grid_rows':len(rows)},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return rows
