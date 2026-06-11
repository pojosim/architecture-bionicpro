import React, { useState } from 'react';

const BFF_URL = process.env.REACT_APP_BFF_URL || 'http://localhost:8081';

interface ReportItem {
  date: string;
  total_signals: number;
  avg_amplitude: number | null;
  avg_frequency: number;
  avg_duration: number;
  customer: {
    name: string;
    email: string;
    country: string;
  };
}

interface ReportData {
  user_id: number;
  report: ReportItem[];
  data_up_to: string;
}

const ReportPage: React.FC = () => {
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const downloadReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${BFF_URL}/api/reports`, {
        credentials: 'include',
      });
      if (!response.ok) {
        if (response.status === 401) {
          window.location.href = '/login';
          return;
        }
        throw new Error('Ошибка загрузки отчёта');
      }
      const data = await response.json();
      setReportData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const exportToCSV = () => {
    if (!reportData || !reportData.report.length) return;

    const headers = [
      'Date',
      'Total signals',
      'Avg amplitude',
      'Avg frequency',
      'Avg duration (ms)',
      'Customer name',
      'Customer email',
      'Country',
    ];
    const rows = reportData.report.map((item) => [
      item.date,
      item.total_signals,
      item.avg_amplitude ?? '',
      item.avg_frequency,
      item.avg_duration,
      item.customer.name,
      item.customer.email,
      item.customer.country,
    ]);

    const csvContent = [headers, ...rows]
        .map((row) => row.map((cell) => `"${cell}"`).join(','))
        .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.href = url;
    link.setAttribute('download', `report_${reportData.user_id}_${new Date().toISOString().slice(0, 19)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const logout = async () => {
    try {
      await fetch(`${BFF_URL}/auth/logout`, { method: 'POST', credentials: 'include' });
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      window.location.href = '/login';
    }
  };

  return (
      <div className="min-h-screen bg-gray-100">
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
            <h1 className="text-3xl font-bold text-gray-900">Usage Reports</h1>
            <button
                onClick={logout}
                className="bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded-lg transition"
            >
              Logout
            </button>
          </div>
        </header>

        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-semibold">Prosthesis Report</h2>
                <button
                    onClick={downloadReport}
                    disabled={loading}
                    className={`bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-6 rounded-lg transition ${
                        loading ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                >
                  {loading ? 'Loading...' : 'Download Report'}
                </button>
              </div>

              {error && (
                  <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-lg">{error}</div>
              )}

              {reportData && (
                  <>
                    <div className="mb-4 text-sm text-gray-600">
                      <p><strong>User ID:</strong> {reportData.user_id}</p>
                      <p><strong>Data up to:</strong> {new Date(reportData.data_up_to).toLocaleString()}</p>
                    </div>

                    {reportData.report.length === 0 ? (
                        <p className="text-gray-500">No data found for this user.</p>
                    ) : (
                        <>
                          <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                              <thead className="bg-gray-50">
                              <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Signals</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Amplitude</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Frequency</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Duration (ms)</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Customer</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Country</th>
                              </tr>
                              </thead>
                              <tbody className="bg-white divide-y divide-gray-200">
                              {reportData.report.map((item, idx) => (
                                  <tr key={idx}>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{item.date}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{item.total_signals}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{item.avg_amplitude?.toFixed(2) ?? '-'}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{item.avg_frequency}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{item.avg_duration}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                      {item.customer.name}<br />
                                      <span className="text-xs text-gray-500">{item.customer.email}</span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{item.customer.country}</td>
                                  </tr>
                              ))}
                              </tbody>
                            </table>
                          </div>

                          <div className="mt-6 flex justify-end">
                            <button
                                onClick={exportToCSV}
                                className="bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 rounded-lg transition"
                            >
                              Export as CSV
                            </button>
                          </div>
                        </>
                    )}
                  </>
              )}
            </div>
          </div>
        </main>
      </div>
  );
};

export default ReportPage;