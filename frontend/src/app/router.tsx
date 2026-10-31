import React, { Suspense, lazy } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { RequireAuth, RequireRole, RequireAnonymous } from './guards';
import { useAuth } from './AuthContext';

// Suspense Loading Fallback
const PageLoader: React.FC = () => (
  <div className="flex items-center justify-center min-h-[40vh]">
    <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
  </div>
);

const Lazy: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <Suspense fallback={<PageLoader />}>{children}</Suspense>
);

// Auth Pages (Lazy)
const LoginPage = lazy(() => import('../features/auth/LoginPage').then((m) => ({ default: m.LoginPage })));
const SignupPage = lazy(() => import('../features/auth/SignupPage').then((m) => ({ default: m.SignupPage })));
const ForgotPasswordPage = lazy(() => import('../features/auth/ForgotPasswordPage').then((m) => ({ default: m.ForgotPasswordPage })));
const ResetPasswordPage = lazy(() => import('../features/auth/ResetPasswordPage').then((m) => ({ default: m.ResetPasswordPage })));

// Operations & Admin Pages (Lazy)
const DashboardPage = lazy(() => import('../features/dashboard/DashboardPage').then((m) => ({ default: m.DashboardPage })));
const CustomersListPage = lazy(() => import('../features/customers/CustomersListPage').then((m) => ({ default: m.CustomersListPage })));
const CustomerDetailPage = lazy(() => import('../features/customers/CustomerDetailPage').then((m) => ({ default: m.CustomerDetailPage })));
const StaffListPage = lazy(() => import('../features/staff/StaffListPage').then((m) => ({ default: m.StaffListPage })));
const ProductsListPage = lazy(() => import('../features/catalogue/ProductsListPage').then((m) => ({ default: m.ProductsListPage })));
const PlansListPage = lazy(() => import('../features/catalogue/PlansListPage').then((m) => ({ default: m.PlansListPage })));
const TaxesListPage = lazy(() => import('../features/catalogue/TaxesListPage').then((m) => ({ default: m.TaxesListPage })));
const DiscountsListPage = lazy(() => import('../features/catalogue/DiscountsListPage').then((m) => ({ default: m.DiscountsListPage })));
const QuotationsListPage = lazy(() => import('../features/quotations/QuotationsListPage').then((m) => ({ default: m.QuotationsListPage })));
const QuotationTemplatesListPage = lazy(() => import('../features/quotations/QuotationTemplatesListPage').then((m) => ({ default: m.QuotationTemplatesListPage })));
const SubscriptionsListPage = lazy(() => import('../features/subscriptions/SubscriptionsListPage').then((m) => ({ default: m.SubscriptionsListPage })));
const SubscriptionDetailPage = lazy(() => import('../features/subscriptions/SubscriptionDetailPage').then((m) => ({ default: m.SubscriptionDetailPage })));
const InvoicesListPage = lazy(() => import('../features/invoices/InvoicesListPage').then((m) => ({ default: m.InvoicesListPage })));
const InvoiceDetailPage = lazy(() => import('../features/invoices/InvoiceDetailPage').then((m) => ({ default: m.InvoiceDetailPage })));
const OutstandingInvoicesPage = lazy(() => import('../features/invoices/OutstandingInvoicesPage').then((m) => ({ default: m.OutstandingInvoicesPage })));
const BillingRunPage = lazy(() => import('../features/invoices/BillingRunPage').then((m) => ({ default: m.BillingRunPage })));
const PaymentsListPage = lazy(() => import('../features/payments/PaymentsListPage').then((m) => ({ default: m.PaymentsListPage })));
const RefundsListPage = lazy(() => import('../features/refunds/RefundsListPage').then((m) => ({ default: m.RefundsListPage })));
const AuditLogsListPage = lazy(() => import('../features/audit/AuditLogsListPage').then((m) => ({ default: m.AuditLogsListPage })));

