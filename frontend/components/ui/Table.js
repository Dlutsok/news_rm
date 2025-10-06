import React from 'react';

const Table = ({ children, className = '' }) => {
  return (
    <div className="overflow-hidden rounded-xl border border-gray-200">
      <table className={`min-w-full divide-y divide-gray-200 ${className}`}>
        {children}
      </table>
    </div>
  );
};

const TableHeader = ({ children, className = '' }) => {
  return (
    <thead className={`bg-gray-50 ${className}`}>
      {children}
    </thead>
  );
};

const TableBody = ({ children, className = '' }) => {
  return (
    <tbody className={`bg-white divide-y divide-gray-200 ${className}`}>
      {children}
    </tbody>
  );
};

const TableRow = ({ children, className = '', hover = true }) => {
  const hoverClass = hover ? 'hover:bg-gray-50' : '';
  return (
    <tr className={`${hoverClass} ${className}`}>
      {children}
    </tr>
  );
};

const TableHeaderCell = ({ children, className = '', ...props }) => {
  return (
    <th 
      className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${className}`}
      {...props}
    >
      {children}
    </th>
  );
};

const TableCell = ({ children, className = '', ...props }) => {
  return (
    <td className={`px-6 py-4 whitespace-nowrap text-sm text-gray-900 ${className}`} {...props}>
      {children}
    </td>
  );
};

// Экспортируем все компоненты
Table.Header = TableHeader;
Table.Body = TableBody;
Table.Row = TableRow;
Table.HeaderCell = TableHeaderCell;
Table.Cell = TableCell;

export default Table;