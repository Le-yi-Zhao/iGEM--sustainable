import subprocess
import sys
import unittest
from pathlib import Path

class CacheOnlyTests(unittest.TestCase):
    def test_cached_rebuild_does_not_import_inference_dependencies(self):
        code = """
import importlib.abc
import sys
class BlockInference(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'admet_ai', 'torch', 'lightning', 'chemprop'}:
            raise AssertionError('Unexpected inference import: ' + fullname)
sys.meta_path.insert(0, BlockInference())
from analysis.adapters import admet_ai_local
assert admet_ai_local.run(force=False).is_file()
from analysis.plotting.model_result_figures import DEFAULT_DRUGBANK_PATH
assert DEFAULT_DRUGBANK_PATH.is_file()
"""
        result = subprocess.run([sys.executable, '-c', code], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
