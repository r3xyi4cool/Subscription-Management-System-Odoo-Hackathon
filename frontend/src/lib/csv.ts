/**
 * Utility to export an array of records to a CSV file.
 */

export function exportToCSV<T extends Record<string, unknown>>(
  filename: string,
  rows: T[],
  columnHeaders?: Record<keyof T | string, string>
): void {
  if (!rows || rows.length === 0) {
    alert('No data to export');
    return;
  }

  const keys = columnHeaders ? Object.keys(columnHeaders) : Object.keys(rows[0]);
  const headerRow = columnHeaders
    ? Object.values(columnHeaders).map(escapeCsvValue).join(',')
    : keys.map(escapeCsvValue).join(',');

  const csvRows = rows.map((row) => {
    return keys
      .map((k) => {
        const val = row[k];
        if (val === null || val === undefined) return '""';
        if (typeof val === 'object') return escapeCsvValue(JSON.stringify(val));
        return escapeCsvValue(String(val));
      })
      .join(',');
  });

  const csvContent = [headerRow, ...csvRows].join('\r\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', `${filename.replace(/\.csv$/, '')}_${new Date().toISOString().split('T')[0]}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

function escapeCsvValue(val: string): string {
  if (val.includes('"') || val.includes(',') || val.includes('\n') || val.includes('\r')) {
    return `"${val.replace(/"/g, '""')}"`;
  }
  return `"${val}"`;
}
