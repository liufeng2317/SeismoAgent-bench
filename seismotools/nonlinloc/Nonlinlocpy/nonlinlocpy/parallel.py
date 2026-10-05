from __future__ import annotations

import concurrent.futures
import csv
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Sequence, TypeVar

from .hyp import parse_hyp_solutions
from .observations import write_nlloc_obs_file
from .runner import run_nlloc_bin
from .utils import cleanup_production_outputs, write_solution_csv

T = TypeVar("T")


@dataclass
class ChunkRunResult:
    """Summary of one chunk-level NLLoc execution.
    
    Attributes:
        chunk_run_dir (str): chunk run dir.
        n_solutions (int): n solutions.
        first_solution (Dict[str, object]): first solution.
    """

    chunk_run_dir: str
    n_solutions: int
    first_solution: Dict[str, object]


@dataclass
class ParallelNLLocConfig:
    """Configuration for chunked parallel NLLoc execution.
    
    Attributes:
        base_run_dir (str): base run dir.
        nlloc_bin_dir (str): nlloc bin dir.
        chunk_size (int): chunk size.
        num_workers (int): num workers.
        output_mode (str): output mode.
        chunk_root_dir (str): chunk root dir.
        merged_output_path (str): merged output path.
        static_dirs (Sequence[str]): static dirs.
        static_files (Sequence[str]): static files.
    """

    base_run_dir: str
    nlloc_bin_dir: str
    chunk_size: int
    num_workers: int = 1
    output_mode: str = "production"
    chunk_root_dir: str = ""
    merged_output_path: str = ""
    static_dirs: Sequence[str] = field(default_factory=lambda: ("model", "time"))
    static_files: Sequence[str] = field(
        default_factory=lambda: ("nlloc.in", "Zone_info.pickle", "Part_of_ControlFile.pickle")
    )


@dataclass
class ParallelNLLocResult:
    """Merged result summary returned by the high-level parallel workflow.
    
    Attributes:
        chunk_run_dirs (List[str]): chunk run dirs.
        chunk_results (List[ChunkRunResult]): chunk results.
        merged_output_path (str): merged output path.
        n_chunks (int): n chunks.
        n_solutions (int): n solutions.
    """

    chunk_run_dirs: List[str]
    chunk_results: List[ChunkRunResult]
    merged_output_path: str
    n_chunks: int
    n_solutions: int


def chunk_sequence(items: Sequence[T], chunk_size: int) -> List[List[T]]:
    """Split an input sequence into fixed-size chunk lists.
    
    Args:
        items (Sequence[T]): items.
        chunk_size (int): chunk size.
    
    Returns:
        List[List[T]]: Result returned by the function.
    """

    if chunk_size <= 0 or len(items) <= chunk_size:
        return [list(items)]
    return [list(items[i : i + chunk_size]) for i in range(0, len(items), chunk_size)]


def safe_link_or_copy(src: Path, dst: Path) -> None:
    """Prefer a symlink for shared static assets, falling back to copying if needed.
    
    Args:
        src (Path): src.
        dst (Path): dst.
    """

    try:
        if dst.exists() or dst.is_symlink():
            if dst.is_dir() and not dst.is_symlink():
                shutil.rmtree(dst)
            else:
                dst.unlink()
        dst.symlink_to(src.resolve(strict=True), target_is_directory=src.is_dir())
    except OSError:
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)


def copy_static_assets(
    base_run_dir: Path,
    chunk_run_dir: Path,
    *,
    static_dirs: Sequence[str] = ("model", "time"),
    static_files: Sequence[str] = ("nlloc.in", "Zone_info.pickle", "Part_of_ControlFile.pickle"),
) -> None:
    """Populate a chunk run directory with reusable static model and control assets.
    
    Args:
        base_run_dir (Path): base run dir.
        chunk_run_dir (Path): chunk run dir.
        static_dirs (Sequence[str]): static dirs.
        static_files (Sequence[str]): static files.
    """

    for subdir in static_dirs:
        safe_link_or_copy(base_run_dir / subdir, chunk_run_dir / subdir)
    for name in static_files:
        src = base_run_dir / name
        if src.exists():
            shutil.copy2(src, chunk_run_dir / name)


