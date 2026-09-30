import csv
import tempfile
import unittest
from pathlib import Path
from analysis.models.resource_metrics import run

class ResourceAccountingTests(unittest.TestCase):
    def calculate(self,batch,materials,equipment):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'data/wetlab').mkdir(parents=True)
            for name,rows in [('batch_summary',batch),('material_inventory',materials),('equipment_usage',equipment)]:
                with (root/f'data/wetlab/{name}_template.csv').open('w',newline='') as f:
                    w=csv.DictWriter(f,fieldnames=sorted(set().union(*(r.keys() for r in rows))) if rows else ['experiment_id','group','replicate'])
                    w.writeheader();w.writerows(rows)
            with run(root).open() as f:return list(csv.DictReader(f))[0]
    def test_purity_and_liquid_mass_are_included(self):
        k={'experiment_id':'test','group':'A','replicate':'1'}
        batch=[dict(k,isolated_product_mass_g='2',purity_fraction='.5',material_inventory_complete='true',equipment_inventory_complete='true')]
        materials=[dict(k,material='water',material_type='water',amount='100',unit='ml',density_g_per_ml='1',density_source='test density'),dict(k,material='solid',material_type='other',amount='10',unit='g')]
        equipment=[dict(k,power_value='100',power_unit='W',power_source='nameplate',use_time_h='2',batch_samples='1')]
        result=self.calculate(batch,materials,equipment)
        self.assertEqual(result['status'],'COMPLETE')
        self.assertEqual(float(result['pure_product_mass_g']),1)
        self.assertEqual(float(result['pmi_g_per_g']),110)
        self.assertEqual(float(result['energy_kwh_per_g']),.2)
        self.assertEqual(result['energy_basis'],'ESTIMATED_POWER')
        materials[0].pop('density_source')
        result=self.calculate(batch,materials,equipment)
        self.assertEqual(result['pmi_g_per_g'],'')
        self.assertEqual(result['status'],'PARTIAL')
    def test_missing_inventory_is_not_zero(self):
        batch=[{'experiment_id':'test','group':'A','replicate':'1','isolated_product_mass_g':'2','purity_fraction':'1'}]
        result=self.calculate(batch,[],[])
        for field in ('pmi_g_per_g','water_l_per_g','solvent_l_per_g','energy_kwh_per_g'):self.assertEqual(result[field],'')
        batch[0].pop('purity_fraction')
        self.assertEqual(self.calculate(batch,[],[])['status'],'MISSING_PURITY_OR_PRODUCT')
