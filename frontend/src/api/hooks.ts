import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  authApi,
  staffApi,
  customerApi,
  catalogueApi,
  quotationApi,
  subscriptionApi,
  invoiceApi,
  paymentApi,
  refundApi,
  dashboardApi,
  portalApi,
  auditApi,
} from './endpoints';
import { PaginationParams } from './types';

export const queryKeys = {
  authMe: ['auth', 'me'] as const,
  staff: (params?: PaginationParams) => ['staff', params] as const,
  customers: (params?: PaginationParams) => ['customers', params] as const,
  customer: (id: string) => ['customer', id] as const,
  products: (params?: PaginationParams) => ['products', params] as const,
  product: (id: string) => ['product', id] as const,
  plans: (params?: PaginationParams) => ['plans', params] as const,
  plan: (id: string) => ['plan', id] as const,
  taxes: (params?: PaginationParams) => ['taxes', params] as const,
  discounts: (params?: PaginationParams) => ['discounts', params] as const,
  quotations: (params?: PaginationParams) => ['quotations', params] as const,
  quotation: (id: string) => ['quotation', id] as const,
  quotationTemplates: (params?: PaginationParams) => ['quotationTemplates', params] as const,
  subscriptions: (params?: PaginationParams) => ['subscriptions', params] as const,
  subscription: (id: string) => ['subscription', id] as const,
  invoices: (params?: PaginationParams) => ['invoices', params] as const,
  invoice: (id: string) => ['invoice', id] as const,
  outstandingInvoices: (params?: PaginationParams) => ['invoices', 'outstanding', params] as const,
  payments: (params?: PaginationParams) => ['payments', params] as const,
  refunds: (params?: PaginationParams) => ['refunds', params] as const,
  dashboardSummary: (filters?: Record<string, string | number>) => ['dashboard', 'summary', filters] as const,
  dashboardOverdue: (params?: PaginationParams) => ['dashboard', 'overdue', params] as const,
  portalDashboard: ['portal', 'dashboard'] as const,
  portalSubscriptions: (params?: PaginationParams) => ['portal', 'subscriptions', params] as const,
  portalInvoices: (params?: PaginationParams) => ['portal', 'invoices', params] as const,
  auditLogs: (params?: PaginationParams) => ['audit-logs', params] as const,
};

// ----------------------------------------------------------------------------
// Auth Hooks
// ----------------------------------------------------------------------------

export function useAuthMe() {
  return useQuery({
    queryKey: queryKeys.authMe,
    queryFn: () => authApi.getMe(),
    retry: false,
    staleTime: 5 * 60 * 1000,
  });
}

// ----------------------------------------------------------------------------
// Catalogue Hooks
// ----------------------------------------------------------------------------

export function useProducts(params?: PaginationParams) {
  return useQuery({
    queryKey: queryKeys.products(params),
    queryFn: () => catalogueApi.listProducts(params),
    staleTime: 60 * 1000,
  });
}

export function usePlans(params?: PaginationParams) {
  return useQuery({
    queryKey: queryKeys.plans(params),
    queryFn: () => catalogueApi.listPlans(params),
    staleTime: 60 * 1000,
  });
}

export function useTaxes(params?: PaginationParams) {
  return useQuery({
    queryKey: queryKeys.taxes(params),
    queryFn: () => catalogueApi.listTaxes(params),
    staleTime: 60 * 1000,
  });
}

export function useDiscounts(params?: PaginationParams) {
  return useQuery({
    queryKey: queryKeys.discounts(params),
    queryFn: () => catalogueApi.listDiscounts(params),
    staleTime: 60 * 1000,
  });
}

// ----------------------------------------------------------------------------
// Customer Hooks
// ----------------------------------------------------------------------------

export function useCustomers(params?: PaginationParams) {
  return useQuery({
    queryKey: queryKeys.customers(params),
    queryFn: () => customerApi.list(params),
    staleTime: 30 * 1000,
  });
}

export function useCustomer(id: string) {
  return useQuery({
    queryKey: queryKeys.customer(id),
    queryFn: () => customerApi.get(id),
    enabled: Boolean(id),
  });
}

// ----------------------------------------------------------------------------
// Subscription Hooks
// ----------------------------------------------------------------------------

export function useSubscriptions(params?: PaginationParams) {
  return useQuery({
    queryKey: queryKeys.subscriptions(params),
    queryFn: () => subscriptionApi.list(params),
    staleTime: 30 * 1000,
  });
}

export function useSubscription(id: string) {
  return useQuery({
    queryKey: queryKeys.subscription(id),
    queryFn: () => subscriptionApi.get(id),
    enabled: Boolean(id),
  });
}

// ----------------------------------------------------------------------------
// Invoice Hooks
// ----------------------------------------------------------------------------

