"""
Atom Extractor - Pure Data Extraction

Focused on extracting raw data from sources (primarily Sabersim).
No analysis, no intelligence - just clean data extraction.

Architecture:
- sabersim/ - Sabersim API integration and extraction
- extractors/ - Core extraction engines
- extractor.py - Main extraction orchestrator

Analysis happens in atom_analyzer/
Intelligence happens in atom_generator/
Mapping happens in atom_mapper/
"""

from .extractor import MLBAtomExtractor

__version__ = "3.0.0"
__description__ = "Simplified data extraction platform"

def create_mlb_extractor():
    """Create MLB atom extractor instance."""
    return MLBAtomExtractor()

def get_extractor_info():
    """Get information about the atom extractor."""
    return {
        'version': __version__,
        'description': __description__,
        'architecture': 'Simplified extraction platform'
    }

__all__ = [
    'MLBAtomExtractor',
    'create_mlb_extractor',
    'get_extractor_info'
]
