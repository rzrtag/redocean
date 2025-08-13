"""
Red Ocean - Main application entry point.
"""

import click
from pathlib import Path

from mlb_api.shared.config import MLBConfig
from mlb_api.shared.incremental_updater import IncrementalUpdater


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Red Ocean - MLB Analytics Platform"""
    pass


@cli.command()
@click.option('--config-path', type=click.Path(exists=True), help='Path to config file')
def setup(config_path):
    """Set up the Red Ocean environment."""
    config = MLBConfig.from_env()
    config.ensure_directories()

    click.echo("✅ Red Ocean environment setup complete!")
    click.echo(f"📁 Data directory: {config.base_data_path}")
    click.echo(f"🔄 Incremental updates: {'enabled' if config.enable_incremental_updates else 'disabled'}")


@cli.command()
@click.option('--force', is_flag=True, help='Force update all data')
def collect(force):
    """Collect MLB data."""
    config = MLBConfig.from_env()
    updater = IncrementalUpdater(config)

    if force:
        updater.clear_cache()
        click.echo("🗑️  Cache cleared, will update all data")

    click.echo("🚀 Starting MLB data collection...")
    # TODO: Implement data collection logic
    click.echo("✅ Data collection complete!")


@cli.command()
def status():
    """Show system status."""
    config = MLBConfig.from_env()
    updater = IncrementalUpdater(config)

    stats = updater.get_update_stats()

    click.echo("📊 Red Ocean System Status")
    click.echo("=" * 30)
    click.echo(f"🏟️  MLB API Base: {config.mlb_api_base_url}")
    click.echo(f"📁 Data Path: {config.base_data_path}")
    click.echo(f"🔄 Incremental Updates: {stats['incremental_updates_enabled']}")
    click.echo(f"📈 Total Tracked Keys: {stats['total_keys']}")
    click.echo(f"⏱️  Rate Limit: {stats['rate_limit']} req/s")


@cli.command()
def clean():
    """Clean cache and temporary files."""
    config = MLBConfig.from_env()
    updater = IncrementalUpdater(config)

    updater.clear_cache()
    click.echo("🧹 Cache cleaned!")


if __name__ == '__main__':
    cli()
