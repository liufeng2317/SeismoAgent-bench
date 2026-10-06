#!/usr/bin/env python3
"""Verify snapshots; optionally import local code and load weights offline on CPU."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--imports', action='store_true')
    args = parser.parse_args()
    registry = json.loads((ROOT / 'support' / 'registry.json').read_text())
    errors = []
    for record in registry['files']:
        path = ROOT / record['path']
        if not path.is_file():
            errors.append(f'missing: {record["path"]}')
        elif path.stat().st_size != record['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
            errors.append(f'changed: {record["path"]}')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'Integrity: {len(registry["files"])} copied files verified', flush=True)
    if not args.imports:
        return
    os.environ['SEISBENCH_CACHE_ROOT'] = str(ROOT / 'phase_picking/cache')
    sys.path.insert(0, str(ROOT / 'phase_picking/source'))
    sys.path.insert(0, str(ROOT / 'gamma/source'))
    import torch
    import gamma.utils
    from phase_picking.model.phasenet import PhaseNet
    from phase_picking.model.eqtransformer import EQTransformer
    from phase_picking.model.dpppickerp import DPPPicker
    assert Path(gamma.utils.__file__).is_relative_to(ROOT / 'gamma/source')
    torch.set_num_threads(1)
    for cls, folder, weight, metadata in [
        (PhaseNet, 'phasenet', 'original.pt.v2', 'original.json.v2'),
        (EQTransformer, 'eqtransformer', 'original_nonconservative.pt.v1', 'original_nonconservative.json.v1'),
        (DPPPicker, 'dpppickerp', 'scedc.pt', 'scedc.json'),
    ]:
        import inspect
        assert Path(inspect.getfile(cls)).is_relative_to(ROOT / 'phase_picking/source')
        base = ROOT / 'phase_picking/runtime/weights' / folder
        meta = json.loads((base / metadata).read_text())
        model = cls(mode='P') if cls is DPPPicker else cls(**meta['model_args'])
        state = torch.load(base / weight, map_location='cpu', weights_only=True)
        model.load_state_dict(state.get('state_dict', state), strict=True)
        model.eval()
        print(f'{cls.__name__}: local import and strict CPU weight load passed', flush=True)
    print('GaMMA: local import passed; no inference, association or relocation executed')


if __name__ == '__main__':
    main()
