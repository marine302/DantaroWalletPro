'use client';

import { useState, useEffect } from 'react';
import { Button, Section } from '@/components/ui/DarkThemeComponents';
import { Badge } from '@/components/ui/Badge';
import { AuditLog, AuditEventType } from '@/types/audit';

interface AuditLogFilters {
  dateFrom: string;
  dateTo: string;
  eventType: AuditEventType | 'all';
  severity: string;
  entityType: string;
  userId: string;
  partnerId: string;
  keyword: string;
  riskLevel: string;
  status: string;
}

interface SearchResult {
  logs: AuditLog[];
  total: number;
  page: number;
  totalPages: number;
}

export function AuditLogSearch() {
  const [filters, setFilters] = useState<AuditLogFilters>({
    dateFrom: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 7일 전
    dateTo: new Date().toISOString().split('T')[0], // 오늘
    eventType: 'all',
    severity: 'all',
    entityType: 'all',
    userId: '',
    partnerId: '',
    keyword: '',
    riskLevel: 'all',
    status: 'all'
  });

  const [searchResults, setSearchResults] = useState<SearchResult>({
    logs: [],
    total: 0,
    page: 1,
    totalPages: 0
  });

  const [isSearching, setIsSearching] = useState(false);
  const [exportFormat, setExportFormat] = useState<'csv' | 'excel' | 'json'>('csv');
  const [advancedMode, setAdvancedMode] = useState(false);

  // Mock data for development
  const mockLogs: AuditLog[] = [
    {
      id: 1,
      timestamp: new Date('2025-01-20T10:30:00Z'),
      event_type: AuditEventType.TRANSACTION_COMPLETED,
      event_category: 'transaction',
      severity: 'info',
      entity_type: 'transaction',
      entity_id: 'tx_123456789',
      partner_id: 1,
      user_id: 101,
      event_data: {
        amount: 50000,
        currency: 'USDT',
        fee: 25,
        from_address: '0x1234...5678',
        to_address: '0x8765...4321'
      },
      ip_address: '192.168.1.100',
      user_agent: 'Mozilla/5.0...',
      log_hash: 'abc123def456'
    },
    {
      id: 2,
      timestamp: new Date('2025-01-20T09:45:00Z'),
      event_type: AuditEventType.SUSPICIOUS_ACTIVITY,
      event_category: 'compliance',
      severity: 'critical',
      entity_type: 'user',
      entity_id: 'user_987654321',
      user_id: 102,
      event_data: {
        detection_type: 'velocity_anomaly',
        risk_score: 95,
        pattern: 'rapid_large_transfers',
        flagged_amount: 250000
      },
      ip_address: '10.0.0.50'
    },
    {
      id: 3,
      timestamp: new Date('2025-01-20T08:15:00Z'),
      event_type: AuditEventType.COMPLIANCE_CHECK,
      event_category: 'compliance',
      severity: 'warning',
      entity_type: 'transaction',
      entity_id: 'tx_555666777',
      event_data: {
        check_type: 'aml_screening',
        result: 'requires_review',
        sanctions_match: false,
        pep_match: true
      },
      ip_address: '127.0.0.1'
    }
  ];

  async function handleSearch() {
    setIsSearching(true);

    try {
      // TODO: 실제 API 호출로 교체
      await new Promise(resolve => setTimeout(resolve, 1000)); // Mock delay

      // 필터링 로직 (실제 구현에서는 백엔드에서 처리)
      const _filteredLogs = mockLogs.filter(log => {
        const _logDate = log.timestamp.toISOString().split('T')[0];

        // 날짜 필터
        if (logDate < filters.dateFrom || logDate > filters.dateTo) return false;

        // 이벤트 타입 필터
        if (filters.eventType !== 'all' && log.event_type !== filters.eventType) return false;

        // 심각도 필터
        if (filters.severity !== 'all' && log.severity !== filters.severity) return false;

        // 엔티티 타입 필터
        if (filters.entityType !== 'all' && log.entity_type !== filters.entityType) return false;

        // 키워드 검색
        if (filters.keyword) {
          const _keyword = filters.keyword.toLowerCase();
          const _searchableText = [
            log.entity_id,
            log.event_category,
            JSON.stringify(log.event_data),
            log.ip_address || ''
          ].join(' ').toLowerCase();

          if (!searchableText.includes(keyword)) return false;
        }

        return true;
      });

      setSearchResults({
        logs: filteredLogs.slice(0, 50), // 페이지네이션 구현 예정
        total: filteredLogs.length,
        page: 1,
        totalPages: Math.ceil(filteredLogs.length / 50)
      });

    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  }

  async function handleExport() {
    try {
      const _data = searchResults.logs.map(log => ({
        timestamp: log.timestamp.toISOString(),
        event_type: log.event_type,
        severity: log.severity,
        entity_type: log.entity_type,
        entity_id: log.entity_id,
        user_id: log.user_id,
        partner_id: log.partner_id,
        ip_address: log.ip_address,
        event_data: JSON.stringify(log.event_data)
      }));

      if (exportFormat === 'csv') {
        const _csv = convertToCSV(data);
        downloadFile(csv, 'audit_logs.csv', 'text/csv');
      } else if (exportFormat === 'json') {
        const _json = JSON.stringify(data, null, 2);
        downloadFile(json, 'audit_logs.json', 'application/json');
      }

      alert(`✅ Exported ${data.length} records as ${exportFormat.toUpperCase()}`);
    } catch (error) {
      console.error('Export failed:', error);
      alert('❌ Export failed');
    }
  }

  function convertToCSV(data: any[]) {
    if (data.length === 0) return '';

    const _headers = Object.keys(data[0]);
    const _csvRows = [
      headers.join(','),
      ...data.map(row =>
        headers.map(header => {
          const _value = row[header];
          return typeof value === 'string' && value.includes(',')
            ? `"${value}"`
            : value;
        }).join(',')
      )
    ];

    return csvRows.join('\n');
  }

  function downloadFile(content: string, filename: string, mimeType: string) {
    const _blob = new Blob([content], { type: mimeType });
    const _url = URL.createObjectURL(blob);
    const _link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  function getSeverityColor(severity: string) {
    switch (severity) {
      case 'info': return 'bg-blue-900/30 text-blue-300';
      case 'warning': return 'bg-yellow-900/30 text-yellow-300';
      case 'critical': return 'bg-red-900/30 text-red-300';
      default: return 'bg-gray-900/30 text-gray-300';
    }
  }

  function getCategoryColor(category: string) {
    switch (category) {
      case 'transaction': return 'bg-green-900/30 text-green-300';
      case 'compliance': return 'bg-orange-900/30 text-orange-300';
      case 'security': return 'bg-red-900/30 text-red-300';
      default: return 'bg-gray-900/30 text-gray-300';
    }
  }

  useEffect(() => {
    // 초기 검색
    handleSearch();
  }, []);

  return (
    <Section title="감사 로그 검색">
      <div className="space-y-6">
        {/* 헤더 */}
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-semibold text-white">
              🔍 감사 로그 검색
            </h3>
            <p className="text-sm text-gray-400 mt-1">
              Advanced search and filtering for audit logs and compliance records
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => setAdvancedMode(!advancedMode)}
              className={`${advancedMode ? 'bg-blue-600' : 'bg-gray-600'}`}
            >
              {advancedMode ? '📊 Advanced' : '🔍 Basic'}
            </Button>
            <Button
              onClick={handleExport}
              className="bg-green-600 hover:bg-green-700"
              disabled={searchResults.logs.length === 0}
            >
              📥 Export
            </Button>
          </div>
        </div>

        {/* 검색 필터 */}
        <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* 날짜 범위 */}
            <div>
              <label className="block text-sm text-gray-300 mb-1">From Date</label>
              <input
                type="date"
                value={filters.dateFrom}
                onChange={(e) => setFilters({...filters, dateFrom: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-300 mb-1">To Date</label>
              <input
                type="date"
                value={filters.dateTo}
                onChange={(e) => setFilters({...filters, dateTo: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm"
              />
            </div>

            {/* 이벤트 타입 */}
            <div>
              <label className="block text-sm text-gray-300 mb-1">Event Type</label>
              <select
                value={filters.eventType}
                onChange={(e) => setFilters({...filters, eventType: e.target.value as any})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm"
              >
                <option value="all">All Events</option>
                {Object.values(AuditEventType).map(type => (
                  <option key={type} value={type}>{type.replace('_', ' ')}</option>
                ))}
              </select>
            </div>

            {/* 심각도 */}
            <div>
              <label className="block text-sm text-gray-300 mb-1">Severity</label>
              <select
                value={filters.severity}
                onChange={(e) => setFilters({...filters, severity: e.target.value})}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm"
              >
                <option value="all">All Levels</option>
                <option value="info">Info</option>
                <option value="warning">Warning</option>
                <option value="critical">Critical</option>
              </select>
            </div>

            {advancedMode && (
              <>
                {/* 엔티티 타입 */}
                <div>
                  <label className="block text-sm text-gray-300 mb-1">Entity Type</label>
                  <select
                    value={filters.entityType}
                    onChange={(e) => setFilters({...filters, entityType: e.target.value})}
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm"
                  >
                    <option value="all">All Types</option>
                    <option value="transaction">Transaction</option>
                    <option value="user">User</option>
                    <option value="wallet">Wallet</option>
                    <option value="partner">Partner</option>
                  </select>
                </div>

                {/* User ID */}
                <div>
                  <label className="block text-sm text-gray-300 mb-1">User ID</label>
                  <input
                    type="text"
                    value={filters.userId}
                    onChange={(e) => setFilters({...filters, userId: e.target.value})}
                    placeholder="Enter User ID"
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm"
                  />
                </div>

                {/* Partner ID */}
                <div>
                  <label className="block text-sm text-gray-300 mb-1">Partner ID</label>
                  <input
                    type="text"
                    value={filters.partnerId}
                    onChange={(e) => setFilters({...filters, partnerId: e.target.value})}
                    placeholder="Enter Partner ID"
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm"
                  />
                </div>

                {/* Export Format */}
                <div>
                  <label className="block text-sm text-gray-300 mb-1">Export Format</label>
                  <select
                    value={exportFormat}
                    onChange={(e) => setExportFormat(e.target.value as any)}
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm"
                  >
                    <option value="csv">CSV</option>
                    <option value="excel">Excel</option>
                    <option value="json">JSON</option>
                  </select>
                </div>
              </>
            )}

            {/* 키워드 검색 */}
            <div className="md:col-span-2">
              <label className="block text-sm text-gray-300 mb-1">Keyword Search</label>
              <input
                type="text"
                value={filters.keyword}
                onChange={(e) => setFilters({...filters, keyword: e.target.value})}
                placeholder="Search in entity IDs, categories, event data..."
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white text-sm"
              />
            </div>

            {/* 검색 버튼 */}
            <div className="flex items-end">
              <Button
                onClick={handleSearch}
                disabled={isSearching}
                className="w-full bg-blue-600 hover:bg-blue-700"
              >
                {isSearching ? '🔄 Searching...' : '🔍 Search'}
              </Button>
            </div>
          </div>
        </div>

        {/* 검색 결과 */}
        <div className="bg-gray-900/50 border border-gray-700 rounded-lg">
          <div className="p-4 border-b border-gray-700 flex justify-between items-center">
            <h4 className="font-semibold text-white">
              📋 Search Results ({searchResults.total} records)
            </h4>
            {searchResults.total > 0 && (
              <span className="text-sm text-gray-400">
                Page {searchResults.page} of {searchResults.totalPages}
              </span>
            )}
          </div>

          <div className="max-h-96 overflow-y-auto">
            {searchResults.logs.length === 0 ? (
              <div className="p-8 text-center text-gray-400">
                {isSearching ? '🔄 Searching...' : 'No audit logs found matching your criteria'}
              </div>
            ) : (
              <div className="divide-y divide-gray-700">
                {searchResults.logs.map((log) => (
                  <div key={log.id} className="p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center gap-2">
                        <Badge className={getSeverityColor(log.severity)}>
                          {log.severity.toUpperCase()}
                        </Badge>
                        <Badge className={getCategoryColor(log.event_category)}>
                          {log.event_category.toUpperCase()}
                        </Badge>
                        <span className="text-xs text-gray-400">
                          {log.timestamp.toLocaleString()}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500 font-mono">
                        ID: {log.id}
                      </span>
                    </div>

                    <div className="space-y-1">
                      <p className="text-sm text-white">
                        <span className="font-medium">{log.event_type.replace('_', ' ')}</span>
                        {' → '}
                        <span className="font-mono">{log.entity_type}:{log.entity_id}</span>
                      </p>

                      {log.user_id && (
                        <p className="text-xs text-gray-400">
                          User: {log.user_id} | Partner: {log.partner_id || 'N/A'} | IP: {log.ip_address || 'N/A'}
                        </p>
                      )}

                      <details className="text-xs">
                        <summary className="text-gray-400 cursor-pointer hover:text-gray-300">
                          📄 Event Data
                        </summary>
                        <pre className="mt-2 p-2 bg-gray-800 rounded text-gray-300 overflow-x-auto">
                          {JSON.stringify(log.event_data, null, 2)}
                        </pre>
                      </details>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </Section>
  );
}
