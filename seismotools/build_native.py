#!/usr/bin/env python3
"""Build copied native sources in local build trees; never mutate source/."""
import argparse
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool', choices=['all', 'nonlinloc', 'hypodd'], default='all')
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    for name in (['nonlinloc', 'hypodd'] if args.tool == 'all' else [args.tool]):
        folder = ROOT / name
        build = folder / 'build'
        shutil.copytree(folder / 'source', build, dirs_exist_ok=True)
        (folder / 'bin').mkdir(exist_ok=True)
        (folder / 'logs').mkdir(exist_ok=True)
        log = folder / 'logs/build.log'
        if name == 'nonlinloc':
            cwd = build / 'src'
            binaries = ['NLLoc', 'Vel2Grid', 'Grid2Time']
            command = ['make', '-R', f'-j{args.jobs}', 'MYBIN=.', *binaries]
        else:
            cwd = build / 'src/hypoDD'
            binaries = ['hypoDD']
            command = ['make', f'-j{args.jobs}', 'FC=gfortran',
                       'FFLAGS=-O2 -I../../include -std=legacy -fallow-argument-mismatch']
        print(f'Building {name}; log: {log}', flush=True)
        with log.open('w') as stream:
            if name == 'hypodd':
                subprocess.run(['make', 'clean'], cwd=cwd, stdout=stream,
                               stderr=subprocess.STDOUT, check=True)
            subprocess.run(command, cwd=cwd, stdout=stream,
                           stderr=subprocess.STDOUT, check=True)
        for binary in binaries:
            shutil.copy2(cwd / binary, folder / 'bin' / binary)
        print(f'{name}: {", ".join(binaries)} built', flush=True)


if __name__ == '__main__':
    main()
