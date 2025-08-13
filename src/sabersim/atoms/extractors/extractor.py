#!/usr/bin/env python3
"""
MLB Atom Extractor - Extract SaberSim data atoms from HAR files

Processes HAR files to extract MLB-specific endpoint data into organized atoms.
Creates proper atom structure with metadata, registries, and lineage tracking.

Supports multiple sites (DraftKings/FanDuel) and dynamic slate detection.
"""

import json
import os
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse, parse_qs
import re
import argparse
import shutil
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MLBAtomExtractor:
    """Extract MLB SaberSim data atoms from HAR files."""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories for atoms and metadata
        self.atoms_dir = self.output_dir / "atoms"
        self.metadata_dir = self.output_dir / "metadata"
        self.atoms_dir.mkdir(exist_ok=True)
        self.metadata_dir.mkdir(exist_ok=True)



        # Initialize registries
        self.atom_registry = {}
        self.endpoint_mapping = {
            'contest_simulations': [],
            'pool_lineup_selection': [],
            'player_projections': [],
            'build_optimization': [],
            'field_lineups': [],
            'contest_information': [],
            'portfolio_optimization': [],
            'progress_tracking': [],
            'lineup_data': []
        }

        # MLB endpoint patterns
        self.mlb_endpoints = {
            'contest_simulations': r'/initiate-user-contest-sim',
            'pool_lineup_selection': r'/select-pool-lineups-gen2',
            'player_projections': r'/get_player_projections',
            'build_optimization': r'/endpoints/lifesaber/build',
            'field_lineups': r'get-contest-lineups',
            'contest_information': r'/api/v1/contests/mlb',
            'portfolio_optimization': r'/solve-portfolio',
            'progress_tracking': r'/https-dripRequest',
            'lineup_data': r'/api/v1/lineups'
        }

        # Service domain mapping
        self.service_domains = {
            'sabersim_backend': ['field_lineups'],
            'baseball_sim': ['player_projections', 'build_optimization'],
            'cloud_run_service': ['contest_simulations', 'pool_lineup_selection'],
            'cloud_functions': ['portfolio_optimization', 'progress_tracking']
        }

    def extract_atoms_from_har(self, har_file_path: str) -> Dict[str, List[str]]:
        """Extract all MLB atoms from HAR file."""
        print(f"🔍 Extracting MLB atoms from: {har_file_path}")
        har_path = Path(har_file_path)
        if not har_path.exists():
            raise FileNotFoundError(f"HAR file not found: {har_file_path}")

        # Check if HAR file has been updated since last extraction
        har_mtime = har_path.stat().st_mtime
        extraction_summary_file = self.output_dir / "metadata" / "extraction_summary.json"

        if extraction_summary_file.exists():
            try:
                with open(extraction_summary_file, 'r') as f:
                    summary = json.load(f)
                last_har_mtime = summary.get('har_file_mtime', 0)

                if har_mtime <= last_har_mtime:
                    print(f"⚠️ HAR file hasn't changed since last extraction")
                    print(f"   Last extraction: {datetime.fromtimestamp(last_har_mtime)}")
                    print(f"   Current HAR: {datetime.fromtimestamp(har_mtime)}")
                    print(f"   Skipping extraction - no new data")
                    return self._load_existing_atoms()
                else:
                    print(f"🆕 HAR file updated - processing new data")
                    print(f"   Last extraction: {datetime.fromtimestamp(last_har_mtime)}")
                    print(f"   Current HAR: {datetime.fromtimestamp(har_mtime)}")
            except Exception as e:
                print(f"⚠️ Could not check extraction history: {e}")



        with open(har_path, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
        extracted_atoms = {endpoint_type: [] for endpoint_type in self.mlb_endpoints.keys()}
        entries = har_data.get('log', {}).get('entries', [])
        print(f"  📊 Processing {len(entries)} HAR entries...")
        print("  🔧 Processing ALL endpoints for fresh data")

        for entry in entries:
            request = entry.get('request', {})
            response = entry.get('response', {})
            url = request.get('url', '')
            status = response.get('status', 0)

            # Only process successful responses
            if status != 200:
                continue

            endpoint_type = self._identify_endpoint_type(url)
            if endpoint_type:
                started = entry.get('startedDateTime', '')
                print(f"  [DEBUG] Processing {endpoint_type} at {started}")
                atom_id = self._extract_single_atom(entry, endpoint_type, har_path.stem, archive_on_replace=True)
                if atom_id:
                    extracted_atoms[endpoint_type].append(atom_id)
                    self.endpoint_mapping[endpoint_type].append(atom_id)
                else:
                    print(f"  ❌ Failed to extract {endpoint_type} at {started}")

        self._save_registries(har_mtime)
        self._print_extraction_summary(extracted_atoms, har_path.stem, har_mtime)
        return extracted_atoms

    def _identify_endpoint_type(self, url: str) -> Optional[str]:
        """Identify which MLB endpoint type this URL represents."""

        for endpoint_type, pattern in self.mlb_endpoints.items():
            if re.search(pattern, url):
                return endpoint_type

        return None

    def _extract_single_atom(self, har_entry: Dict[str, Any], endpoint_type: str, har_filename: str, archive_on_replace: bool = False) -> Optional[str]:
        """Extract single atom from HAR entry."""

        try:
            request = har_entry.get('request', {})
            response = har_entry.get('response', {})
            url = request.get('url', '')

            # Extract response data
            response_content = response.get('content', {})
            response_text = response_content.get('text', '')

            if not response_text:
                return None

            # Parse response JSON
            try:
                response_data = json.loads(response_text)
            except json.JSONDecodeError:
                print(f"  ⚠️ Invalid JSON in {endpoint_type} response")
                return None

            # Extract metadata first to get request data
            metadata = self._extract_metadata(har_entry, endpoint_type, har_filename, url)
            if not metadata:
                print(f"  ⚠️ Could not extract metadata for {endpoint_type}")
                return None

            # Generate atom ID using request data for uniqueness
            request_data = metadata.get('request_data', {})
            atom_id = self._generate_atom_id(endpoint_type, url, response_text, request_data)

            # Create atom structure
            atom_data = {
                'endpoint_type': endpoint_type,
                'url': url,
                'response_data': response_data,
                'metadata': metadata
            }

            # Always replace existing atoms (no archiving)
            atom_file = self.atoms_dir / f"{atom_id}.json"
            if atom_file.exists():
                print(f"  🔄 Replacing existing atom: {atom_id}")

            # Save atom
            with open(atom_file, 'w') as f:
                json.dump(atom_data, f, indent=2)

            # Update registry
            self.atom_registry[atom_id] = {
                'endpoint_type': endpoint_type,
                'url': url,
                'timestamp': metadata['request_timestamp'],
                'har_source': har_filename,
                'file_path': str(atom_file),
                'data_keys': list(response_data.keys()) if isinstance(response_data, dict) else []
            }

            print(f"  ✅ Extracted {endpoint_type} atom: {atom_id}")
            return atom_id

        except Exception as e:
            print(f"  ❌ Error extracting atom from {endpoint_type}: {e}")
            import traceback
            print(f"  🔍 Traceback: {traceback.format_exc()}")
            return None

    def _generate_atom_id(self, endpoint_type: str, url: str, response_text: str, request_data: Optional[Dict[str, Any]] = None) -> str:
        """Generate clean atom ID using endpoint type and contest information."""

        # Start with endpoint type
        atom_id_parts = [endpoint_type]

        # Add contest-specific identifier if available
        if request_data:
            if endpoint_type == 'contest_simulations':
                # Use contest_build_id for simulations
                contest_build_id = request_data.get('contest_build_id', '')
                if contest_build_id:
                    atom_id_parts.append(contest_build_id)
            elif endpoint_type == 'field_lineups':
                # Use contest_bucket for field lineups
                contest_bucket = request_data.get('contest_bucket', '')
                if contest_bucket:
                    # Extract the meaningful contest type from the bucket name
                    # Contest buckets are in format: "uuid_flagship_mid_entry"
                    # We want to extract "flagship_mid_entry" part
                    if '_' in contest_bucket:
                        # Split by underscore and take everything after the first part (UUID)
                        parts = contest_bucket.split('_')
                        if len(parts) >= 3:
                            # Skip the UUID (first part) and join the rest
                            contest_type = '_'.join(parts[1:])
                            atom_id_parts.append(contest_type)
                        else:
                            atom_id_parts.append(contest_bucket)
                    else:
                        atom_id_parts.append(contest_bucket)
            elif endpoint_type == 'portfolio_optimization':
                # Add latest suffix for portfolio
                atom_id_parts.append('latest')

        # Create clean atom ID without hash suffix
        atom_id = '_'.join(atom_id_parts)

        return atom_id

    def _extract_metadata(self, har_entry: Dict[str, Any], endpoint_type: str, har_filename: str, url: str) -> Dict[str, Any]:
        """Extract metadata from HAR entry."""

        request = har_entry.get('request', {})
        response = har_entry.get('response', {})

        # Extract timing info
        timings = har_entry.get('timings', {})
        started_datetime = har_entry.get('startedDateTime', '')

        # Extract query parameters and proc_id if available
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        proc_id = query_params.get('proc_id', [None])[0]

        # Extract request data if POST
        request_data = {}
        if request.get('method') == 'POST':
            post_data = request.get('postData', {})
            if post_data.get('mimeType') == 'application/json':
                try:
                    request_data = json.loads(post_data.get('text', '{}'))
                except json.JSONDecodeError:
                    pass

        # Extract response timing
        response_time = timings.get('receive', 0)

        metadata = {
            'request_timestamp': started_datetime,
            'response_time_ms': response_time,
            'proc_id': proc_id,
            'request_data': request_data,
            'har_source': har_filename,
            'extraction_timestamp': datetime.now().isoformat()
        }

        return metadata

    def _save_registries(self, har_mtime: float):
        """Save atom registry and endpoint mapping."""

        # Save atom registry
        registry_file = self.metadata_dir / "atom_registry.json"
        with open(registry_file, 'w') as f:
            json.dump(self.atom_registry, f, indent=2)

        # Save endpoint mapping
        mapping_file = self.metadata_dir / "endpoint_mapping.json"
        with open(mapping_file, 'w') as f:
            json.dump(self.endpoint_mapping, f, indent=2)

        # Save extraction summary
        summary_file = self.metadata_dir / "extraction_summary.json"
        summary = {
            'extraction_timestamp': datetime.now().isoformat(),
            'har_file_mtime': har_mtime,
            'total_atoms': sum(len(atoms) for atoms in self.endpoint_mapping.values()),
            'atoms_by_endpoint': {k: len(v) for k, v in self.endpoint_mapping.items()},
            'har_source': 'unknown'
        }
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

    def _load_existing_atoms(self) -> Dict[str, List[str]]:
        """Load existing atoms from registry."""
        registry_file = self.metadata_dir / "atom_registry.json"
        if registry_file.exists():
            with open(registry_file, 'r') as f:
                self.atom_registry = json.load(f)

            # Reconstruct endpoint mapping from registry
            for atom_id, atom_info in self.atom_registry.items():
                endpoint_type = atom_info.get('endpoint_type')
                if endpoint_type in self.endpoint_mapping:
                    self.endpoint_mapping[endpoint_type].append(atom_id)

        return self.endpoint_mapping

    def _print_extraction_summary(self, extracted_atoms: Dict[str, List[str]], har_filename: str, har_mtime: float):
        """Print summary of extraction results."""

        print(f"\n📊 Extraction Summary for {har_filename}")
        print("=" * 50)

        total_atoms = sum(len(atoms) for atoms in extracted_atoms.values())
        print(f"Total atoms extracted: {total_atoms}")
        print(f"HAR file timestamp: {datetime.fromtimestamp(har_mtime)}")
        print(f"Output directory: {self.output_dir}")

        print(f"\nAtoms by endpoint type:")
        for endpoint_type, atoms in extracted_atoms.items():
            if atoms:
                print(f"  {endpoint_type}: {len(atoms)} atoms")
                for atom_id in atoms[:3]:  # Show first 3
                    print(f"    - {atom_id}")
                if len(atoms) > 3:
                    print(f"    ... and {len(atoms) - 3} more")

        print(f"\n📁 Files created:")
        print(f"  Atoms: {self.atoms_dir}")
        print(f"  Metadata: {self.metadata_dir}")


def main():
    """Command line interface for MLB Atom Extractor."""
    parser = argparse.ArgumentParser(description='Extract MLB atoms from SaberSim HAR file')
    parser.add_argument('har_file', help='Path to HAR file')
    parser.add_argument('--output', '-o', default='./atoms_output', help='Output directory')

    args = parser.parse_args()

    extractor = MLBAtomExtractor(args.output)
    atoms = extractor.extract_atoms_from_har(args.har_file)

    print(f"\n✅ Extraction completed!")
    print(f"📁 Output saved to: {args.output}")


if __name__ == '__main__':
    main()