export function useInvoices(params?: PaginationParams) {
  return useQuery({
    queryKey: queryKeys.invoices(params),
    queryFn: () => invoiceApi.list(params),
    staleTime: 30 * 1000,
  });
}

export function useInvoice(id: string) {
  return useQuery({
    queryKey: queryKeys.invoice(id),
    queryFn: () => invoiceApi.get(id),
    enabled: Boolean(id),
  });
}

export function useOutstandingInvoices(params?: PaginationParams) {
  return useQuery({
    queryKey: queryKeys.outstandingInvoices(params),
    queryFn: () => invoiceApi.listOutstanding(params),
    staleTime: 30 * 1000,
  });
}

// ----------------------------------------------------------------------------
// Payment & Refund Hooks
// ----------------------------------------------------------------------------

export function usePayments(params?: PaginationParams) {
  return useQuery({
    queryKey: queryKeys.payments(params),
    queryFn: () => paymentApi.list(params),
    staleTime: 30 * 1000,
  });
}

export function useRefunds(params?: PaginationParams) {
  return useQuery({
    queryKey: queryKeys.refunds(params),
    queryFn: () => refundApi.list(params),
    staleTime: 30 * 1000,
  });
}

// ----------------------------------------------------------------------------
// Quotation Hooks
// ----------------------------------------------------------------------------

export function useQuotations(params?: PaginationParams) {
  return useQuery({
    queryKey: queryKeys.quotations(params),
    queryFn: () => quotationApi.list(params),
    staleTime: 30 * 1000,
  });
}

export function useQuotation(id: string) {
  return useQuery({
    queryKey: queryKeys.quotation(id),
    queryFn: () => quotationApi.get(id),
    enabled: Boolean(id),
  });
}

export function useQuotationTemplates(params?: PaginationParams) {
  return useQuery({
    queryKey: queryKeys.quotationTemplates(params),
    queryFn: () => quotationApi.listTemplates(params),
    staleTime: 60 * 1000,
  });
}

// ----------------------------------------------------------------------------
// Staff & Audit Hooks
// ----------------------------------------------------------------------------

export function useStaff(params?: PaginationParams) {
  return useQuery({
    queryKey: queryKeys.staff(params),
    queryFn: () => staffApi.list(params),
    staleTime: 60 * 1000,
  });
}

export function useAuditLogs(params?: PaginationParams) {
  return useQuery({
    queryKey: queryKeys.auditLogs(params),
    queryFn: () => auditApi.list(params),
    staleTime: 15 * 1000,
  });
}

// ----------------------------------------------------------------------------
// Dashboard Hooks
// ----------------------------------------------------------------------------

export function useDashboardSummary(filters?: Record<string, string | number>) {
  return useQuery({
    queryKey: queryKeys.dashboardSummary(filters),
    queryFn: () => dashboardApi.getSummary(filters),
    staleTime: 30 * 1000,
  });
}

export function useDashboardOverdue(params?: PaginationParams) {
  return useQuery({
    queryKey: queryKeys.dashboardOverdue(params),
    queryFn: () => dashboardApi.getOverdue(params),
    staleTime: 30 * 1000,
  });
}

// ----------------------------------------------------------------------------
// Portal Hooks
// ----------------------------------------------------------------------------

export function usePortalDashboard() {
  return useQuery({
    queryKey: queryKeys.portalDashboard,
    queryFn: () => portalApi.getMyDashboard(),
    staleTime: 30 * 1000,
  });
}

export function usePortalSubscriptions(params?: PaginationParams) {
  return useQuery({
    queryKey: queryKeys.portalSubscriptions(params),
    queryFn: () => portalApi.getMySubscriptions(params),
    staleTime: 30 * 1000,
  });
}

export function usePortalInvoices(params?: PaginationParams) {
  return useQuery({
    queryKey: queryKeys.portalInvoices(params),
    queryFn: () => portalApi.getMyInvoices(params),
    staleTime: 30 * 1000,
  });
}

// Invalidation helper
export function useInvalidateQueries() {
  const queryClient = useQueryClient();
  return {
    invalidateAll: () => queryClient.invalidateQueries(),
    invalidateAuth: () => queryClient.invalidateQueries({ queryKey: ['auth'] }),
    invalidateSubscriptions: () => queryClient.invalidateQueries({ queryKey: ['subscriptions'] }),
    invalidateInvoices: () => queryClient.invalidateQueries({ queryKey: ['invoices'] }),
    invalidatePayments: () => queryClient.invalidateQueries({ queryKey: ['payments'] }),
    invalidateRefunds: () => queryClient.invalidateQueries({ queryKey: ['refunds'] }),
    invalidateCatalogue: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['plans'] });
      queryClient.invalidateQueries({ queryKey: ['taxes'] });
      queryClient.invalidateQueries({ queryKey: ['discounts'] });
    },
  };
}
