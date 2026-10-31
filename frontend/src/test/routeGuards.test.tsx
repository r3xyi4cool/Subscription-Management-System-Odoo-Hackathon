import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { RequireRole } from '../app/guards';
import * as AuthContextModule from '../app/AuthContext';
import { User } from '../api/types';

describe('Route Guards by Role', () => {
  const mockUser = (role: 'admin' | 'staff' | 'customer', isActive = true): User => ({
    id: 'test_user',
    email: 'test@example.com',
    role,
    name: 'Test User',
    is_active: isActive,
    created_at: '',
    updated_at: '',
  });

  it('renders protected child content when user role matches allowed roles', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: mockUser('admin'),
      role: 'admin',
      isLoading: false,
      isAuthenticated: true,
      isAdmin: true,
      isStaff: false,
      isCustomer: false,
      login: vi.fn(),
      signup: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
      sessionExpiredMessage: null,
      clearSessionExpiredMessage: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/admin-only']}>
        <Routes>
          <Route
            path="/admin-only"
            element={
              <RequireRole roles={['admin']}>
                <div>Admin Secret Content</div>
              </RequireRole>
            }
          />
          <Route path="/403" element={<div>Access Denied 403</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('Admin Secret Content')).toBeInTheDocument();
  });

  it('redirects to /403 when customer attempts to access staff or admin routes', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: mockUser('customer'),
      role: 'customer',
      isLoading: false,
      isAuthenticated: true,
      isAdmin: false,
      isStaff: false,
      isCustomer: true,
      login: vi.fn(),
      signup: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
      sessionExpiredMessage: null,
      clearSessionExpiredMessage: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/staff-dashboard']}>
        <Routes>
          <Route
            path="/staff-dashboard"
            element={
              <RequireRole roles={['admin', 'staff']}>
                <div>Staff Operations</div>
              </RequireRole>
            }
          />
          <Route path="/403" element={<div>Access Denied 403</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.queryByText('Staff Operations')).not.toBeInTheDocument();
    expect(screen.getByText('Access Denied 403')).toBeInTheDocument();
  });

  it('redirects staff to /403 when attempting to access admin-only routes', () => {
    vi.spyOn(AuthContextModule, 'useAuth').mockReturnValue({
      user: mockUser('staff'),
      role: 'staff',
      isLoading: false,
      isAuthenticated: true,
      isAdmin: false,
      isStaff: true,
      isCustomer: false,
      login: vi.fn(),
      signup: vi.fn(),
      logout: vi.fn(),
      refreshUser: vi.fn(),
      sessionExpiredMessage: null,
      clearSessionExpiredMessage: vi.fn(),
    });

    render(
      <MemoryRouter initialEntries={['/staff-management']}>
        <Routes>
          <Route
            path="/staff-management"
            element={
              <RequireRole roles={['admin']}>
                <div>Admin Staff Management</div>
              </RequireRole>
            }
          />
          <Route path="/403" element={<div>Access Denied 403</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.queryByText('Admin Staff Management')).not.toBeInTheDocument();
    expect(screen.getByText('Access Denied 403')).toBeInTheDocument();
  });
});
