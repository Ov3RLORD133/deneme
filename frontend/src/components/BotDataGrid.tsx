/**
 * BotDataGrid Component - Bot List Table
 * 
 * Displays infected bots in a sortable, filterable data grid.
 * Supports clicking rows to open detail drawer.
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { formatDistanceToNow } from 'date-fns';
import { ChevronDown, ChevronUp, Activity, AlertCircle } from 'lucide-react';
import { botsApi } from '@/lib/api';
import type { Bot } from '@/types';

interface BotDataGridProps {
  onBotSelect?: (bot: Bot) => void;
  protocol?: string;
}

type SortField = 'last_seen' | 'ip_address' | 'protocol' | 'bot_id';
type SortDirection = 'asc' | 'desc';

export const BotDataGrid: React.FC<BotDataGridProps> = ({ onBotSelect, protocol }) => {
  const [sortField, setSortField] = useState<SortField>('last_seen');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

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
              <th>Hostname</th>
              <th>Username</th>
              <th>OS</th>
              <th
                className="cursor-pointer hover:text-ops-cyan transition-colors"
                onClick={() => handleSort('last_seen')}
              >
                Last Seen {renderSortIcon('last_seen')}
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedBots.length === 0 ? (
              <tr>
                <td colSpan={8} className="text-center py-8 text-gray-500">
                  No bots detected yet
                </td>
              </tr>
            ) : (
              sortedBots.map((bot) => (
                <tr
                  key={bot.id}
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
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default BotDataGrid;
