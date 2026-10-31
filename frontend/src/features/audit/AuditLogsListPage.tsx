import React, { useState } from 'react';
import { useAuditLogs } from '../../api/hooks';
import { PageHeader } from '../../components/PageHeader';
import { DataTable, Column } from '../../components/DataTable';
import { AuditLog } from '../../api/types';
import { formatDateTime } from '../../lib/dates';
import { History, Eye, X } from 'lucide-react';

export const AuditLogsListPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(20);
  const [search, setSearch] = useState('');
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  const { data, isLoading } = useAuditLogs({
    page,
    per_page: perPage,
    q: search,
  });

  const columns: Column<AuditLog>[] = [
    {
      key: 'created_at',
      header: 'Timestamp (UTC)',
      sortable: true,
      render: (row) => <span className="font-mono text-xs">{formatDateTime(row.created_at)}</span>,
    },
    {
      key: 'action',
      header: 'Action',
      sortable: true,
      render: (row) => (
        <span className="font-mono font-semibold text-xs px-2 py-0.5 rounded bg-muted border border-border text-primary">
          {row.action}
        </span>
      ),
    },
    {
      key: 'entity_type',
      header: 'Entity',
      render: (row) => (
        <div className="text-xs">
          <span className="uppercase text-[11px] font-bold text-muted-foreground">{row.entity_type}</span>
          <p className="font-mono text-foreground">{row.entity_id}</p>
        </div>
      ),
    },
    {
      key: 'user_name',
      header: 'Actor',
      render: (row) => (
        <div>
          <p className="font-medium text-foreground text-xs">{row.user_name || 'System'}</p>
          <p className="text-[11px] text-muted-foreground">{row.user_email || '—'}</p>
        </div>
      ),
    },
    {
      key: 'ip_address',
      header: 'IP Address',
      render: (row) => <span className="font-mono text-xs text-muted-foreground">{row.ip_address || '—'}</span>,
    },
    {
      key: 'details',
      header: 'Payload',
      render: (row) => (
        <button
          onClick={() => setSelectedLog(row)}
          className="inline-flex items-center gap-1 text-xs text-primary hover:underline font-medium"
        >
          <Eye className="h-3 w-3" /> Inspect JSON
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Audit Logs"
        description="Immutable system trail of sensitive operations, billing runs, and authorization activities"
      />

      <DataTable
        columns={columns}
        data={data?.items}
        total={data?.total}
        page={page}
        perPage={perPage}
        pages={data?.pages}
        isLoading={isLoading}
        searchPlaceholder="Search audit logs by action, user, entity ID..."
        onPageChange={setPage}
        onPerPageChange={setPerPage}
        onSearchChange={setSearch}
        exportFilename="audit_logs"
      />

      {/* JSON Payload Inspector Modal */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-lg rounded-xl border border-border bg-card p-6 shadow-xl">
            <div className="flex items-center justify-between border-b border-border pb-3 mb-4">
              <div>
                <h3 className="text-base font-semibold text-foreground">Audit Log Event Payload</h3>
                <p className="font-mono text-xs text-muted-foreground">{selectedLog.action} on {selectedLog.entity_id}</p>
              </div>
              <button
                onClick={() => setSelectedLog(null)}
                className="p-1 text-muted-foreground hover:bg-muted rounded"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <pre className="max-h-80 overflow-auto rounded-lg bg-muted p-4 font-mono text-xs text-foreground">
              {JSON.stringify(selectedLog.details || {}, null, 2)}
            </pre>

            <div className="mt-4 flex justify-end">
              <button
                onClick={() => setSelectedLog(null)}
                className="rounded-md border border-input px-4 py-1.5 text-xs font-semibold hover:bg-muted"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
