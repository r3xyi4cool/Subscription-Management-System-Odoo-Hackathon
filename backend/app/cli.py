import click
from datetime import date
from flask.cli import with_appcontext

from backend.app.services.billing_service import BillingService
from backend.seed import run_seed


@click.command("seed")
@with_appcontext
def seed_command():
    """Seed dummy data for development and testing."""
    click.echo("Seeding database...")
    run_seed()
    click.echo("Seeding completed successfully.")


@click.command("run-billing")
@click.option("--as-of", default=None, help="Billing date in YYYY-MM-DD format (defaults to today)")
@with_appcontext
def run_billing_command(as_of):
    """Run billing cycle manually for due subscriptions."""
    as_of_date = None
    if as_of:
        try:
            as_of_date = date.fromisoformat(as_of)
        except ValueError:
            click.echo(f"Invalid date format: {as_of}. Use YYYY-MM-DD.")
            return

    click.echo(f"Running billing cycle as of {as_of_date or date.today()}...")
    result = BillingService.generate_invoices_for_due_subscriptions(as_of_date=as_of_date)
    click.echo(
        f"Billing completed: {result['created_count']} invoices created, {result['skipped_count']} skipped."
    )


def register_cli_commands(app):
    app.cli.add_command(seed_command)
    app.cli.add_command(run_billing_command)

