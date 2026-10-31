import React, { useState } from 'react';
import { useStaff, useInvalidateQueries } from '../../api/hooks';
import { staffApi } from '../../api/endpoints';
import { PageHeader } from '../../components/PageHeader';
import { DataTable, Column } from '../../components/DataTable';
import { FormField } from '../../components/FormField';
import { ConfirmDialog } from '../../components/ConfirmDialog';
import { StaffMember } from '../../api/types';
import { formatDate } from '../../lib/dates';
import { Plus, Shield, User, Edit, Power, Check } from 'lucide-react';

export const StaffListPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState('created_at');
  const [order, setOrder] = useState<'asc' | 'desc'>('desc');

  // Modals state
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [editingStaff, setEditingStaff] = useState<StaffMember | null>(null);
  const [deactivatingStaff, setDeactivatingStaff] = useState<StaffMember | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form fields
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState<'admin' | 'staff'>('staff');
  const [phone, setPhone] = useState('');
  const [department, setDepartment] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const { data, isLoading, refetch } = useStaff({
    page,
    per_page: perPage,
    q: search,
    sort,
    order,
  });

  const { invalidateAll } = useInvalidateQueries();

  const handleOpenAdd = () => {
    setName('');
    setEmail('');
    setRole('staff');
    setPhone('');
    setDepartment('');
    setFormError(null);
    setIsAddModalOpen(true);
  };

  const handleOpenEdit = (member: StaffMember) => {
    setEditingStaff(member);
    setName(member.name);
    setEmail(member.email);
    setRole(member.role);
    setPhone(member.phone || '');
    setDepartment(member.department || '');
    setFormError(null);
  };

  const handleCreateStaff = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !email) {
      setFormError('Name and email are required');
      return;
    }
    setIsSubmitting(true);
    setFormError(null);
    try {
      await staffApi.create({
        name,
        email,
        role,
        phone: phone || undefined,
        department: department || undefined,
      });
      setIsAddModalOpen(false);
      refetch();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : 'Failed to create staff member');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateStaff = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingStaff) return;
    setIsSubmitting(true);
    setFormError(null);
    try {
      await staffApi.update(editingStaff.id, {
        name,
        role,
        phone: phone || undefined,
        department: department || undefined,
      });
      setEditingStaff(null);
      refetch();
    } catch (err: unknown) {
      setFormError(err instanceof Error ? err.message : 'Failed to update staff member');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleToggleActive = async (reason?: string) => {
    if (!deactivatingStaff) return;
    setIsSubmitting(true);
    try {
      await staffApi.update(deactivatingStaff.id, {
        is_active: !deactivatingStaff.is_active,
      });
      setDeactivatingStaff(null);
      refetch();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to update status');
    } finally {
      setIsSubmitting(false);
    }
  };

  const columns: Column<StaffMember>[] = [
    {
      key: 'name',
      header: 'Staff Member',
      sortable: true,
      render: (row) => (
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-xs">
            {row.name.charAt(0)}
          </div>
          <div>
            <p className="font-semibold text-foreground">{row.name}</p>
            <p className="text-xs text-muted-foreground">{row.email}</p>
          </div>
        </div>
      ),
    },
    {
      key: 'role',
      header: 'Role',
      sortable: true,
      render: (row) => (
        <span
          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
            row.role === 'admin'
              ? 'bg-purple-50 text-purple-700 border border-purple-200 dark:bg-purple-950/40 dark:text-purple-300'
              : 'bg-blue-50 text-blue-700 border border-blue-200 dark:bg-blue-950/40 dark:text-blue-300'
          }`}
        >
          {row.role === 'admin' ? <Shield className="h-3 w-3" /> : <User className="h-3 w-3" />}
          <span className="uppercase text-[10px] tracking-wider">{row.role}</span>
        </span>
      ),
    },
    {
      key: 'department',
      header: 'Department',
      render: (row) => <span>{row.department || '—'}</span>,
    },
    {
      key: 'phone',
      header: 'Phone',
      render: (row) => <span>{row.phone || '—'}</span>,
    },
    {
      key: 'is_active',
      header: 'Status',
      sortable: true,
      render: (row) => (
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${
            row.is_active
              ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300'
              : 'bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-300'
          }`}
        >
          {row.is_active ? 'Active' : 'Deactivated'}
        </span>
      ),
    },
    {
      key: 'created_at',
      header: 'Joined',
      sortable: true,
      render: (row) => <span>{formatDate(row.created_at)}</span>,
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (row) => (
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleOpenEdit(row)}
            className="p-1 text-muted-foreground hover:text-foreground rounded"
            title="Edit staff details"
          >
            <Edit className="h-3.5 w-3.5" />
          </button>
          <button
            onClick={() => setDeactivatingStaff(row)}
            className={`p-1 rounded ${
              row.is_active ? 'text-rose-600 hover:bg-rose-50' : 'text-emerald-600 hover:bg-emerald-50'
            }`}
            title={row.is_active ? 'Deactivate staff member' : 'Reactivate staff member'}
          >
            <Power className="h-3.5 w-3.5" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Staff Team"
        description="Manage internal organization employees, system roles, and account access permissions"
        actions={
          <button
            onClick={handleOpenAdd}
            className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3.5 py-2 text-xs font-semibold text-primary-foreground shadow hover:bg-primary/90 transition-colors"
          >
            <Plus className="h-4 w-4" /> Add Staff Member
          </button>
        }
      />

      <DataTable
        columns={columns}
        data={data?.items}
        total={data?.total}
        page={page}
        perPage={perPage}
        pages={data?.pages}
        isLoading={isLoading}
        searchPlaceholder="Search staff by name, email, department..."
        onPageChange={setPage}
        onPerPageChange={setPerPage}
        onSearchChange={setSearch}
        onSortChange={(k, ord) => {
          setSort(k);
          setOrder(ord);
        }}
        exportFilename="staff_team"
      />

      {/* Add Staff Modal */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-xl">
            <h3 className="text-base font-semibold text-foreground mb-4">Add Staff Member</h3>

            {formError && (
              <p className="mb-4 rounded bg-destructive/10 p-2 text-xs text-destructive">{formError}</p>
            )}

            <form onSubmit={handleCreateStaff} className="space-y-4">
              <FormField label="Full Name" required id="sname">
                <input
                  id="sname"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Rohan Mehta"
                  required
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </FormField>

              <FormField label="Email" required id="semail">
                <input
                  id="semail"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="rohan@brightloop.test"
                  required
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </FormField>

              <div className="grid grid-cols-2 gap-3">
                <FormField label="System Role" required id="srole">
                  <select
                    id="srole"
                    value={role}
                    onChange={(e) => setRole(e.target.value as 'admin' | 'staff')}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    <option value="staff">Staff</option>
                    <option value="admin">Admin</option>
                  </select>
                </FormField>

                <FormField label="Department" id="sdept">
                  <input
                    id="sdept"
                    type="text"
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    placeholder="Operations"
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </FormField>
              </div>

              <FormField label="Phone" id="sphone">
                <input
                  id="sphone"
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+91 98765 43210"
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </FormField>

              <div className="mt-6 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsAddModalOpen(false)}
                  disabled={isSubmitting}
                  className="rounded-md border border-input px-4 py-2 text-sm font-medium hover:bg-muted"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
                >
                  {isSubmitting ? 'Creating...' : 'Create Staff Member'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Staff Modal */}
      {editingStaff && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-xl">
            <h3 className="text-base font-semibold text-foreground mb-4">Edit Staff Member</h3>

            {formError && (
              <p className="mb-4 rounded bg-destructive/10 p-2 text-xs text-destructive">{formError}</p>
            )}

            <form onSubmit={handleUpdateStaff} className="space-y-4">
              <FormField label="Full Name" required id="esname">
                <input
                  id="esname"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </FormField>

              <div className="grid grid-cols-2 gap-3">
                <FormField label="System Role" required id="esrole">
                  <select
                    id="esrole"
                    value={role}
                    onChange={(e) => setRole(e.target.value as 'admin' | 'staff')}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  >
                    <option value="staff">Staff</option>
                    <option value="admin">Admin</option>
                  </select>
                </FormField>

                <FormField label="Department" id="esdept">
                  <input
                    id="esdept"
                    type="text"
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                  />
                </FormField>
              </div>

              <FormField label="Phone" id="esphone">
                <input
                  id="esphone"
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </FormField>

              <div className="mt-6 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setEditingStaff(null)}
                  disabled={isSubmitting}
                  className="rounded-md border border-input px-4 py-2 text-sm font-medium hover:bg-muted"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
                >
                  {isSubmitting ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Deactivate / Reactivate Confirm Dialog */}
      <ConfirmDialog
        isOpen={Boolean(deactivatingStaff)}
        title={deactivatingStaff?.is_active ? 'Deactivate Staff Account' : 'Reactivate Staff Account'}
        message={
          deactivatingStaff?.is_active
            ? `Are you sure you want to deactivate ${deactivatingStaff?.name}? They will immediately lose access to the system.`
            : `Reactivate staff access for ${deactivatingStaff?.name}?`
        }
        confirmLabel={deactivatingStaff?.is_active ? 'Deactivate Staff' : 'Reactivate Staff'}
        isDestructive={deactivatingStaff?.is_active}
        requireReason={deactivatingStaff?.is_active}
        reasonPlaceholder="Specify reason for account deactivation..."
        isLoading={isSubmitting}
        onConfirm={handleToggleActive}
        onCancel={() => setDeactivatingStaff(null)}
      />
    </div>
  );
};
