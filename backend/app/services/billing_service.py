from datetime import date, timedelta
from decimal import Decimal
import calendar
import uuid

from sqlalchemy.exc import IntegrityError

from backend.app.extensions import db
from backend.app.models.subscription import Subscription
from backend.app.models.billing import Invoice, InvoiceLine
from backend.app.models.catalog import Discount
from backend.app.services.pricing_service import PricingService
from backend.app.services.audit_service import log_audit


def add_billing_period(start_date: date, period: str) -> date:
    period = period.lower()
    if period == "daily":
        return start_date + timedelta(days=1)
    elif period == "weekly":
        return start_date + timedelta(days=7)
    elif period == "monthly":
        year = start_date.year
        month = start_date.month + 1
        if month > 12:
            month = 1
            year += 1
        day = min(start_date.day, calendar.monthrange(year, month)[1])
        return date(year, month, day)
    elif period == "yearly":
        year = start_date.year + 1
        day = start_date.day
        if start_date.month == 2 and day == 29 and not calendar.isleap(year):
            day = 28
        return date(year, start_date.month, day)
    else:
        # Default 30 days
        return start_date + timedelta(days=30)


class BillingService:
    @classmethod
    def generate_invoices_for_due_subscriptions(cls, as_of_date: date = None, auth_id: int = None):
        if as_of_date is None:
            as_of_date = date.today()

        created_invoices = []
        skipped_count = 0

        # Only ACTIVE subscriptions are billed. Paused, closed, draft, quotation are ignored.
        active_subscriptions = Subscription.query.filter(
            Subscription.status == "active",
            Subscription.next_billing_date <= as_of_date,
        ).all()

        for sub in active_subscriptions:
            plan = sub.plan
            # Catch up missed periods safely
            # Safeguard maximum loop to prevent runaway cycles
            max_iterations = 365
            iterations = 0

            while sub.next_billing_date <= as_of_date and iterations < max_iterations:
                iterations += 1
                p_start = sub.current_period_start
                p_end = sub.current_period_end

                # Check unique constraint (subscription_id, billing_period_start)
                existing = Invoice.query.filter_by(
                    subscription_id=sub.id, billing_period_start=p_start
                ).first()

                if existing:
                    # Already billed for this period, advance safely
                    skipped_count += 1
                else:
                    try:
                        with db.session.begin_nested():
                            invoice_num = f"INV-{sub.id}-{p_start.strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
                            due_date = as_of_date + timedelta(days=14)

                            invoice = Invoice(
                                invoice_number=invoice_num,
                                subscription_id=sub.id,
                                customer_id=sub.customer_id,
                                status="draft",
                                issue_date=as_of_date,
                                due_date=due_date,
                                billing_period_start=p_start,
                                billing_period_end=p_end,
                                subtotal=Decimal("0.00"),
                                tax_amount=Decimal("0.00"),
                                discount_amount=Decimal("0.00"),
                                total=Decimal("0.00"),
                                amount_paid=Decimal("0.00"),
                            )
                            db.session.add(invoice)
                            db.session.flush()

                            total_subtotal = Decimal("0.00")
                            total_tax = Decimal("0.00")
                            total_discount = Decimal("0.00")
                            total_amount = Decimal("0.00")

                            for line in sub.lines:
                                calc = PricingService.calculate_line(
                                    product=line.product,
                                    quantity=line.quantity,
                                    variant=line.variant,
                                    discount=line.discount,
                                    tax=line.tax,
                                    as_of_date=as_of_date,
                                    context="subscription",
                                )

                                # Atomic discount usage increment
                                if calc["discount_applied"] and line.discount:
                                    if line.discount.usage_limit is not None:
                                        affected = (
                                            db.session.query(Discount)
                                            .filter(
                                                Discount.id == line.discount.id,
                                                Discount.used_count < line.discount.usage_limit,
                                            )
                                            .update({Discount.used_count: Discount.used_count + 1})
                                        )
                                        if affected == 0:
                                            # Concurrently exhausted: recalculate line without discount
                                            calc = PricingService.calculate_line(
                                                product=line.product,
                                                quantity=line.quantity,
                                                variant=line.variant,
                                                discount=None,
                                                tax=line.tax,
                                                as_of_date=as_of_date,
                                                context="subscription",
                                            )
                                    else:
                                        line.discount.used_count += 1

                                inv_line = InvoiceLine(
                                    invoice_id=invoice.id,
                                    product_id=line.product_id,
                                    variant_id=line.variant_id,
                                    description=f"{line.product.name} ({sub.plan.name})",
                                    quantity=line.quantity,
                                    unit_price=calc["unit_price"],
                                    variant_price=calc["variant_price"],
                                    discount_amount=calc["discount_amount"],
                                    tax_amount=calc["tax_amount"],
                                    line_total=calc["line_total"],
                                )
                                db.session.add(inv_line)

                                total_subtotal += calc["subtotal"]
                                total_discount += calc["discount_amount"]
                                total_tax += calc["tax_amount"]
                                total_amount += calc["line_total"]

                            invoice.subtotal = total_subtotal
                            invoice.discount_amount = total_discount
                            invoice.tax_amount = total_tax
                            invoice.total = total_amount

                            created_invoices.append(invoice)
                            log_audit(
                                auth_id=auth_id,
                                entity_type="invoice",
                                entity_id=invoice.id,
                                action="generate",
                                new_values=invoice.to_dict(),
                            )
                    except IntegrityError:
                        # Concurrent billing generated this period first; catch-up safely
                        skipped_count += 1

                # Advance period
                next_start = p_end
                next_end = add_billing_period(next_start, plan.billing_period)
                sub.current_period_start = next_start
                sub.current_period_end = next_end
                sub.next_billing_date = next_start

        db.session.commit()
        return {
            "created_count": len(created_invoices),
            "skipped_count": skipped_count,
            "invoices": [inv.to_dict() for inv in created_invoices],
        }

