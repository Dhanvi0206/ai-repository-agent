"""Collaboration layer for multi-agent result fusion and conflict handling."""

from backend.collaboration.collaboration_engine import CollaborationEngine
from backend.collaboration.confidence_fusion import fuse_confidence
from backend.collaboration.conflict_resolver import ConflictResolver
from backend.collaboration.result_aggregator import ResultAggregator
from backend.collaboration.risk_scoring import score_risk_level

__all__ = [
    "CollaborationEngine",
    "ConflictResolver",
    "ResultAggregator",
    "fuse_confidence",
    "score_risk_level",
]
