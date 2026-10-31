import { apiClient } from './client';
import {
  User,
  PaginatedResponse,
  PaginationParams,
  Customer,
  CustomerDetail,
  StaffMember,
  Product,
  ProductVariant,
  Plan,
  TaxRule,
  DiscountRule,
  Quotation,
  QuotationTemplate,
  Subscription,
  Invoice,
  Payment,
  Refund,
  DashboardSummary,
  CustomerDashboardSummary,
  BillingRunResult,
  AuditLog,
} from './types';

function buildQuery(params?: PaginationParams): string {
  if (!params) return '';
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, val]) => {
    if (val !== undefined && val !== null && val !== '') {
      searchParams.set(key, String(val));
    }
  });
  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : '';
}

// ============================================================================
// Auth Endpoints
// ============================================================================

export const authApi = {
  signup: (data: { email: string; password: string; name: string; phone?: string; company_name?: string }) =>
    apiClient<{ user: User; access_token?: string; session_token?: string }>('auth/signup', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  login: (data: { email: string; password: string }) =>
    apiClient<{ user: User; access_token?: string; session_token?: string }>('auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  logout: () =>
    apiClient<{ message: string }>('auth/logout', {
      method: 'POST',
    }),

  forgotPassword: (data: { email: string }) =>
    apiClient<{ message: string }>('auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  resetPassword: (data: { token: string; password: string }) =>
    apiClient<{ message: string }>('auth/reset-password', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  getMe: () =>
    apiClient<User>('auth/me'),

  updateProfile: (data: Partial<User>) =>
    apiClient<User>('auth/me', {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  changePassword: (data: { current_password: string; new_password: string }) =>
    apiClient<{ message: string }>('auth/change-password', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};

// ============================================================================
// Staff Endpoints (Admin)
// ============================================================================

export const staffApi = {
  list: (params?: PaginationParams) =>
    apiClient<PaginatedResponse<StaffMember>>(`staff${buildQuery(params)}`),

  create: (data: { name: string; email: string; role: 'admin' | 'staff'; phone?: string; department?: string; password?: string }) =>
    apiClient<StaffMember>('staff', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: string, data: Partial<StaffMember>) =>
    apiClient<StaffMember>(`staff/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
};

// ============================================================================
// Customer Endpoints
// ============================================================================

export const customerApi = {
  list: (params?: PaginationParams) =>
    apiClient<PaginatedResponse<Customer>>(`customers${buildQuery(params)}`),

  get: (id: string) =>
    apiClient<CustomerDetail>(`customers/${id}`),

  create: (data: Partial<Customer>) =>
    apiClient<Customer>('customers', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: string, data: Partial<Customer>) =>
    apiClient<Customer>(`customers/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  sendResetLink: (customerId: string) =>
    apiClient<{ message: string; reset_link?: string }>(`customers/${customerId}/send-reset-link`, {
      method: 'POST',
    }),
};

// ============================================================================
// Catalogue Endpoints: Products, Plans, Taxes, Discounts
// ============================================================================

export const catalogueApi = {
  // Products
  listProducts: (params?: PaginationParams) =>
    apiClient<PaginatedResponse<Product>>(`products${buildQuery(params)}`),

  getProduct: (id: string) =>
    apiClient<Product>(`products/${id}`),

  createProduct: (data: Partial<Product>) =>
    apiClient<Product>('products', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateProduct: (id: string, data: Partial<Product>) =>
    apiClient<Product>(`products/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  deleteProduct: (id: string) =>
    apiClient<{ message: string }>(`products/${id}`, {
      method: 'DELETE',
    }),

  createVariant: (productId: string, data: Partial<ProductVariant>) =>
    apiClient<ProductVariant>(`products/${productId}/variants`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  // Plans
  listPlans: (params?: PaginationParams) =>
    apiClient<PaginatedResponse<Plan>>(`plans${buildQuery(params)}`),

  getPlan: (id: string) =>
    apiClient<Plan>(`plans/${id}`),

  createPlan: (data: Partial<Plan>) =>
    apiClient<Plan>('plans', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updatePlan: (id: string, data: Partial<Plan>) =>
    apiClient<Plan>(`plans/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  deletePlan: (id: string) =>
    apiClient<{ message: string }>(`plans/${id}`, {
      method: 'DELETE',
    }),

  // Taxes
  listTaxes: (params?: PaginationParams) =>
    apiClient<PaginatedResponse<TaxRule>>(`taxes${buildQuery(params)}`),

  createTax: (data: Partial<TaxRule>) =>
    apiClient<TaxRule>('taxes', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateTax: (id: string, data: Partial<TaxRule>) =>
    apiClient<TaxRule>(`taxes/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  deleteTax: (id: string) =>
    apiClient<{ message: string }>(`taxes/${id}`, {
      method: 'DELETE',
    }),

  // Discounts
  listDiscounts: (params?: PaginationParams) =>
    apiClient<PaginatedResponse<DiscountRule>>(`discounts${buildQuery(params)}`),

  createDiscount: (data: Partial<DiscountRule>) =>
    apiClient<DiscountRule>('discounts', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateDiscount: (id: string, data: Partial<DiscountRule>) =>
    apiClient<DiscountRule>(`discounts/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  deleteDiscount: (id: string) =>
    apiClient<{ message: string }>(`discounts/${id}`, {
      method: 'DELETE',
    }),
};

// ============================================================================
// Quotations & Templates
// ============================================================================

export const quotationApi = {
  listTemplates: (params?: PaginationParams) =>
    apiClient<PaginatedResponse<QuotationTemplate>>(`quotation-templates${buildQuery(params)}`),

  createTemplate: (data: Partial<QuotationTemplate>) =>
    apiClient<QuotationTemplate>('quotation-templates', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  list: (params?: PaginationParams) =>
    apiClient<PaginatedResponse<Quotation>>(`quotations${buildQuery(params)}`),

  get: (id: string) =>
    apiClient<Quotation>(`quotations/${id}`),

  create: (data: Partial<Quotation>) =>
    apiClient<Quotation>('quotations', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: string, data: Partial<Quotation>) =>
    apiClient<Quotation>(`quotations/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
};

// ============================================================================
// Subscriptions
// ============================================================================

export const subscriptionApi = {
  list: (params?: PaginationParams) =>
    apiClient<PaginatedResponse<Subscription>>(`subscriptions${buildQuery(params)}`),

  get: (id: string) =>
    apiClient<Subscription>(`subscriptions/${id}`),

  create: (data: Partial<Subscription>) =>
    apiClient<Subscription>('subscriptions', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: string, data: Partial<Subscription>) =>
    apiClient<Subscription>(`subscriptions/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  // State transitions
  confirm: (id: string, reason?: string) =>
    apiClient<Subscription>(`subscriptions/${id}/confirm`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),

  activate: (id: string, reason?: string) =>
    apiClient<Subscription>(`subscriptions/${id}/activate`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),

  pause: (id: string, reason?: string) =>
    apiClient<Subscription>(`subscriptions/${id}/pause`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),

  resume: (id: string, reason?: string) =>
    apiClient<Subscription>(`subscriptions/${id}/resume`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),

  renew: (id: string, reason?: string) =>
    apiClient<Subscription>(`subscriptions/${id}/renew`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),

  close: (id: string, reason?: string) =>
    apiClient<Subscription>(`subscriptions/${id}/close`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),
};

// ============================================================================
// Invoices & Billing Run
// ============================================================================

export const invoiceApi = {
  list: (params?: PaginationParams) =>
    apiClient<PaginatedResponse<Invoice>>(`invoices${buildQuery(params)}`),

  get: (id: string) =>
    apiClient<Invoice>(`invoices/${id}`),

  create: (data: Partial<Invoice>) =>
    apiClient<Invoice>('invoices', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  confirm: (id: string) =>
    apiClient<Invoice>(`invoices/${id}/confirm`, {
      method: 'POST',
    }),

  send: (id: string) =>
    apiClient<{ message: string }>(`invoices/${id}/send`, {
      method: 'POST',
    }),

  cancel: (id: string, reason?: string) =>
    apiClient<Invoice>(`invoices/${id}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),

  getPdf: (id: string) =>
    apiClient<Blob>(`invoices/${id}/pdf`),

  listOutstanding: (params?: PaginationParams) =>
    apiClient<PaginatedResponse<Invoice>>(`invoices/outstanding${buildQuery(params)}`),

  runBilling: () =>
    apiClient<BillingRunResult>('billing/run', {
      method: 'POST',
    }),
};

// ============================================================================
// Payments
// ============================================================================

export const paymentApi = {
  list: (params?: PaginationParams) =>
    apiClient<PaginatedResponse<Payment>>(`payments${buildQuery(params)}`),

  create: (data: Partial<Payment>) =>
    apiClient<Payment>('payments', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: string, data: Partial<Payment>) =>
    apiClient<Payment>(`payments/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
};

// ============================================================================
// Refunds
// ============================================================================

export const refundApi = {
  list: (params?: PaginationParams) =>
    apiClient<PaginatedResponse<Refund>>(`refunds${buildQuery(params)}`),

  create: (data: Partial<Refund>) =>
    apiClient<Refund>('refunds', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: string, data: Partial<Refund>) =>
    apiClient<Refund>(`refunds/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),
};

// ============================================================================
// Dashboard & Analytics
// ============================================================================

export const dashboardApi = {
  getSummary: (params?: Record<string, string | number>) =>
    apiClient<DashboardSummary>(`dashboard/summary${buildQuery(params)}`),

  getOverdue: (params?: PaginationParams) =>
    apiClient<PaginatedResponse<Invoice>>(`dashboard/overdue${buildQuery(params)}`),
};

// ============================================================================
// Customer Portal
// ============================================================================

export const portalApi = {
  getMySubscriptions: (params?: PaginationParams) =>
    apiClient<PaginatedResponse<Subscription>>(`me/subscriptions${buildQuery(params)}`),

  getMyInvoices: (params?: PaginationParams) =>
    apiClient<PaginatedResponse<Invoice>>(`me/invoices${buildQuery(params)}`),

  getMyDashboard: () =>
    apiClient<CustomerDashboardSummary>('me/dashboard'),
};

// ============================================================================
// Audit Logs (Admin)
// ============================================================================

export const auditApi = {
  list: (params?: PaginationParams) =>
    apiClient<PaginatedResponse<AuditLog>>(`audit-logs${buildQuery(params)}`),
};