// Customer Portal Pages (Lazy)
const CustomerDashboardPage = lazy(() => import('../features/portal/CustomerDashboardPage').then((m) => ({ default: m.CustomerDashboardPage })));
const CustomerSubscriptionsPage = lazy(() => import('../features/portal/CustomerSubscriptionsPage').then((m) => ({ default: m.CustomerSubscriptionsPage })));
const CustomerInvoicesPage = lazy(() => import('../features/portal/CustomerInvoicesPage').then((m) => ({ default: m.CustomerInvoicesPage })));
const CustomerRefundsPage = lazy(() => import('../features/portal/CustomerRefundsPage').then((m) => ({ default: m.CustomerRefundsPage })));
const CustomerAccountPage = lazy(() => import('../features/portal/CustomerAccountPage').then((m) => ({ default: m.CustomerAccountPage })));
const CustomerNotificationsPage = lazy(() => import('../features/portal/CustomerNotificationsPage').then((m) => ({ default: m.CustomerNotificationsPage })));

// Error Pages
import { ForbiddenPage, NotFoundPage, SessionExpiredPage } from '../components/ErrorPages';

// Dynamic Root Redirect based on user role
const RootRedirect: React.FC = () => {
  const { user, isLoading } = useAuth();
  if (isLoading) return null;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === 'customer') return <Navigate to="/portal/dashboard" replace />;
  return <Navigate to="/dashboard" replace />;
};

