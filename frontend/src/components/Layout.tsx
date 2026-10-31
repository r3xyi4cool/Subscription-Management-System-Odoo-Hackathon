import React, { useState } from 'react';
import { NavLink, Outlet, Link } from 'react-router-dom';
import { useAuth } from '../app/AuthContext';
import { ThemeToggle } from './ThemeToggle';
import {
  LayoutDashboard,
  Users,
  UserCheck,
  Package,
  Layers,
  Percent,
  Receipt,
  CreditCard,
  RotateCcw,
  FileText,
  History,
  Zap,
  Menu,
  X,
  LogOut,
  User,
  Shield,
  ShoppingBag,
  Clock,
} from 'lucide-react';

export const Layout: React.FC = () => {
  const { user, role, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isAdmin = role === 'admin';
  const isStaff = role === 'staff';
  const isCustomer = role === 'customer';

  const staffNavItems = [
    { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { label: 'Subscriptions', href: '/subscriptions', icon: Layers },
    { label: 'Invoices', href: '/invoices', icon: Receipt },
    { label: 'Outstanding', href: '/invoices/outstanding', icon: Clock },
    { label: 'Payments', href: '/payments', icon: CreditCard },
    { label: 'Refunds', href: '/refunds', icon: RotateCcw },
    { label: 'Quotations', href: '/quotations', icon: FileText },
    { label: 'Quotation Templates', href: '/quotation-templates', icon: FileText },
    { label: 'Customers', href: '/customers', icon: Users },
    { label: 'Billing Run', href: '/billing-run', icon: Zap },
  ];

  const adminOnlyNavItems = [
    { label: 'Staff Team', href: '/staff', icon: UserCheck },
    { label: 'Products & Variants', href: '/catalogue/products', icon: Package },
    { label: 'Subscription Plans', href: '/catalogue/plans', icon: ShoppingBag },
    { label: 'Tax Rules', href: '/catalogue/taxes', icon: Percent },
    { label: 'Discount Rules', href: '/catalogue/discounts', icon: Percent },
    { label: 'Audit Logs', href: '/audit-logs', icon: History },
  ];

  const customerNavItems = [
    { label: 'My Dashboard', href: '/portal/dashboard', icon: LayoutDashboard },
    { label: 'My Subscriptions', href: '/portal/subscriptions', icon: Layers },
    { label: 'My Invoices', href: '/portal/invoices', icon: Receipt },
    { label: 'Refund Requests', href: '/portal/refunds', icon: RotateCcw },
    { label: 'Account Profile', href: '/portal/account', icon: User },
  ];

  return (
    <div className="min-h-screen bg-background flex flex-col md:flex-row">
      {/* Mobile Top Header */}
      <div className="flex md:hidden items-center justify-between border-b border-border bg-card px-4 py-3">
        <Link to="/" className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground font-black text-lg">
            B
          </div>
          <span className="font-bold text-foreground">Brightloop SMS</span>
        </Link>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 text-muted-foreground hover:bg-muted rounded-md"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>
      </div>

      {/* Sidebar Navigation */}
      <aside
        className={`${
          mobileMenuOpen ? 'block' : 'hidden'
        } md:block md:w-64 shrink-0 border-r border-border bg-card flex flex-col h-auto md:h-screen md:sticky md:top-0 z-40`}
      >
        {/* Brand Header */}
        <div className="hidden md:flex items-center gap-2.5 px-6 py-5 border-b border-border">
          <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground font-black text-lg shadow-sm">
            B
          </div>
          <div>
            <h1 className="font-bold text-sm tracking-tight text-foreground">Brightloop SMS</h1>
            <p className="text-[10px] text-muted-foreground font-medium">Subscription Management</p>
          </div>
        </div>

        {/* Navigation Items */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-6">
          {isCustomer ? (
            <div className="space-y-1">
              <p className="px-3 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                Customer Portal
              </p>
              {customerNavItems.map((item) => (
                <NavLink
                  key={item.href}
                  to={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                    }`
                  }
                >
                  <item.icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </div>
          ) : (
            <>
              {/* Staff / Operations Section */}
              <div className="space-y-1">
                <p className="px-3 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                  Operations
                </p>
                {staffNavItems.map((item) => (
                  <NavLink
                    key={item.href}
                    to={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={({ isActive }) =>
                      `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                        isActive
                          ? 'bg-primary text-primary-foreground'
                          : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                      }`
                    }
                  >
                    <item.icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </NavLink>
                ))}
              </div>

              {/* Admin Console Section */}
              {isAdmin && (
                <div className="space-y-1">
                  <p className="px-3 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground mb-2 flex items-center gap-1.5">
                    <Shield className="h-3 w-3 text-primary" /> Admin Management
                  </p>
                  {adminOnlyNavItems.map((item) => (
                    <NavLink
                      key={item.href}
                      to={item.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className={({ isActive }) =>
                        `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                          isActive
                            ? 'bg-primary text-primary-foreground'
                            : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                        }`
                      }
                    >
                      <item.icon className="h-4 w-4" />
                      <span>{item.label}</span>
                    </NavLink>
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        {/* User Footer */}
        <div className="border-t border-border p-4 bg-muted/20">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="h-8 w-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-xs uppercase shrink-0">
                {user?.name?.charAt(0) || user?.email?.charAt(0) || 'U'}
              </div>
              <div className="overflow-hidden">
                <p className="text-xs font-semibold text-foreground truncate">{user?.name || user?.email}</p>
                <div className="flex items-center gap-1">
                  <span className="inline-block text-[10px] uppercase font-bold text-muted-foreground">
                    {user?.role}
                  </span>
                </div>
              </div>
            </div>
            <div className="hidden md:block">
              <ThemeToggle />
            </div>
          </div>

          <button
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 rounded-md border border-input bg-background px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-destructive/10 hover:text-destructive hover:border-destructive/30 transition-colors"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span>Sign out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto min-h-screen p-4 sm:p-6 lg:p-8">
        <div className="max-w-7xl mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
