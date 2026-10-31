// ============================================================================
// Brightloop SMS - Core API Types Contract
// Based on Section 12 DB Schema and Section 13 API Specification
// All money values are integers in paise (1 INR = 100 paise).
// All date fields follow ISO 8601.
// All field names follow snake_case.
// ============================================================================

export type UserRole = 'admin' | 'staff' | 'customer';

export interface User {
  id: string;
  email: string;
  role: UserRole;
  name: string;
  phone?: string | null;
  company_name?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthSession {
  user: User;
  session_token?: string;
  expires_at?: string;
}

// ----------------------------------------------------------------------------
// Pagination & Error Envelopes
// ----------------------------------------------------------------------------

export interface PaginatedResponse<T> {
  items: T[];
  page: number;
  per_page: number;
  total: number;
  pages: number;
}

export interface ApiErrorPayload {
  error: {
    code: string;
    message: string;
    fields?: Record<string, string[]>;
  };
}

export interface PaginationParams {
  page?: number;
  per_page?: number;
  sort?: string;
  order?: 'asc' | 'desc';
  q?: string;
  [key: string]: string | number | boolean | undefined;
}

// ----------------------------------------------------------------------------
// Customers
// ----------------------------------------------------------------------------

export interface Customer {
  id: string;
  user_id?: string;
  name: string;
  email: string;
  phone?: string | null;
  company_name?: string | null;
  billing_address?: string | null;
  shipping_address?: string | null;
  gstin?: string | null;
  is_active: boolean;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CustomerDetail extends Customer {
  active_subscriptions_count?: number;
  total_invoiced_paise?: number;
  outstanding_balance_paise?: number;
}

// ----------------------------------------------------------------------------
// Staff
// ----------------------------------------------------------------------------

export interface StaffMember {
  id: string;
  user_id: string;
  name: string;
  email: string;
  role: 'admin' | 'staff';
  phone?: string | null;
  department?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ----------------------------------------------------------------------------
// Catalogue: Products & Variants
// ----------------------------------------------------------------------------

export type ProductType = 'service' | 'software' | 'add_on';

export interface ProductVariant {
  id: string;
  product_id: string;
  name: string;
  sku: string;
  extra_price_paise: number; // in paise
  is_active: boolean;
  created_at: string;
}

export interface Product {
  id: string;
  name: string;
  sku: string;
  description?: string | null;
  type: ProductType;
  sales_price_paise: number; // base price in paise
  tax_rule_id?: string | null;
  is_active: boolean;
  variants?: ProductVariant[];
  created_at: string;
  updated_at: string;
}

// ----------------------------------------------------------------------------
// Catalogue: Plans
// ----------------------------------------------------------------------------

export type BillingPeriod = 'daily' | 'weekly' | 'monthly' | 'yearly';

export interface Plan {
  id: string;
  name: string;
  code: string;
  description?: string | null;
  billing_period: BillingPeriod;
  min_quantity: number;
  available_from?: string | null; // YYYY-MM-DD
  available_to?: string | null;   // YYYY-MM-DD
  // 4 Plan Toggles
  auto_close: boolean;
  allow_early_close: boolean;
  allow_pause: boolean;
  allow_renewal: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ----------------------------------------------------------------------------
// Catalogue: Taxes & Discounts
// ----------------------------------------------------------------------------

export interface TaxRule {
  id: string;
  name: string;
  code: string;
  rate_percent: number; // e.g. 18 for 18%
  description?: string | null;
  is_active: boolean;
  created_at: string;
}

export type DiscountType = 'percent' | 'fixed';
export type DiscountScope = 'subscription' | 'line' | 'product';

export interface DiscountRule {
  id: string;
  code: string;
  name: string;
  discount_type: DiscountType;
  discount_value: number; // paise if fixed, or percentage if percent
  scope: DiscountScope;
  min_amount_paise?: number; // in paise
  min_quantity?: number;
  valid_from?: string | null; // YYYY-MM-DD
  valid_to?: string | null;   // YYYY-MM-DD
  usage_limit?: number | null;
  times_used: number;
  target_product_id?: string | null;
  is_active: boolean;
  created_at: string;
}

// ----------------------------------------------------------------------------
// Quotations & Quotation Templates
// ----------------------------------------------------------------------------

export type QuotationStatus = 'draft' | 'sent' | 'accepted' | 'expired' | 'rejected' | 'converted';

export interface QuotationLineItem {
  id: string;
  product_id: string;
  product_name?: string;
  variant_id?: string | null;
  variant_name?: string | null;
  quantity: number;
  unit_price_paise: number;
  discount_paise: number;
  tax_rate_percent: number;
  line_subtotal_paise: number;
  line_tax_paise: number;
  line_total_paise: number;
}

export interface Quotation {
  id: string;
  quotation_number: string;
  customer_id: string;
  customer_name?: string;
  customer_email?: string;
  plan_id: string;
  plan_name?: string;
  status: QuotationStatus;
  validity_days: number;
  valid_until: string; // YYYY-MM-DD
  subtotal_paise: number;
  discount_total_paise: number;
  tax_total_paise: number;
  total_paise: number;
  items: QuotationLineItem[];
  notes?: string | null;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface QuotationTemplate {
  id: string;
  name: string;
  description?: string | null;
  default_validity_days: number;
  default_plan_id?: string | null;
  default_notes?: string | null;
  line_items: Array<{
    product_id: string;
    variant_id?: string | null;
    quantity: number;
  }>;
  is_active: boolean;
  created_at: string;
}

// ----------------------------------------------------------------------------
// Subscriptions
// ----------------------------------------------------------------------------

export type SubscriptionStatus =
  | 'draft'
  | 'quotation'
  | 'confirmed'
  | 'active'
  | 'paused'
  | 'closed';

export interface SubscriptionOrderLine {
  id: string;
  subscription_id: string;
  product_id: string;
  product_name?: string;
  variant_id?: string | null;
  variant_name?: string | null;
  quantity: number;
  unit_price_paise: number; // base + variant extra
  tax_rule_id?: string | null;
  tax_rate_percent: number;
  line_subtotal_paise: number;
  line_tax_paise: number;
  line_total_paise: number;
}

export interface SubscriptionStatusHistory {
  id: string;
  subscription_id: string;
  from_status?: SubscriptionStatus | null;
  to_status: SubscriptionStatus;
  changed_by_user_id: string;
  changed_by_name: string;
  reason?: string | null;
  created_at: string;
}

export interface Subscription {
  id: string;
  subscription_number: string; // e.g. SUB-2026-000123
  customer_id: string;
  customer_name?: string;
  customer_email?: string;
  plan_id: string;
  plan?: Plan;
  plan_name?: string;
  billing_period: BillingPeriod;
  status: SubscriptionStatus;
  start_date?: string | null; // YYYY-MM-DD
  end_date?: string | null;   // YYYY-MM-DD
  next_billing_date?: string | null; // YYYY-MM-DD
  quotation_id?: string | null;
  applied_discount_id?: string | null;
  applied_discount_name?: string | null;
  subtotal_paise: number;
  discount_paise: number;
  tax_paise: number;
  recurring_total_paise: number; // Estimate per billing cycle
  lines: SubscriptionOrderLine[];
  status_history?: SubscriptionStatusHistory[];
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

// ----------------------------------------------------------------------------
// Invoices
// ----------------------------------------------------------------------------

export type InvoiceStatus = 'draft' | 'confirmed' | 'paid' | 'cancelled';

export interface InvoiceLine {
  id: string;
  invoice_id: string;
  product_id?: string | null;
  product_name: string;
  variant_id?: string | null;
  variant_name?: string | null;
  quantity: number;
  unit_price_paise: number;
  tax_rule_id?: string | null;
  tax_rate_percent: number;
  line_subtotal_paise: number;
  line_tax_paise: number;
  line_total_paise: number;
}

export interface Invoice {
  id: string;
  invoice_number: string; // e.g. INV-2026-000123
  subscription_id?: string | null;
  subscription_number?: string | null;
  customer_id: string;
  customer_name?: string;
  customer_email?: string;
  status: InvoiceStatus;
  issue_date: string; // YYYY-MM-DD
  due_date: string;   // YYYY-MM-DD
  billing_period_start?: string | null;
  billing_period_end?: string | null;
  lines_subtotal_paise: number;
  discount_rule_id?: string | null;
  discount_name?: string | null;
  discount_paise: number; // Separate line item discount
  taxable_amount_paise: number;
  tax_total_paise: number;
  total_paise: number;
  amount_paid_paise: number;
  balance_due_paise: number;
  lines: InvoiceLine[];
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface BillingRunResult {
  run_at: string;
  created_count: number;
  skipped_count: number;
  failed_count: number;
  created: Array<{
    subscription_id: string;
    subscription_number: string;
    invoice_id: string;
    invoice_number: string;
    amount_paise: number;
  }>;
  skipped: Array<{
    subscription_id: string;
    subscription_number: string;
    reason: string;
  }>;
  failed: Array<{
    subscription_id: string;
    subscription_number: string;
    error: string;
  }>;
}

// ----------------------------------------------------------------------------
// Payments
// ----------------------------------------------------------------------------

export type PaymentMethod = 'credit_card' | 'bank_transfer' | 'upi' | 'cash' | 'cheque' | 'other';

export interface Payment {
  id: string;
  payment_number: string; // e.g. PAY-2026-000123
  invoice_id: string;
  invoice_number?: string;
  customer_id: string;
  customer_name?: string;
  amount_paise: number;
  payment_method: PaymentMethod;
  payment_date: string; // YYYY-MM-DD
  reference?: string | null;
  notes?: string | null;
  recorded_by_user_id?: string;
  recorded_by_name?: string;
  created_at: string;
}

// ----------------------------------------------------------------------------
// Refunds
// ----------------------------------------------------------------------------

export type RefundStatus = 'requested' | 'approved' | 'processed' | 'rejected';

export interface Refund {
  id: string;
  refund_number: string; // e.g. REF-2026-000123
  payment_id: string;
  payment_number?: string;
  invoice_id: string;
  invoice_number?: string;
  customer_id: string;
  customer_name?: string;
  amount_paise: number;
  reason: string;
  status: RefundStatus;
  requested_by_user_id?: string;
  approved_by_user_id?: string;
  processed_by_user_id?: string;
  rejection_reason?: string | null;
  created_at: string;
  updated_at: string;
}

// ----------------------------------------------------------------------------
// Dashboard & Analytics
// ----------------------------------------------------------------------------

export interface DashboardSummary {
  active_subscriptions: number;
  revenue_collected_paise: number;
  amount_owed_paise: number;
  payments_received_count: number;
  overdue_invoices_count: number;
  overdue_amount_paise: number;
  mrr_paise: number;
  arr_paise: number;
  churn_rate_percent: number;
  collection_rate_percent: number;
  revenue_trend: Array<{
    date: string;
    revenue_paise: number;
    invoiced_paise: number;
  }>;
  subscription_distribution: Array<{
    name: string;
    count: number;
  }>;
}

export interface CustomerDashboardSummary {
  active_subscriptions_count: number;
  total_spent_paise: number;
  pending_invoices_count: number;
  balance_due_paise: number;
  next_renewal_date?: string | null;
  recent_invoices: Invoice[];
  recent_subscriptions: Subscription[];
}

// ----------------------------------------------------------------------------
// Audit Log
// ----------------------------------------------------------------------------

export interface AuditLog {
  id: string;
  user_id?: string | null;
  user_name?: string | null;
  user_email?: string | null;
  action: string;
  entity_type: string;
  entity_id: string;
  details?: Record<string, unknown> | null;
  ip_address?: string | null;
  created_at: string;
}
