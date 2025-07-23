'use client';

import { useState } from 'react';
import { Button, Section } from '@/components/ui/DarkThemeComponents';
import { Badge } from '@/components/ui/Badge';

interface EmergencyAction {
  id: string;
  type: 'block_transaction' | 'freeze_account' | 'suspend_partner' | 'emergency_halt';
  target_id: string;
  target_type: 'transaction' | 'account' | 'partner' | 'system';
  reason: string;
  timestamp: Date;
  executed_by: string;
  status: 'pending' | 'executed' | 'cancelled';
  impact_level: 'low' | 'medium' | 'high' | 'critical';
}

interface BlockingPanelProps {
  onAction?: (action: EmergencyAction) => void;
}

export function EmergencyBlockingPanel({ onAction }: BlockingPanelProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [actionType, setActionType] = useState<EmergencyAction['type']>('block_transaction');
  const [targetId, setTargetId] = useState('');
  const [reason, setReason] = useState('');
  const [recentActions, setRecentActions] = useState<EmergencyAction[]>([
    {
      id: '1',
      type: 'block_transaction',
      target_id: 'tx_123456789',
      target_type: 'transaction',
      reason: 'Suspicious large transfer pattern detected',
      timestamp: new Date(Date.now() - 300000), // 5분 전
      executed_by: 'admin@system.com',
      status: 'executed',
      impact_level: 'medium'
    },
    {
      id: '2',
      type: 'freeze_account',
      target_id: 'acc_987654321',
      target_type: 'account',
      reason: 'Multiple failed KYC verification attempts',
      timestamp: new Date(Date.now() - 1800000), // 30분 전
      executed_by: 'security@system.com',
      status: 'executed',
      impact_level: 'high'
    }
  ]);

  const _actionTypes = [
    { value: 'block_transaction', label: '🚫 Block Transaction', impact: 'medium' },
    { value: 'freeze_account', label: '🧊 Freeze Account', impact: 'high' },
    { value: 'suspend_partner', label: '⏸️ Suspend Partner', impact: 'critical' },
    { value: 'emergency_halt', label: '🛑 Emergency System Halt', impact: 'critical' }
  ];

  const _reasonTemplates = [
    'Suspicious transaction pattern detected',
    'AML/KYC compliance violation',
    'Large amount threshold exceeded',
    'Multiple failed verification attempts',
    'Potential fraud activity detected',
    'Regulatory compliance requirement',
    'Security breach suspected',
    'System integrity compromise'
  ];

  function executeEmergencyAction() {
    if (!targetId || !reason) {
      alert('Please provide target ID and reason');
      return;
    }

    const action: EmergencyAction = {
      id: `emergency_${Date.now()}`,
      type: actionType,
      target_id: targetId,
      target_type: getTargetType(actionType),
      reason,
      timestamp: new Date(),
      executed_by: 'current_admin@system.com', // TODO: 실제 로그인 사용자
      status: 'executed',
      impact_level: getImpactLevel(actionType)
    };

    setRecentActions(prev => [action, ...prev]);

    if (onAction) {
      onAction(action);
    }

    // 성공 알림
    alert(`✅ Emergency action executed: ${actionType} for ${targetId}`);

    // 폼 리셋
    setTargetId('');
    setReason('');
    setIsModalOpen(false);
  }

  function getTargetType(actionType: EmergencyAction['type']): EmergencyAction['target_type'] {
    switch (actionType) {
      case 'block_transaction': return 'transaction';
      case 'freeze_account': return 'account';
      case 'suspend_partner': return 'partner';
      case 'emergency_halt': return 'system';
      default: return 'transaction';
    }
  }

  function getImpactLevel(actionType: EmergencyAction['type']): EmergencyAction['impact_level'] {
    switch (actionType) {
      case 'block_transaction': return 'medium';
      case 'freeze_account': return 'high';
      case 'suspend_partner': return 'critical';
      case 'emergency_halt': return 'critical';
      default: return 'medium';
    }
  }

  function getStatusColor(status: string) {
    switch (status) {
      case 'executed': return 'bg-red-900/30 text-red-300';
      case 'pending': return 'bg-yellow-900/30 text-yellow-300';
      case 'cancelled': return 'bg-gray-900/30 text-gray-300';
      default: return 'bg-blue-900/30 text-blue-300';
    }
  }

  function getImpactColor(level: string) {
    switch (level) {
      case 'low': return 'bg-green-900/30 text-green-300';
      case 'medium': return 'bg-yellow-900/30 text-yellow-300';
      case 'high': return 'bg-orange-900/30 text-orange-300';
      case 'critical': return 'bg-red-900/30 text-red-300';
      default: return 'bg-gray-900/30 text-gray-300';
    }
  }

  return (
    <Section title="긴급 차단 패널">
      <div className="space-y-6">
        {/* 헤더 */}
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-semibold text-white">
              🚨 긴급 차단 패널
            </h3>
            <p className="text-sm text-gray-400 mt-1">
              Critical security actions and immediate response controls
            </p>
          </div>
          <Button
            onClick={() => setIsModalOpen(true)}
            className="bg-red-600 hover:bg-red-700"
          >
            🚨 EMERGENCY ACTION
          </Button>
        </div>

        {/* 빠른 액션 버튼들 */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {actionTypes.map((action) => (
            <Button
              key={action.value}
              onClick={() => {
                setActionType(action.value as EmergencyAction['type']);
                setIsModalOpen(true);
              }}
              className={`h-16 text-xs ${
                action.impact === 'critical' ? 'bg-red-700 hover:bg-red-800' :
                action.impact === 'high' ? 'bg-orange-700 hover:bg-orange-800' :
                'bg-yellow-700 hover:bg-yellow-800'
              }`}
            >
              <div className="text-center">
                <div>{action.label}</div>
                <div className="text-xs opacity-75">({action.impact})</div>
              </div>
            </Button>
          ))}
        </div>

        {/* 최근 액션 히스토리 */}
        <div className="bg-gray-900/50 border border-gray-700 rounded-lg">
          <div className="p-4 border-b border-gray-700">
            <h4 className="font-semibold text-white">📋 Recent Emergency Actions</h4>
          </div>
          <div className="divide-y divide-gray-700">
            {recentActions.length === 0 ? (
              <div className="p-6 text-center text-gray-400">
                No emergency actions recorded
              </div>
            ) : (
              recentActions.map((action) => (
                <div key={action.id} className="p-4">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge className={getStatusColor(action.status)}>
                          {action.status.toUpperCase()}
                        </Badge>
                        <Badge className={getImpactColor(action.impact_level)}>
                          {action.impact_level.toUpperCase()}
                        </Badge>
                        <span className="text-xs text-gray-400">
                          {action.timestamp.toLocaleString()}
                        </span>
                      </div>
                      <p className="text-sm text-white font-medium">
                        {action.type.replace('_', ' ').toUpperCase()}: {action.target_id}
                      </p>
                      <p className="text-xs text-gray-400 mt-1">
                        Reason: {action.reason}
                      </p>
                      <p className="text-xs text-gray-500">
                        Executed by: {action.executed_by}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* 모달 */}
        {isModalOpen && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 w-full max-w-md">
              <h3 className="text-lg font-semibold text-white mb-4">
                🚨 Execute Emergency Action
              </h3>

              <div className="space-y-4">
                {/* Action Type */}
                <div>
                  <label className="block text-sm text-gray-300 mb-2">Action Type</label>
                  <select
                    value={actionType}
                    onChange={(e) => setActionType(e.target.value as EmergencyAction['type'])}
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  >
                    {actionTypes.map((action) => (
                      <option key={action.value} value={action.value}>
                        {action.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Target ID */}
                <div>
                  <label className="block text-sm text-gray-300 mb-2">
                    Target ID ({getTargetType(actionType)})
                  </label>
                  <input
                    type="text"
                    value={targetId}
                    onChange={(e) => setTargetId(e.target.value)}
                    placeholder={`Enter ${getTargetType(actionType)} ID`}
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white"
                  />
                </div>

                {/* Reason */}
                <div>
                  <label className="block text-sm text-gray-300 mb-2">Reason</label>
                  <select
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white mb-2"
                  >
                    <option value="">Select reason template</option>
                    {reasonTemplates.map((template, idx) => (
                      <option key={idx} value={template}>
                        {template}
                      </option>
                    ))}
                  </select>
                  <textarea
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    placeholder="Provide detailed reason for this emergency action"
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white h-20 text-sm"
                  />
                </div>

                {/* Warning */}
                <div className="bg-red-900/20 border border-red-700/30 rounded p-3">
                  <p className="text-red-300 text-xs">
                    ⚠️ This action will be logged and may have immediate impact on system operations.
                    Make sure you have proper authorization.
                  </p>
                </div>

                {/* Buttons */}
                <div className="flex gap-3 pt-4">
                  <Button
                    onClick={() => setIsModalOpen(false)}
                    className="flex-1 bg-gray-600 hover:bg-gray-700"
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={executeEmergencyAction}
                    className="flex-1 bg-red-600 hover:bg-red-700"
                    disabled={!targetId || !reason}
                  >
                    🚨 EXECUTE
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Section>
  );
}