def make_standard_chunk_preparer(
    *,
    base_run_dir: Path,
    static_dirs: Sequence[str],
    static_files: Sequence[str],
    prepare_chunk_inputs: Callable[[Path, Sequence[T]], None],
) -> Callable[[Path, Sequence[T]], None]:
    """Build a reusable chunk-directory preparer around caller-provided input writing.
    
    Args:
        base_run_dir (Path): base run dir.
        static_dirs (Sequence[str]): static dirs.
        static_files (Sequence[str]): static files.
        prepare_chunk_inputs (Callable[[Path, Sequence[T]], None]): prepare chunk inputs.
    
    Returns:
        Callable[[Path, Sequence[T]], None]: Result returned by the function.
    """

    def _prepare(chunk_run_dir: Path, chunk_items: Sequence[T]) -> None:
        """Create and populate one chunk run directory.

        Args:
            chunk_run_dir (Path): Chunk-specific run directory.
            chunk_items (Sequence[T]): Items assigned to this chunk.
        """
        from .utils import build_run_directory

        build_run_directory(chunk_run_dir)
        copy_static_assets(
            base_run_dir,
            chunk_run_dir,
            static_dirs=static_dirs,
            static_files=static_files,
        )
        prepare_chunk_inputs(chunk_run_dir, chunk_items)

    return _prepare


def run_nlloc_chunk(
    chunk_run_dir: str,
    nlloc_bin_dir: str,
    output_mode: str,
) -> ChunkRunResult:
    """Run ``NLLoc`` for one prepared chunk directory and write its compact CSV.
    
    Args:
        chunk_run_dir (str): chunk run dir.
        nlloc_bin_dir (str): nlloc bin dir.
        output_mode (str): output mode.
    
    Returns:
        ChunkRunResult: Result returned by the function.
    """

    run_dir = Path(chunk_run_dir)
    run_nlloc_bin(nlloc_bin_dir, str(run_dir))
    solutions = parse_hyp_solutions(str(run_dir))
    write_solution_csv(run_dir / "located_events.csv", solutions)
    if output_mode == "production" and solutions:
        cleanup_production_outputs(run_dir)
    return ChunkRunResult(
        chunk_run_dir=str(run_dir),
        n_solutions=len(solutions),
        first_solution=solutions[0] if solutions else {},
    )


def read_solution_csv(path: Path) -> List[Dict[str, object]]:
    """Read a compact solution CSV into a list of dictionaries.
    
    Args:
        path (Path): path.
    
    Returns:
        List[Dict[str, object]]: Result returned by the function.
    """

    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return [dict(row) for row in rows]


def merge_solution_csvs(chunk_run_dirs: Sequence[Path], output_path: Path) -> List[Dict[str, object]]:
    """Merge per-chunk compact CSV files into one package-standard output table.
    
    Args:
        chunk_run_dirs (Sequence[Path]): chunk run dirs.
        output_path (Path): output path.
    
    Returns:
        List[Dict[str, object]]: Result returned by the function.
    """

    merged: List[Dict[str, object]] = []
    for chunk_run_dir in chunk_run_dirs:
        merged.extend(read_solution_csv(chunk_run_dir / "located_events.csv"))
    write_solution_csv(output_path, merged)
    return merged


def prepare_chunk_run_dirs(
    base_run_dir: Path,
    chunk_items: Sequence[Sequence[T]],
    chunk_root_dir: Path,
    prepare_chunk_dir: Callable[[Path, Sequence[T]], None],
) -> List[Path]:
    """Create all chunk run directories and let the caller populate each chunk's inputs.
    
    Args:
        base_run_dir (Path): base run dir.
        chunk_items (Sequence[Sequence[T]]): chunk items.
        chunk_root_dir (Path): chunk root dir.
        prepare_chunk_dir (Callable[[Path, Sequence[T]], None]): prepare chunk dir.
    
    Returns:
        List[Path]: Result returned by the function.
    """

    if chunk_root_dir.exists():
        shutil.rmtree(chunk_root_dir)
    chunk_root_dir.mkdir(parents=True, exist_ok=True)

    chunk_run_dirs: List[Path] = []
    for index, chunk_item_group in enumerate(chunk_items):
        chunk_run_dir = chunk_root_dir / f"chunk_{index:04d}"
        prepare_chunk_dir(chunk_run_dir, chunk_item_group)
        chunk_run_dirs.append(chunk_run_dir)
    return chunk_run_dirs


