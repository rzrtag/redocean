#!/usr/bin/env python3
from __future__ import annotations

"""
Flat tables API

Re-exports key entry points from subpackages to simplify imports.
"""

# Summary
from sabersim.tables.summary.compute_contest_summary import (
    build_summary as build_contest_summary,
    write_summary as write_contest_summary,
)

# Analysis
from sabersim.tables.analysis.generate_analysis import (
    write_analysis,
    generate_lineup_stats,
    generate_stack_analysis,
)

__all__ = [
    'build_contest_summary',
    'write_contest_summary',
    'write_analysis',
    'generate_lineup_stats',
    'generate_stack_analysis',
]
