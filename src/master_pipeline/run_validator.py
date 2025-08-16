#!/usr/bin/env python3
"""
Master Pipeline Runner with Data Validation

Runs the complete pipeline including:
1. SaberSim data extraction
2. MLB data collection (Statcast + Rolling Windows)
3. Win Calc adjustments with enhanced rolling adjuster
4. Data validation at key points
5. Comprehensive reporting

Outputs validation reports to: /mnt/storage_fast/workspaces/red_ocean/_data/reports/validator
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Pipeline components
SABERSIM_PIPELINE = "src/master_pipeline/run_ss.py"
MLB_PIPELINE = "src/master_pipeline/run_mlb_fg.py"
WIN_CALC_PIPELINE = "src/win_calc/pipeline/run_win_calc.py"

# Validation components
VALIDATION_TOOL = "src/win_calc/validate_data.py"

# Output directories
VALIDATOR_OUTPUT_ROOT = "/mnt/storage_fast/workspaces/red_ocean/_data/reports/validator"
SABERSIM_DATA_ROOT = "/mnt/storage_fast/workspaces/red_ocean/_data/sabersim_2025"
MLB_DATA_ROOT = "/mnt/storage_fast/workspaces/red_ocean/_data/mlb_api_2025"


class MasterPipelineRunner:
    """Master pipeline runner with integrated validation."""

    def __init__(self, validate_only: bool = False, skip_validation: bool = False):
        self.validate_only = validate_only
        self.skip_validation = skip_validation
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.report_dir = Path(VALIDATOR_OUTPUT_ROOT) / self.timestamp
        self.report_dir.mkdir(parents=True, exist_ok=True)

        # Pipeline results
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "pipeline_version": "1.0",
            "steps": [],
            "validation_reports": [],
            "summary": {
                "total_steps": 0,
                "successful_steps": 0,
                "failed_steps": 0,
                "validation_errors": 0,
                "validation_warnings": 0
            }
        }

    def log_step(self, step_name: str, success: bool, message: str = "", duration: float = 0):
        """Log a pipeline step result."""
        step_result = {
            "step": step_name,
            "success": success,
            "message": message,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
        self.results["steps"].append(step_result)
        self.results["summary"]["total_steps"] += 1

        if success:
            self.results["summary"]["successful_steps"] += 1
        else:
            self.results["summary"]["failed_steps"] += 1

        status = "✅" if success else "❌"
        print(f"{status} {step_name}: {message}")

    def run_command(self, command: str, step_name: str) -> bool:
        """Run a command and log the result."""
        print(f"\n🚀 Running: {step_name}")
        print(f"   Command: {command}")

        start_time = time.time()

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd="/mnt/storage_fast/workspaces/red_ocean"
            )

            duration = time.time() - start_time

            if result.returncode == 0:
                self.log_step(step_name, True, "Completed successfully", duration)
                if result.stdout:
                    print(f"   Output: {result.stdout[:500]}...")
                return True
            else:
                self.log_step(step_name, False, f"Failed with return code {result.returncode}", duration)
                if result.stderr:
                    print(f"   Error: {result.stderr}")
                return False

        except Exception as e:
            duration = time.time() - start_time
            self.log_step(step_name, False, f"Exception: {str(e)}", duration)
            return False

    def run_sabersim_pipeline(self) -> bool:
        """Run SaberSim data extraction pipeline."""
        if self.validate_only:
            self.log_step("SaberSim Pipeline", True, "Skipped (validate only mode)")
            return True

        return self.run_command(
            f"python3 {SABERSIM_PIPELINE}",
            "SaberSim Pipeline"
        )

    def run_mlb_pipeline(self) -> bool:
        """Run MLB data collection pipeline."""
        if self.validate_only:
            self.log_step("MLB Pipeline", True, "Skipped (validate only mode)")
            return True

        return self.run_command(
            f"python3 {MLB_PIPELINE}",
            "MLB Pipeline"
        )

    def run_win_calc_pipeline(self) -> bool:
        """Run Win Calc adjustments pipeline."""
        if self.validate_only:
            self.log_step("Win Calc Pipeline", True, "Skipped (validate only mode)")
            return True

        return self.run_command(
            f"python3 {WIN_CALC_PIPELINE}",
            "Win Calc Pipeline"
        )

    def run_data_validation(self, stage: str) -> bool:
        """Run data validation for a specific stage."""
        if self.skip_validation:
            self.log_step(f"Data Validation ({stage})", True, "Skipped (validation disabled)")
            return True

        validation_report_path = self.report_dir / f"validation_{stage}_{self.timestamp}.json"

        success = self.run_command(
            f"python3 {VALIDATION_TOOL} --quick --output {validation_report_path}",
            f"Data Validation ({stage})"
        )

        if success:
            # Load and analyze validation report
            try:
                with open(validation_report_path, 'r') as f:
                    validation_report = json.load(f)

                self.results["validation_reports"].append({
                    "stage": stage,
                    "report_path": str(validation_report_path),
                    "summary": validation_report.get("summary", {})
                })

                # Update pipeline summary
                summary = validation_report.get("summary", {})
                self.results["summary"]["validation_errors"] += summary.get("error_count", 0)
                self.results["summary"]["validation_warnings"] += summary.get("warning_count", 0)

                return summary.get("error_count", 0) == 0

            except Exception as e:
                self.log_step(f"Validation Report Analysis ({stage})", False, f"Failed to analyze report: {str(e)}")
                return False

        return False

    def generate_pipeline_report(self):
        """Generate comprehensive pipeline report."""
        report_path = self.report_dir / f"pipeline_report_{self.timestamp}.json"

        # Add final summary
        total_steps = self.results["summary"]["total_steps"]
        successful_steps = self.results["summary"]["successful_steps"]
        success_rate = (successful_steps / total_steps * 100) if total_steps > 0 else 0

        self.results["summary"]["success_rate"] = success_rate
        self.results["summary"]["pipeline_status"] = "SUCCESS" if success_rate == 100 else "PARTIAL" if success_rate > 0 else "FAILED"

        # Save report
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        # Print summary
        print(f"\n📊 PIPELINE SUMMARY:")
        print(f"   Total steps: {total_steps}")
        print(f"   Successful: {successful_steps}")
        print(f"   Failed: {self.results['summary']['failed_steps']}")
        print(f"   Success rate: {success_rate:.1f}%")
        print(f"   Validation errors: {self.results['summary']['validation_errors']}")
        print(f"   Validation warnings: {self.results['summary']['validation_warnings']}")
        print(f"   Pipeline status: {self.results['summary']['pipeline_status']}")
        print(f"   Report saved to: {report_path}")

        return report_path

    def run_full_pipeline(self) -> bool:
        """Run the complete pipeline with validation."""
        print("🚀 Starting Master Pipeline with Data Validation")
        print(f"   Timestamp: {self.timestamp}")
        print(f"   Report directory: {self.report_dir}")
        print(f"   Validate only: {self.validate_only}")
        print(f"   Skip validation: {self.skip_validation}")
        print("=" * 60)

        # Step 1: Pre-validation (if not validate-only)
        if not self.validate_only:
            print("\n🔍 Step 1: Pre-validation")
            self.run_data_validation("pre_pipeline")

        # Step 2: SaberSim Pipeline
        print("\n📊 Step 2: SaberSim Data Extraction")
        sabersim_success = self.run_sabersim_pipeline()

        # Step 3: Post-SaberSim validation
        if sabersim_success:
            print("\n🔍 Step 3: Post-SaberSim Validation")
            self.run_data_validation("post_sabersim")

        # Step 4: MLB Pipeline
        print("\n⚾ Step 4: MLB Data Collection")
        mlb_success = self.run_mlb_pipeline()

        # Step 5: Post-MLB validation
        if mlb_success:
            print("\n🔍 Step 5: Post-MLB Validation")
            self.run_data_validation("post_mlb")

        # Step 6: Win Calc Pipeline
        print("\n🧮 Step 6: Win Calc Adjustments")
        win_calc_success = self.run_win_calc_pipeline()

        # Step 7: Post-Win-Calc validation
        if win_calc_success:
            print("\n🔍 Step 7: Post-Win-Calc Validation")
            self.run_data_validation("post_win_calc")

        # Step 8: Final validation
        print("\n🔍 Step 8: Final Validation")
        self.run_data_validation("final")

        # Generate final report
        print("\n📋 Step 9: Generate Pipeline Report")
        report_path = self.generate_pipeline_report()

        # Return overall success
        success_rate = self.results["summary"]["success_rate"]
        return success_rate == 100


def main():
    parser = argparse.ArgumentParser(description="Master Pipeline Runner with Data Validation")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Run only validation, skip data pipelines"
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip validation steps, run only pipelines"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick validation (sample players only)"
    )

    args = parser.parse_args()

    # Create pipeline runner
    runner = MasterPipelineRunner(
        validate_only=args.validate_only,
        skip_validation=args.skip_validation
    )

    # Run pipeline
    success = runner.run_full_pipeline()

    # Exit with appropriate code
    if success:
        print(f"\n🎉 Pipeline completed successfully!")
        sys.exit(0)
    else:
        print(f"\n⚠️ Pipeline completed with issues - check report for details")
        sys.exit(1)


if __name__ == "__main__":
    main()