def run_parallel_chunks(
    *,
    chunk_run_dirs: Sequence[Path],
    nlloc_bin_dir: str,
    output_mode: str,
    num_workers: int,
    merged_output_path: Path,
) -> List[Dict[str, object]]:
    """Execute prepared chunk directories in parallel and merge their compact outputs.
    
    Args:
        chunk_run_dirs (Sequence[Path]): chunk run dirs.
        nlloc_bin_dir (str): nlloc bin dir.
        output_mode (str): output mode.
        num_workers (int): num workers.
        merged_output_path (Path): merged output path.
    
    Returns:
        List[Dict[str, object]]: Result returned by the function.
    """

    worker_count = max(1, min(int(num_workers), len(chunk_run_dirs)))
    if worker_count == 1:
        results = [run_nlloc_chunk(str(chunk_dir), nlloc_bin_dir, output_mode) for chunk_dir in chunk_run_dirs]
    else:
        results = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=worker_count) as executor:
            future_map = {
                executor.submit(run_nlloc_chunk, str(chunk_dir), nlloc_bin_dir, output_mode): chunk_dir
                for chunk_dir in chunk_run_dirs
            }
            for future in concurrent.futures.as_completed(future_map):
                results.append(future.result())

    merged_solutions = merge_solution_csvs(chunk_run_dirs, merged_output_path)
    return merged_solutions


def run_parallel_nlloc_workflow(
    *,
    items: Sequence[T],
    config: ParallelNLLocConfig,
    prepare_chunk_inputs: Callable[[Path, Sequence[T]], None],
    on_chunk_completed: Callable[[ChunkRunResult], None] | None = None,
) -> ParallelNLLocResult:
    """High-level reusable workflow for chunking, running, and merging NLLoc jobs.
    
    Args:
        items (Sequence[T]): items.
        config (ParallelNLLocConfig): config.
        prepare_chunk_inputs (Callable[[Path, Sequence[T]], None]): prepare chunk inputs.
        on_chunk_completed (Callable[[ChunkRunResult], None] | None): on chunk completed.
    
    Returns:
        ParallelNLLocResult: Result returned by the function.
    """

    base_run_dir = Path(config.base_run_dir)
    chunk_root_dir = Path(config.chunk_root_dir) if config.chunk_root_dir else base_run_dir / "chunks"
    merged_output_path = Path(config.merged_output_path) if config.merged_output_path else base_run_dir / "located_events.csv"

    chunk_items = chunk_sequence(items, config.chunk_size)
    prepare_chunk_dir = make_standard_chunk_preparer(
        base_run_dir=base_run_dir,
        static_dirs=config.static_dirs,
        static_files=config.static_files,
        prepare_chunk_inputs=prepare_chunk_inputs,
    )
    chunk_run_dirs = prepare_chunk_run_dirs(
        base_run_dir,
        chunk_items,
        chunk_root_dir,
        prepare_chunk_dir,
    )

    worker_count = max(1, min(int(config.num_workers), len(chunk_run_dirs)))
    chunk_results: List[ChunkRunResult] = []
    if worker_count == 1:
        for chunk_dir in chunk_run_dirs:
            result = run_nlloc_chunk(str(chunk_dir), config.nlloc_bin_dir, config.output_mode)
            chunk_results.append(result)
            if on_chunk_completed is not None:
                on_chunk_completed(result)
    else:
        with concurrent.futures.ProcessPoolExecutor(max_workers=worker_count) as executor:
            future_map = {
                executor.submit(run_nlloc_chunk, str(chunk_dir), config.nlloc_bin_dir, config.output_mode): chunk_dir
                for chunk_dir in chunk_run_dirs
            }
            for future in concurrent.futures.as_completed(future_map):
                result = future.result()
                chunk_results.append(result)
                if on_chunk_completed is not None:
                    on_chunk_completed(result)

    merged_solutions = merge_solution_csvs(chunk_run_dirs, merged_output_path)
    return ParallelNLLocResult(
        chunk_run_dirs=[str(path) for path in chunk_run_dirs],
        chunk_results=chunk_results,
        merged_output_path=str(merged_output_path),
        n_chunks=len(chunk_run_dirs),
        n_solutions=len(merged_solutions),
    )


def write_chunk_obs_file(chunk_run_dir: Path, obs_lines: Sequence[str], obs_basename: str = "All.obs") -> Path:
    """Write one chunk's observation file using the package-standard ``obs/`` layout.
    
    Args:
        chunk_run_dir (Path): chunk run dir.
        obs_lines (Sequence[str]): obs lines.
        obs_basename (str): obs basename.
    
    Returns:
        Path: Result returned by the function.
    """

    obs_path = write_nlloc_obs_file(str(chunk_run_dir), obs_lines, obs_basename=obs_basename, mode="w")
    return Path(obs_path)
