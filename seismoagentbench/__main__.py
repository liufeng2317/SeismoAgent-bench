"""Read-only source registry validation and inventory commands."""
import argparse
import json
from pathlib import Path

import yaml

from .sources import SourceError, inventory, load_case


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['validate-sources', 'inventory'])
    parser.add_argument('--case-dir', type=Path, required=True)
    parser.add_argument('--verify-files', action='store_true', help='Hash locally available source payloads')
    args = parser.parse_args()
    try:
        case = args.case_dir.resolve()
        cfg = load_case(case)
        report = inventory(cfg, case, verify=args.verify_files)
        result = report if args.command == 'inventory' else {
            'case_id': cfg['case_id'], 'source_contract_valid': True,
            'products': len(report['products']),
            'missing_local_products': [k for k,v in report['products'].items() if v['local_status'] == 'missing'],
            'mismatched_products': [k for k,v in report['products'].items() if v['integrity'] == 'mismatch'],
            'file_hashes_checked': args.verify_files,
        }
        failed = args.verify_files and any(v['local_status'] == 'missing' or v['integrity'] == 'mismatch' for v in report['products'].values())
    except (SourceError, OSError, yaml.YAMLError) as exc:
        parser.exit(2, f'Source configuration error: {exc}\n')
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if failed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
