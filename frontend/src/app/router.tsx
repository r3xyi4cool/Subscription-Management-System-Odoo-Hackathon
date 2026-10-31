import React from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Layout } from '../components/Layout';
import { RequireAuth, RequireRole, RequireAnonymous } from './guards';
import { useAuth } from './AuthContext';

// Auth Pages
import { LoginPage } from '../features/auth/LoginPage';
import { SignupPage } from '../features/auth/SignupPage';
import { ForgotPasswordPage } from '../features/auth/ForgotPasswordPage';
import { ResetPasswordPage } from '../features/auth/ResetPasswordPage';

// Operations & Admin Pages
import { DashboardPage } from '../features/dashboard/DashboardPage';
import { CustomersListPage } from '../features/customers/CustomersListPage';
import { CustomerDetailPage } from '../features/customers/CustomerDetailPage';
import { StaffListPage } from '../features/staff/StaffListPage';
import { ProductsListPage } from '../features/catalogue/ProductsListPage';
import { PlansListPage } from '../features/catalogue/PlansListPage';
import { TaxesListPage } from '../features/catalogue/TaxesListPage';
import { DiscountsListPage } from '../features/catalogue/DiscountsListPage';
import { QuotationsListPage } from '../features/quotations/QuotationsListPage';
import { QuotationTemplatesListPage } from '../features/quotations/QuotationTemplatesListPage';
import { SubscriptionsListPage } from '../features/subscriptions/SubscriptionsListPage';
import { SubscriptionDetailPage } from '../features/subscriptions/SubscriptionDetailPage';
import { InvoicesListPage } from '../features/invoices/InvoicesListPage';
import { InvoiceDetailPage } from '../features/invoices/InvoiceDetailPage';
import { OutstandingInvoicesPage } from '../features/invoices/OutstandingInvoicesPage';
import { BillingRunPage } from '../features/invoices/BillingRunPage';
import { PaymentsListPage } from '../features/payments/PaymentsListPage';
import { RefundsListPage } from '../features/refunds/RefundsListPage';
import { AuditLogsListPage } from '../features/audit/AuditLogsListPage';

// Customer Portal Pages
import { CustomerDashboardPage } from '../features/portal/CustomerDashboardPage';
import { CustomerSubscriptionsPage } from '../features/portal/CustomerSubscriptionsPage';
import { CustomerInvoicesPage } from '../features/portal/CustomerInvoicesPage';
import { CustomerRefundsPage } from '../features/portal/CustomerRefundsPage';
import { CustomerAccountPage } from '../features/portal/CustomerAccountPage';

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
        <LoginPage />
      </RequireAnonymous>
    ),
  },
  {
    path: '/signup',
    element: (
      <RequireAnonymous>
        <SignupPage />
      </RequireAnonymous>
    ),
  },
  {
    path: '/forgot-password',
    element: (
      <RequireAnonymous>
        <ForgotPasswordPage />
      </RequireAnonymous>
    ),
  },
  {
    path: '/reset-password',
    element: (
      <RequireAnonymous>
        <ResetPasswordPage />
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
            <DashboardPage />
          </RequireRole>
        ),
      },
      {
        path: 'customers',
        element: (
          <RequireRole roles={['admin', 'staff']}>
            <CustomersListPage />
          </RequireRole>
        ),
      },
      {
        path: 'customers/:id',
        element: (
          <RequireRole roles={['admin', 'staff']}>
            <CustomerDetailPage />
          </RequireRole>
        ),
      },
      {
        path: 'quotations',
        element: (
          <RequireRole roles={['admin', 'staff']}>
            <QuotationsListPage />
          </RequireRole>
        ),
      },
      {
        path: 'quotation-templates',
        element: (
          <RequireRole roles={['admin', 'staff']}>
            <QuotationTemplatesListPage />
          </RequireRole>
        ),
      },
      {
        path: 'subscriptions',
        element: (
          <RequireRole roles={['admin', 'staff']}>
            <SubscriptionsListPage />
          </RequireRole>
        ),
      },
      {
        path: 'subscriptions/:id',
        element: (
          <RequireRole roles={['admin', 'staff']}>
            <SubscriptionDetailPage />
          </RequireRole>
        ),
      },
      {
        path: 'invoices',
        element: (
          <RequireRole roles={['admin', 'staff']}>
            <InvoicesListPage />
          </RequireRole>
        ),
      },
      {
        path: 'invoices/outstanding',
        element: (
          <RequireRole roles={['admin', 'staff']}>
            <OutstandingInvoicesPage />
          </RequireRole>
        ),
      },
      {
        path: 'invoices/:id',
        element: (
          <RequireRole roles={['admin', 'staff']}>
            <InvoiceDetailPage />
          </RequireRole>
        ),
      },
      {
        path: 'billing-run',
        element: (
          <RequireRole roles={['admin', 'staff']}>
            <BillingRunPage />
          </RequireRole>
        ),
      },
      {
        path: 'payments',
        element: (
          <RequireRole roles={['admin', 'staff']}>
            <PaymentsListPage />
          </RequireRole>
        ),
      },
      {
        path: 'refunds',
        element: (
          <RequireRole roles={['admin', 'staff']}>
            <RefundsListPage />
          </RequireRole>
        ),
      },

      // Admin Only Management Routes
      {
        path: 'staff',
        element: (
          <RequireRole roles={['admin']}>
            <StaffListPage />
          </RequireRole>
        ),
      },
      {
        path: 'catalogue/products',
        element: (
          <RequireRole roles={['admin']}>
            <ProductsListPage />
          </RequireRole>
        ),
      },
      {
        path: 'catalogue/plans',
        element: (
          <RequireRole roles={['admin']}>
            <PlansListPage />
          </RequireRole>
        ),
      },
      {
        path: 'catalogue/taxes',
        element: (
          <RequireRole roles={['admin']}>
            <TaxesListPage />
          </RequireRole>
        ),
      },
      {
        path: 'catalogue/discounts',
        element: (
          <RequireRole roles={['admin']}>
            <DiscountsListPage />
          </RequireRole>
        ),
      },
      {
        path: 'audit-logs',
        element: (
          <RequireRole roles={['admin']}>
            <AuditLogsListPage />
          </RequireRole>
        ),
      },

      // Customer Portal Routes (Customer Role Only)
      {
        path: 'portal/dashboard',
        element: (
          <RequireRole roles={['customer']}>
            <CustomerDashboardPage />
          </RequireRole>
        ),
      },
      {
        path: 'portal/subscriptions',
        element: (
          <RequireRole roles={['customer']}>
            <CustomerSubscriptionsPage />
          </RequireRole>
        ),
      },
      {
        path: 'portal/invoices',
        element: (
          <RequireRole roles={['customer']}>
            <CustomerInvoicesPage />
          </RequireRole>
        ),
      },
      {
        path: 'portal/refunds',
        element: (
          <RequireRole roles={['customer']}>
            <CustomerRefundsPage />
          </RequireRole>
        ),
      },
      {
        path: 'portal/account',
        element: (
          <RequireRole roles={['customer']}>
            <CustomerAccountPage />
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
