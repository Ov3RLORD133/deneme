/**
 * DashboardLayout Component - Main Application Layout
 * 
 * Provides the top-level structure with sidebar navigation,
 * header, and main content area.
 */

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Activity,
  Database,
  FileText,
  Key,
  Map,
  Terminal,
  Settings,
  Shield,
} from 'lucide-react';
import { statsApi } from '@/lib/api';
import { useKeyChaserSocket } from '@/hooks/useKeyChaserSocket';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

type NavItem = {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
};

const navItems: NavItem[] = [
  { id: 'overview', label: 'Overview', icon: Activity },
  { id: 'bots', label: 'Bots', icon: Database },
  { id: 'logs', label: 'Logs', icon: FileText },
  { id: 'credentials', label: 'Credentials', icon: Key },
  { id: 'map', label: 'Map', icon: Map },
  { id: 'terminal', label: 'Terminal', icon: Terminal },
  { id: 'settings', label: 'Settings', icon: Settings },
];

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  const [activeNav, setActiveNav] = useState('overview');
  const { isConnected } = useKeyChaserSocket();

  // Fetch overview stats
  const { data: stats } = useQuery({
    queryKey: ['stats', 'overview'],
    queryFn: () => statsApi.overview(),
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  return (
    <div className="flex h-screen overflow-hidden bg-ops-black">
      {/* Sidebar */}
      <aside className="w-64 bg-ops-gray border-r border-ops-border flex flex-col">
        {/* Logo */}
        <div className="p-6 border-b border-ops-border">
          <div className="flex items-center gap-3">
            <Shield className="w-8 h-8 text-ops-red" />
            <div>
              <h1 className="text-lg font-bold text-ops-green glow-green">
                KeyChaser
              </h1>
              <p className="text-[10px] text-gray-500 uppercase tracking-wider">
                Operator Console
              </p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => setActiveNav(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded transition-all ${
                  activeNav === item.id
                    ? 'bg-ops-black border-l-2 border-ops-green text-ops-green'
                    : 'text-gray-400 hover:text-ops-green hover:bg-ops-black'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span className="text-sm">{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Stats Summary */}
        <div className="p-4 border-t border-ops-border space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-500">Total Bots</span>
            <span className="text-ops-green font-semibold">
              {stats?.total_bots || 0}
            </span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-500">Active</span>
            <span className="text-ops-green font-semibold">
              {stats?.active_bots || 0}
            </span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-gray-500">Credentials</span>
            <span className="text-ops-yellow font-semibold">
              {stats?.total_credentials || 0}
            </span>
          </div>
        </div>

        {/* Connection Status */}
        <div className="p-4 border-t border-ops-border">
          <div className="flex items-center gap-2 text-xs">
            <span
              className={`status-dot ${
                isConnected ? 'status-active' : 'status-inactive'
              }`}
            />
            <span className="text-gray-500">
              {isConnected ? 'Stream Connected' : 'Stream Offline'}
            </span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-ops-gray border-b border-ops-border px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-ops-green uppercase tracking-wider">
                {navItems.find((item) => item.id === activeNav)?.label || 'Dashboard'}
              </h2>
              <p className="text-xs text-gray-500 mt-1">
                Real-time malware C2 traffic analysis
              </p>
            </div>

            {/* System Status */}
            <div className="flex items-center gap-6">
              {/* Protocols */}
              <div className="text-right">
                <div className="text-[10px] text-gray-500 uppercase">Protocols</div>
                <div className="text-sm font-semibold text-ops-cyan">
                  {stats ? Object.keys(stats.protocols).length : 0}
                </div>
              </div>

              {/* Logs */}
              <div className="text-right">
                <div className="text-[10px] text-gray-500 uppercase">Logs</div>
                <div className="text-sm font-semibold text-ops-green">
                  {stats?.total_logs.toLocaleString() || 0}
                </div>
              </div>

              {/* System Time */}
              <div className="text-right">
                <div className="text-[10px] text-gray-500 uppercase">System Time</div>
                <div className="text-sm font-mono text-gray-300">
                  {new Date().toLocaleTimeString()}
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Content Area */}
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
