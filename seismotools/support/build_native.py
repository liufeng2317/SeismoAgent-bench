#!/usr/bin/env python3
"""Build copied native sources in local build trees; never mutate source/."""
import argparse
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ['nonlinloc', 'hypodd', 'match_and_locate']
# MatchLocate2 is plain C + OpenMP. -ffp-contract=off keeps floating-point
# results independent of FMA availability (aarch64 contracts by default).
MATCHLOCATE_CFLAGS = ['-O2', '-std=gnu99', '-fopenmp', '-ffp-contract=off', '-w']
MATCHLOCATE_PROGRAMS = {
    'MatchLocate2': ['MatchLocate2.c', 'sacio.c'],
    'SelectFinal': ['SelectFinal.c'],
    'SHIFT': ['SHIFT.c'],
    'lsac': ['lsac.c', 'sacio.c'],
}


def build_match_and_locate(folder, log):
    """Patch a pristine copy of the upstream src/ and compile it.

    ccsacc (a plotting helper) links SAC's libsac and is not built.
    """
    build = folder / 'runtime' / 'build'
    if build.exists():
        shutil.rmtree(build)
    shutil.copytree(folder / 'source' / 'upstream' / 'src', build / 'src')
    for patch in sorted((folder / 'source' / 'patches').glob('*.patch')):
        log.write(f'== patch {patch.name}\n')
        log.flush()
        subprocess.run(['patch', '-p1', '--no-backup-if-mismatch', '-i', str(patch)], cwd=build,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    binary_dir = folder / 'runtime' / 'bin'
    binary_dir.mkdir(parents=True, exist_ok=True)
    for program, sources in MATCHLOCATE_PROGRAMS.items():
        command = ['gcc', *MATCHLOCATE_CFLAGS, '-o', program, *sources, '-lm']
        log.write('== ' + ' '.join(command) + '\n')
        log.flush()
        subprocess.run(command, cwd=build / 'src', stdout=log, stderr=subprocess.STDOUT, check=True)
        shutil.copy2(build / 'src' / program, binary_dir / program)
    return list(MATCHLOCATE_PROGRAMS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool', choices=['all', *TOOLS], default='all')
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error('--jobs must be positive')
    for name in (TOOLS if args.tool == 'all' else [args.tool]):
        folder = ROOT / name
        if name == 'match_and_locate':
            log = folder / 'runtime' / 'build.log'
            log.parent.mkdir(exist_ok=True)
            print(f'Building {name}; log: {log}', flush=True)
            with log.open('w') as stream:
                binaries = build_match_and_locate(folder, stream)
            print(f'{name}: {", ".join(binaries)} built', flush=True)
            continue
        # Both native tools use the standardized source/runtime layout.
        if name == 'nonlinloc':
            source = folder / 'source'
            build = folder / 'runtime' / 'build'
            binary_dir = folder / 'runtime' / 'bin'
        else:
            source = folder / 'source'
            build = folder / 'runtime' / 'build'
            binary_dir = folder / 'runtime' / 'bin'
        shutil.copytree(source, build, dirs_exist_ok=True)
        binary_dir.mkdir(exist_ok=True)
        log = folder / 'runtime' / 'build.log'
        log.parent.mkdir(exist_ok=True)
        if name == 'nonlinloc':
            cwd = build / 'src'
            binaries = ['NLLoc', 'Vel2Grid', 'Grid2Time']
            builds = [(cwd, ['make', '-R', f'-j{args.jobs}', 'MYBIN=.', *binaries])]
        else:
            binaries = ['hypoDD', 'ph2dt']
            builds = [
                (build / 'src' / binary, ['make', f'-j{args.jobs}', 'FC=gfortran',
                 'FFLAGS=-O2 -I../../include -std=legacy -fallow-argument-mismatch'])
                for binary in binaries
            ]
        print(f'Building {name}; log: {log}', flush=True)
        with log.open('w') as stream:
            for cwd, command in builds:
                if name == 'hypodd':
                    subprocess.run(['make', 'clean'], cwd=cwd, stdout=stream,
                                   stderr=subprocess.STDOUT, check=True)
                subprocess.run(command, cwd=cwd, stdout=stream,
                               stderr=subprocess.STDOUT, check=True)
        for cwd, _ in builds:
            binary = cwd.name if name == 'hypodd' else None
            if binary:
                shutil.copy2(cwd / binary, binary_dir / binary)
        if name == 'nonlinloc':
            for binary in binaries:
                shutil.copy2(cwd / binary, binary_dir / binary)
        print(f'{name}: {", ".join(binaries)} built', flush=True)


if __name__ == '__main__':
    main()
