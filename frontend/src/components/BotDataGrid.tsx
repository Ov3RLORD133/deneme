/**
 * BotDataGrid Component - Bot List Table
 * 
 * Displays infected bots in a sortable, filterable data grid.
 * Supports clicking rows to open detail drawer.
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { formatDistanceToNow } from 'date-fns';
import { ChevronDown, ChevronUp, Activity, AlertCircle, Download, Shield, Globe, Bug } from 'lucide-react';
import { botsApi } from '@/lib/api';
import type { Bot, BotExtraData } from '@/types';

interface BotDataGridProps {
  onBotSelect?: (bot: Bot) => void;
  protocol?: string;
}

type SortField = 'last_seen' | 'ip_address' | 'protocol' | 'bot_id';
type SortDirection = 'asc' | 'desc';

/**
 * Download forensic data export for a bot
 */
const handleExportBot = async (botId: number, event: React.MouseEvent) => {
  event.stopPropagation(); // Prevent row click
  
  try {
    const response = await fetch(`/api/bots/${botId}/export`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('keychaser_token')}`,
      },
    });
    
    if (!response.ok) {
      throw new Error('Export failed');
    }
    
    // Get filename from Content-Disposition header
    const contentDisposition = response.headers.get('Content-Disposition');
    const filename = contentDisposition
      ? contentDisposition.split('filename=')[1].replace(/"/g, '')
      : `bot_${botId}_export.json`;
    
    // Download file
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (error) {
    console.error('Export failed:', error);
    alert('Failed to export bot data');
  }
};

export const BotDataGrid: React.FC<BotDataGridProps> = ({ onBotSelect, protocol }) => {
  const [sortField, setSortField] = useState<SortField>('last_seen');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [expandedBotId, setExpandedBotId] = useState<number | null>(null);

  // Fetch bots
  const { data: bots = [], isLoading, error } = useQuery({
    queryKey: ['bots', protocol],
    queryFn: () => botsApi.list({ protocol, limit: 100 }),
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  /**
   * Handle column sort
   */
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  /**
   * Sort bots
   */
  const sortedBots = React.useMemo(() => {
    return [...bots].sort((a, b) => {
      let aVal: any = a[sortField];
      let bVal: any = b[sortField];

      // Handle null values
      if (aVal === null) return 1;
      if (bVal === null) return -1;

      // Convert dates to timestamps for comparison
      if (sortField === 'last_seen') {
        aVal = new Date(aVal).getTime();
        bVal = new Date(bVal).getTime();
      }

      if (sortDirection === 'asc') {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });
  }, [bots, sortField, sortDirection]);

  /**
   * Render sort icon
   */
  const renderSortIcon = (field: SortField) => {
    if (sortField !== field) return null;
    return sortDirection === 'asc' ? (
      <ChevronUp className="w-3 h-3 inline ml-1" />
    ) : (
      <ChevronDown className="w-3 h-3 inline ml-1" />
    );
  };

  /**
   * Check if bot is active (last seen < 1 hour ago)
   */
  const isActive = (lastSeen: string): boolean => {
    const hourAgo = Date.now() - 60 * 60 * 1000;
    return new Date(lastSeen).getTime() > hourAgo;
  };

  /**
   * Parse extra_data JSON field
   */
  const parseExtraData = (extraDataStr: string | null): BotExtraData | null => {
    if (!extraDataStr) return null;
    try {
      return JSON.parse(extraDataStr) as BotExtraData;
    } catch {
      return null;
    }
  };

  /**
   * Get risk level badge based on abuse score
   */
  const getRiskBadge = (abuseScore: number) => {
    if (abuseScore === 0) {
      return (
        <span className="px-2 py-1 text-[10px] bg-gray-700 text-gray-400 border border-gray-600 rounded">
          Low
        </span>
      );
    } else if (abuseScore <= 20) {
      return (
        <span className="px-2 py-1 text-[10px] bg-gray-700 text-gray-300 border border-gray-500 rounded">
          Low ({abuseScore}%)
        </span>
      );
    } else if (abuseScore <= 50) {
      return (
        <span className="px-2 py-1 text-[10px] bg-yellow-900/30 text-yellow-400 border border-yellow-600 rounded">
          Medium ({abuseScore}%)
        </span>
      );
    } else {
      return (
        <span className="px-2 py-1 text-[10px] bg-red-900/30 text-red-500 border border-red-600 rounded font-semibold">
          High ({abuseScore}%)
        </span>
      );
    }
  };

  /**
   * Toggle row expansion
   */
  const toggleExpanded = (botId: number, event: React.MouseEvent) => {
    event.stopPropagation();
    setExpandedBotId(expandedBotId === botId ? null : botId);
  };

  if (isLoading) {
    return (
      <div className="ops-card">
        <div className="text-center py-12 text-gray-500">
          <Activity className="w-8 h-8 mx-auto mb-2 animate-spin" />
          Loading bot data...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="ops-card">
        <div className="text-center py-12 text-ops-red">
          <AlertCircle className="w-8 h-8 mx-auto mb-2" />
          Failed to load bots
        </div>
      </div>
    );
  }

  return (
    <div className="ops-card overflow-hidden">
      {/* Header */}
      <div className="ops-card-header mb-4">
        <span>Infected Bots</span>
        <span className="text-gray-500 text-[10px]">
          {sortedBots.length} total
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="data-grid">
          <thead>
            <tr>
              <th className="w-8">Status</th>
              <th
                className="cursor-pointer hover:text-ops-cyan transition-colors"
                onClick={() => handleSort('bot_id')}
              >
                Bot ID {renderSortIcon('bot_id')}
              </th>
              <th
                className="cursor-pointer hover:text-ops-cyan transition-colors"
                onClick={() => handleSort('ip_address')}
              >
                IP Address {renderSortIcon('ip_address')}
              </th>
              <th
                className="cursor-pointer hover:text-ops-cyan transition-colors"
                onClick={() => handleSort('protocol')}
              >
                Protocol {renderSortIcon('protocol')}
              </th>
              <th>Risk Score</th>
              <th>Hostname</th>
              <th>Username</th>
              <th>OS</th>
              <th
                className="cursor-pointer hover:text-ops-cyan transition-colors"
                onClick={() => handleSort('last_seen')}
              >
                Last Seen {renderSortIcon('last_seen')}
              </th>
              <th className="w-20">Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedBots.length === 0 ? (
              <tr>
                <td colSpan={10} className="text-center py-8 text-gray-500">
                  No bots detected yet
                </td>
              </tr>
            ) : (
              sortedBots.map((bot) => {
                const extraData = parseExtraData(bot.extra_data);
                const abuseScore = extraData?.ip_reputation?.abuse_score;
                const isExpanded = expandedBotId === bot.id;

                return (
                  <React.Fragment key={bot.id}>
                    <tr
                      onClick={() => onBotSelect?.(bot)}
                      className="group"
                    >
                      <td>
                        <span
                          className={`status-dot ${
                            isActive(bot.last_seen) ? 'status-active' : 'status-inactive'
                          }`}
                        />
                      </td>
                      <td className="font-semibold text-ops-cyan">
                        {bot.bot_id || `BOT-${bot.id}`}
                      </td>
                      <td className="font-mono text-ops-green">
                        {bot.ip_address}
                      </td>
                      <td>
                        <span className="px-2 py-1 text-[10px] bg-ops-red bg-opacity-20 text-ops-red border border-ops-red rounded">
                          {bot.protocol}
                        </span>
                      </td>
                      <td>
                        {abuseScore !== undefined ? (
                          <div className="flex items-center gap-2">
                            {getRiskBadge(abuseScore)}
                            {extraData && (
                              <button
                                onClick={(e) => toggleExpanded(bot.id, e)}
                                className="p-1 hover:bg-gray-700 rounded transition-colors"
                                title="View intelligence details"
                              >
                                {isExpanded ? (
                                  <ChevronUp className="w-3 h-3 text-gray-400" />
                                ) : (
                                  <ChevronDown className="w-3 h-3 text-gray-400" />
                                )}
                              </button>
                            )}
                          </div>
                        ) : (
                          <span className="text-gray-500 text-xs">N/A</span>
                        )}
                      </td>
                      <td className="text-gray-400">
                        {bot.hostname || '-'}
                      </td>
                      <td className="text-gray-400">
                        {bot.username || '-'}
                      </td>
                      <td className="text-gray-400 text-xs">
                        {bot.os_info || '-'}
                      </td>
                      <td className="text-gray-500 text-xs">
                        {formatDistanceToNow(new Date(bot.last_seen), { addSuffix: true })}
                      </td>
                      <td>
                        <button
                          onClick={(e) => handleExportBot(bot.id, e)}
                          className="p-1.5 hover:bg-ops-green/10 border border-ops-green/30 rounded transition-colors group/btn"
                          title="Export forensic data"
                        >
                          <Download className="w-4 h-4 text-ops-green group-hover/btn:text-ops-cyan" />
                        </button>
                      </td>
                    </tr>
                    {/* Expanded Intelligence Report */}
                    {isExpanded && extraData && (
                      <tr className="bg-gray-800/50">
                        <td colSpan={10} className="p-4">
                          <div className="grid grid-cols-2 gap-4">
                            {/* Network Intelligence */}
                            {extraData.ip_reputation && (
                              <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-4">
                                <div className="flex items-center gap-2 mb-3">
                                  <Globe className="w-4 h-4 text-ops-cyan" />
                                  <h4 className="text-sm font-semibold text-ops-cyan">Network Intelligence</h4>
                                </div>
                                <div className="space-y-2 text-xs">
                                  <div className="flex justify-between">
                                    <span className="text-gray-400">Abuse Score:</span>
                                    <span className={`font-semibold ${
                                      extraData.ip_reputation.abuse_score > 50 
                                        ? 'text-red-500' 
                                        : extraData.ip_reputation.abuse_score > 20 
                                        ? 'text-yellow-400' 
                                        : 'text-gray-300'
                                    }`}>
                                      {extraData.ip_reputation.abuse_score}%
                                    </span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-gray-400">ISP:</span>
                                    <span className="text-white">{extraData.ip_reputation.isp}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-gray-400">Country:</span>
                                    <span className="text-white">{extraData.ip_reputation.country}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-gray-400">Usage Type:</span>
                                    <span className="text-white">{extraData.ip_reputation.usage_type}</span>
                                  </div>
                                  {extraData.ip_reputation.domain && (
                                    <div className="flex justify-between">
                                      <span className="text-gray-400">Domain:</span>
                                      <span className="text-white font-mono text-[10px]">{extraData.ip_reputation.domain}</span>
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}

                            {/* Malware Intelligence */}
                            {extraData.virustotal && (
                              <div className="bg-gray-900/50 border border-gray-700 rounded-lg p-4">
                                <div className="flex items-center gap-2 mb-3">
                                  <Bug className="w-4 h-4 text-ops-red" />
                                  <h4 className="text-sm font-semibold text-ops-red">Malware Intelligence</h4>
                                </div>
                                <div className="space-y-2 text-xs">
                                  <div className="flex justify-between">
                                    <span className="text-gray-400">Detection Ratio:</span>
                                    <span className="font-semibold text-red-500">
                                      {extraData.virustotal.malicious}/{extraData.virustotal.total_vendors} Malicious
                                    </span>
                                  </div>
                                  {extraData.virustotal.detection_names.length > 0 && (
                                    <div>
                                      <span className="text-gray-400 block mb-1">Top Detections:</span>
                                      <div className="space-y-1 ml-2">
                                        {extraData.virustotal.detection_names.slice(0, 5).map((name, idx) => (
                                          <div key={idx} className="text-red-400 font-mono text-[10px]">
                                            • {name}
                                          </div>
                                        ))}
                                        {extraData.virustotal.detection_names.length > 5 && (
                                          <div className="text-gray-500 text-[10px] italic">
                                            +{extraData.virustotal.detection_names.length - 5} more...
                                          </div>
                                        )}
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}

                            {/* No Intelligence Available */}
                            {!extraData.ip_reputation && !extraData.virustotal && (
                              <div className="col-span-2 text-center py-4 text-gray-500 text-sm">
                                <Shield className="w-6 h-6 mx-auto mb-2 opacity-50" />
                                No threat intelligence data available
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default BotDataGrid;