export const router = createBrowserRouter([
  // Public Auth Routes
  {
    path: '/login',
    element: (
      <RequireAnonymous>
        <Lazy><LoginPage /></Lazy>
      </RequireAnonymous>
    ),
  },
  {
    path: '/signup',
    element: (
      <RequireAnonymous>
        <Lazy><SignupPage /></Lazy>
      </RequireAnonymous>
    ),
  },
  {
    path: '/forgot-password',
    element: (
      <RequireAnonymous>
        <Lazy><ForgotPasswordPage /></Lazy>
      </RequireAnonymous>
    ),
  },
  {
    path: '/reset-password',
    element: (
      <RequireAnonymous>
        <Lazy><ResetPasswordPage /></Lazy>
      </RequireAnonymous>
    ),
  },
  {
    path: '/session-expired',
    element: <SessionExpiredPage />,
  },
  {
    path: '/403',
    element: <ForbiddenPage />,
  },

  // Main App Shell
  {
    path: '/',
    element: (
      <RequireAuth>
        <Layout />
      </RequireAuth>
    ),
    children: [
      {
        index: true,
        element: <RootRedirect />,
      },

      // Operations & Staff Workspace Routes (admin & staff)
      {
        path: 'dashboard',
        element: (
          <RequireRole roles={['admin', 'staff']}>
            <Lazy><DashboardPage /></Lazy>
          </RequireRole>
        ),
      },
      {
        path: 'customers',
        element: (
          <RequireRole roles={['admin', 'staff']}>
            <Lazy><CustomersListPage /></Lazy>
          </RequireRole>
        ),
      },
      {
        path: 'customers/:id',
        element: (
          <RequireRole roles={['admin', 'staff']}>
            <Lazy><CustomerDetailPage /></Lazy>
          </RequireRole>
        ),
      },
      {
        path: 'subscriptions',
        element: (
          <RequireRole roles={['admin', 'staff']}>
            <Lazy><SubscriptionsListPage /></Lazy>
          </RequireRole>
        ),
      },
      {
        path: 'subscriptions/:id',
        element: (
          <RequireRole roles={['admin', 'staff']}>
            <Lazy><SubscriptionDetailPage /></Lazy>
          </RequireRole>
        ),
      },
      {
        path: 'invoices',
        element: (
          <RequireRole roles={['admin', 'staff']}>
            <Lazy><InvoicesListPage /></Lazy>
          </RequireRole>
        ),
      },
      {
        path: 'invoices/outstanding',
        element: (
          <RequireRole roles={['admin', 'staff']}>
            <Lazy><OutstandingInvoicesPage /></Lazy>
          </RequireRole>
        ),
      },
      {
        path: 'invoices/:id',
        element: (
          <RequireRole roles={['admin', 'staff']}>
            <Lazy><InvoiceDetailPage /></Lazy>
          </RequireRole>
        ),
      },
      {
        path: 'billing-run',
        element: (
          <RequireRole roles={['admin', 'staff']}>
            <Lazy><BillingRunPage /></Lazy>
          </RequireRole>
        ),
      },
      {
        path: 'payments',
        element: (
          <RequireRole roles={['admin', 'staff']}>
            <Lazy><PaymentsListPage /></Lazy>
          </RequireRole>
        ),
      },
      {
        path: 'refunds',
        element: (
          <RequireRole roles={['admin', 'staff']}>
            <Lazy><RefundsListPage /></Lazy>
          </RequireRole>
        ),
      },
      {
        path: 'quotations',
        element: (
          <RequireRole roles={['admin', 'staff']}>
            <Lazy><QuotationsListPage /></Lazy>
          </RequireRole>
        ),
      },
      {
        path: 'quotation-templates',
        element: (
          <RequireRole roles={['admin', 'staff']}>
            <Lazy><QuotationTemplatesListPage /></Lazy>
          </RequireRole>
        ),
      },
      {
        path: 'templates',
        element: <Navigate to="/quotation-templates" replace />,
      },

      // Admin Only Catalogue & Team Routes
      {
        path: 'staff',
        element: (
          <RequireRole roles={['admin']}>
            <Lazy><StaffListPage /></Lazy>
          </RequireRole>
        ),
      },
      {
        path: 'catalogue/products',
        element: (
          <RequireRole roles={['admin']}>
            <Lazy><ProductsListPage /></Lazy>
          </RequireRole>
        ),
      },
      {
        path: 'catalogue/plans',
        element: (
          <RequireRole roles={['admin']}>
            <Lazy><PlansListPage /></Lazy>
          </RequireRole>
        ),
      },
      {
        path: 'catalogue/taxes',
        element: (
          <RequireRole roles={['admin']}>
            <Lazy><TaxesListPage /></Lazy>
          </RequireRole>
        ),
      },
      {
        path: 'catalogue/discounts',
        element: (
          <RequireRole roles={['admin']}>
            <Lazy><DiscountsListPage /></Lazy>
          </RequireRole>
        ),
      },
      {
        path: 'audit-logs',
        element: (
          <RequireRole roles={['admin']}>
            <Lazy><AuditLogsListPage /></Lazy>
          </RequireRole>
        ),
      },

      // Customer Portal Routes (Customer Role Only)
      {
        path: 'portal/dashboard',
        element: (
          <RequireRole roles={['customer']}>
            <Lazy><CustomerDashboardPage /></Lazy>
          </RequireRole>
        ),
      },
      {
        path: 'portal/subscriptions',
        element: (
          <RequireRole roles={['customer']}>
            <Lazy><CustomerSubscriptionsPage /></Lazy>
          </RequireRole>
        ),
      },
      {
        path: 'portal/invoices',
        element: (
          <RequireRole roles={['customer']}>
            <Lazy><CustomerInvoicesPage /></Lazy>
          </RequireRole>
        ),
      },
      {
        path: 'portal/notifications',
        element: (
          <RequireRole roles={['customer']}>
            <Lazy><CustomerNotificationsPage /></Lazy>
          </RequireRole>
        ),
      },
      {
        path: 'portal/refunds',
        element: (
          <RequireRole roles={['customer']}>
            <Lazy><CustomerRefundsPage /></Lazy>
          </RequireRole>
        ),
      },
      {
        path: 'portal/account',
        element: (
          <RequireRole roles={['customer']}>
            <Lazy><CustomerAccountPage /></Lazy>
          </RequireRole>
        ),
      },
    ],
  },

  // Catch-all
  {
    path: '*',
    element: <NotFoundPage />,
  },
]);
