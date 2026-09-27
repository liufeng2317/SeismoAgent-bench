"""Check output navigation and optional frozen dependencies; never run a solver."""
import argparse
import hashlib
import json
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--full', action='store_true',
                        help='Also check migrated links and frozen stage-52 sources.')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1] / 'export'
    manifest = json.loads((root / '_provenance/export_layout.json').read_text())
    mapping = manifest['stage_paths']
    errors = []
    for old, new in mapping.items():
        alias, target = root / old, root / new
        if not target.is_dir() or target.is_symlink():
            errors.append('Missing physical stage: ' + new)
        if not alias.is_symlink() or alias.resolve() != target.resolve():
            errors.append('Invalid compatibility alias: ' + old)
    for path in ['06_full_catalog/52_full_catalog/working_catalog.csv',
                 '06_full_catalog/52_full_catalog/events.csv',
                 '01_baseline/10_validate_catalog/events.csv', 'README.md']:
        if not (root / path).is_file():
            errors.append('Missing entry point: ' + path)
    print(f'Checked {len(mapping)} stage directories and compatibility aliases.', flush=True)
    if args.full:
        missing_before = 0
        for row in manifest['links_before']:
            stage, rest = row['path'].split('/', 1)
            link = root / mapping[stage] / rest
            old_target = Path(row['target'])
            if not old_target.is_absolute():
                old_target = (root / row['path']).parent / old_target
            if not link.is_symlink() or link.resolve() != old_target.resolve():
                errors.append('Changed link target: ' + row['path'])
            if row['existed_before'] and not link.exists():
                errors.append('New broken link: ' + row['path'])
            missing_before += not row['existed_before']
        print(f'Checked {len(manifest["links_before"])} migrated links; '
              f'{missing_before} targets were already missing before migration.', flush=True)
        for index, (name, expected) in enumerate(manifest['full_catalog_frozen_sources'].items(), 1):
            path = Path(name)
            if not path.is_file() or sha256(path) != expected:
                errors.append('Frozen source mismatch: ' + name)
            if index % 50 == 0:
                print(f'Checked {index} frozen sources.', flush=True)
        print(f'Checked {len(manifest["full_catalog_frozen_sources"])} frozen sources.', flush=True)
        product = root / '06_full_catalog/52_full_catalog'
        audit = json.loads((product / 'comparison_audit.json').read_text())
        for name, expected in audit['fit_sha256'].items():
            if sha256(product / name) != expected:
                errors.append('Changed fitted result: ' + name)
        print(f'Checked {len(audit["fit_sha256"])} fitted result hashes.', flush=True)
    if errors:
        raise SystemExit('\n'.join(errors))
    print('PASS: output layout and requested dependency checks.')


if __name__ == '__main__':
    main()
