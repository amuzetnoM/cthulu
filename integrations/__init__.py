"""
Integrations Module

External system integrations for Cthulu trading system.
Includes Vector Studio (Hecktor) for semantic trade memory.
"""

from .vector_studio import VectorStudioAdapter, VectorStudioConfig
from .embedder import TradeEmbedder
from .retriever import ContextRetriever, SimilarContext
from .data_layer import UnifiedDataLayer

__all__ = [
    "VectorStudioAdapter",
    "VectorStudioConfig",
    "TradeEmbedder",
    "ContextRetriever",
    "SimilarContext",
    "UnifiedDataLayer",
]
