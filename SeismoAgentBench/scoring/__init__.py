"""Output artifact validation and scoring components."""

from .artifacts import ArtifactValidationError, validate_artifacts
from .catalog import CatalogValidationError, validate_catalog
from .contract import ScoreError, score_artifacts
from .reference import MatchingPolicy, ReferenceError, ReferenceSpec, match_events
from .scientific import ScientificScoreError, score_catalogs

__all__ = [
    "ArtifactValidationError", "CatalogValidationError", "ScoreError",
    "MatchingPolicy", "ReferenceError", "ReferenceSpec", "match_events",
    "ScientificScoreError", "score_catalogs",
    "score_artifacts", "validate_artifacts", "validate_catalog",
]
