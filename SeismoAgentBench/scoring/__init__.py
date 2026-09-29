"""Output artifact validation and scoring components."""

from .artifacts import ArtifactValidationError, validate_artifacts
from .catalog import CatalogValidationError, validate_catalog
from .contract import ScoreError, score_artifacts
from .aggregate import AggregationError, aggregate_catalog_score
from .reference import MatchingPolicy, ReferenceError, ReferenceSpec, match_events
from .scientific import ScientificScoreError, score_catalogs
from .picks import PickScoreError, load_picks, score_picks
from .registry import (ScorerContext, ScorerDefinition, ScorerRegistry,
                       ScorerRegistryError, ScorerUnavailable, default_scorer_registry)

__all__ = [
    "AggregationError", "ArtifactValidationError", "CatalogValidationError", "ScoreError",
    "MatchingPolicy", "ReferenceError", "ReferenceSpec", "match_events",
    "ScientificScoreError", "score_catalogs",
    "aggregate_catalog_score", "score_artifacts", "validate_artifacts", "validate_catalog",
    "PickScoreError", "load_picks", "score_picks",
    "ScorerContext", "ScorerDefinition", "ScorerRegistry", "ScorerRegistryError",
    "ScorerUnavailable",
    "default_scorer_registry",
]
