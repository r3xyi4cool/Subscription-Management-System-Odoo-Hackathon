import click
from datetime import date
from flask.cli import with_appcontext, AppGroup

from backend.app.extensions import db
from backend.app.models.subscription import Subscription
from backend.app.models.billing import Invoice
from backend.app.services.billing_service import BillingService
from backend.seed import run_seed


# ---------------- SEED COMMAND ----------------
@click.command("seed")
@with_appcontext
def seed_command():
    """Seed dummy data for development and testing."""
    click.echo("Seeding database...")
    run_seed()
    click.echo("Seeding completed successfully.")


# ---------------- BILLING COMMAND GROUP ----------------
billing_cli = AppGroup("billing", help="Billing cycle management and status commands.")


@billing_cli.command("run")
@click.option("--as-of", default=None, help="Billing date in YYYY-MM-DD format (defaults to today)")
@with_appcontext
def billing_run_command(as_of):
    """Run billing cycle one-shot for due subscriptions."""
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


@billing_cli.command("status")
@with_appcontext
def billing_status_command():
    """Display real-time billing health: active subscriptions, due dates, and outstanding invoices."""
    today = date.today()

    total_active = Subscription.query.filter_by(status="active").count()
    due_today_count = Subscription.query.filter(
        Subscription.status == "active",
        Subscription.next_billing_date <= today,
    ).count()

    upcoming_subs = (
        Subscription.query.filter(
            Subscription.status == "active",
            Subscription.next_billing_date > today,
        )
        .order_by(Subscription.next_billing_date.asc())
        .limit(5)
        .all()
    )

    unpaid_invoices = Invoice.query.filter(
        Invoice.status.in_(["draft", "confirmed"]),
        Invoice.amount_paid < Invoice.total,
    ).all()

    total_unpaid = len(unpaid_invoices)
    total_unpaid_amount = sum(float(inv.total - inv.amount_paid) for inv in unpaid_invoices)

    overdue_invoices = [inv for inv in unpaid_invoices if inv.due_date < today]
    overdue_count = len(overdue_invoices)
    overdue_amount = sum(float(inv.total - inv.amount_paid) for inv in overdue_invoices)

    click.echo("=" * 60)
    click.echo("           SUBSCRIPTION MANAGEMENT SYSTEM - BILLING STATUS")
    click.echo("=" * 60)
    click.echo(f"As of date:                  {today.isoformat()}")
    click.echo(f"Active subscriptions:        {total_active}")
    click.echo(f"Subscriptions due today:     {due_today_count}")
    click.echo(f"Total outstanding invoices:  {total_unpaid} (Total Due: ${total_unpaid_amount:.2f})")
    click.echo(f"Overdue invoices:            {overdue_count} (Overdue Amount: ${overdue_amount:.2f})")
    click.echo("-" * 60)
    click.echo("Next Upcoming Renewals:")
    if not upcoming_subs:
        click.echo("  No upcoming renewals found.")
    else:
        for s in upcoming_subs:
            click.echo(
                f"  - {s.subscription_number or f'SUB-{s.id}'} | Next: {s.next_billing_date} | Customer: {s.customer.name if s.customer else 'N/A'}"
            )
    click.echo("=" * 60)


# ---------------- WORKER COMMAND ----------------
@click.command("run-worker")
@click.option("--once", is_flag=True, default=False, help="Run a single tick and exit")
@click.option("--interval", default=60, type=int, help="Loop interval in seconds (default 60)")
@click.option("--as-of", default=None, help="Date override in YYYY-MM-DD format")
def run_worker_command(once, interval, as_of):
    """Run the background billing & reminder worker loop."""
    from backend.app.worker import run_worker_loop

    run_worker_loop(once=once, interval=interval, as_of=as_of)


# Keep legacy run-billing alias
@click.command("run-billing")
@click.option("--as-of", default=None, help="Billing date in YYYY-MM-DD format")
@with_appcontext
def run_billing_legacy(as_of):
    """Run billing cycle manually (alias for `billing run`)."""
    from click.testing import CliRunner

    ctx = click.get_current_context()
    ctx.invoke(billing_run_command, as_of=as_of)


def register_cli_commands(app):
    app.cli.add_command(seed_command)
    app.cli.add_command(billing_cli)
    app.cli.add_command(run_worker_command)
    app.cli.add_command(run_billing_legacy)
