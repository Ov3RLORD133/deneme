/**
 * Main App Component - Entry Point with Authentication
 * 
 * Orchestrates the dashboard layout and primary views with login protection.
 */

import React, { useState } from 'react';
import DashboardLayout from '@/components/DashboardLayout';
import BotDataGrid from '@/components/BotDataGrid';
import LiveTerminal from '@/components/LiveTerminal';
import HexViewer from '@/components/HexViewer';
import { AuthProvider, useAuth, LoginPage } from '@/components/Auth';
import { useQuery } from '@tanstack/react-query';
import { botsApi, statsApi } from '@/lib/api';
import type { Bot } from '@/types';

const DashboardContent: React.FC = () => {
  const [selectedBot, setSelectedBot] = useState<Bot | null>(null);

  // Fetch bots
  const { data: bots = [] } = useQuery({
    queryKey: ['bots'],
    queryFn: () => botsApi.list({ limit: 100 }),
    refetchInterval: 10000,
  });

  // Sample hex data for demonstration
  const sampleHexData = new Uint8Array([
    0x54, 0x45, 0x53, 0x54, 0x2d, 0x42, 0x4f, 0x54,
    0x2d, 0x30, 0x30, 0x31, 0x7c, 0x56, 0x49, 0x43,
    0x54, 0x49, 0x4d, 0x2d, 0x50, 0x43, 0x7c, 0x6a,
    0x6f, 0x68, 0x6e, 0x2e, 0x64, 0x6f, 0x65, 0x7c,
  ]);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Top Row: Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Map */}
          <div className="md:col-span-2">
            <InfectionMap bots={bots} />
          </div>

          {/* Quick Stats */}
          <div className="space-y-4">
            <div className="ops-card">
              <div className="ops-card-header">
                  <span className="text-lg font-bold text-ops-green">1</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">Uptime</span>
                  <span className="text-lg font-bold text-ops-cyan">24h 15m</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">Traffic</span>
                  <span className="text-lg font-bold text-ops-yellow">1.2 GB</span>
                </div>
              </div>
            </div>

            <div className="ops-card">
              <div className="ops-card-header">
                <span>Top Protocols</span>
              </div>
              <div className="space-y-2 mt-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-ops-red">ExampleLogger</span>
                  <span className="text-gray-400">{bots.length}</span>
                </div>
                <div className="w-full bg-ops-black rounded-full h-1.5">
                  <div
                    className="bg-ops-red h-1.5 rounded-full"
                    style={{ width: '100%' }}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Middle Row: Bot Grid */}
        <div>
          <BotDataGrid onBotSelect={setSelectedBot} />

          {/* Additional Stats Panel */}
          <div className="md:col-span-2">
            <div className="ops-card h-full">
              <div className="ops-card-header">
                <span>System Overview</span>
              </div>
              <div className="grid grid-cols-2 gap-6 mt-6">
                <div className="text-center p-6 bg-ops-black rounded border border-ops-border">
                  <div className="text-4xl font-bold text-ops-green mb-2">{bots.length}</div>
                  <div className="text-sm text-gray-400">Total Infections</div>
                </div>
                <div className="text-center p-6 bg-ops-black rounded border border-ops-border">
                  <div className="text-4xl font-bold text-ops-red mb-2">
                    {bots.filter(b => b.protocol === 'AgentTesla').length}
                  </div>
                  <div className="text-sm text-gray-400">AgentTesla Detections</div>
                </div>
                <div className="text-center p-6 bg-ops-black rounded border border-ops-border">
                  <div className="text-4xl font-bold text-ops-cyan mb-2">
                    {new Set(bots.map(b => b.ip_address)).size}
                  </div>
                  <div className="text-sm text-gray-400">Unique IPs</div>
                </div>
                <div className="text-center p-6 bg-ops-black rounded border border-ops-border">
                  <div className="text-4xl font-bold text-ops-yellow mb-2">1</div>
                  <div className="text-sm text-gray-400">Active Protocols</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Row: Hex Viewer & Terminal */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <HexViewer
            data={sampleHexData}
            className="min-h-[400px]"
          />
          <LiveTerminal />
        </div>

        {/* Bot Details Drawer (if bot selected) */}
        {selectedBot && (
          <div className="fixed inset-0 bg-black bg-opacity-80 z-50 flex items-center justify-center p-6">
            <div className="bg-ops-gray border border-ops-border rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6 border-b border-ops-border flex items-center justify-between">
                <h3 className="text-xl font-bold text-ops-green">
                  Bot Details: {selectedBot.bot_id || `BOT-${selectedBot.id}`}
                </h3>
                <button
                  onClick={() => setSelectedBot(null)}
                  className="ops-button-danger"
                >
                  Close
                </button>
              </div>
              
              <div className="p-6 space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">IP Address:</span>
                    <span className="ml-2 text-ops-green font-mono">{selectedBot.ip_address}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Protocol:</span>
                    <span className="ml-2 text-ops-red">{selectedBot.protocol}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Hostname:</span>
                    <span className="ml-2">{selectedBot.hostname || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Username:</span>
                    <span className="ml-2">{selectedBot.username || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">OS:</span>
                    <span className="ml-2">{selectedBot.os_info || 'N/A'}</span>
                  </div>
                  <div>
                    <span className="text-gray-500">First Seen:</span>
                    <span className="ml-2">{new Date(selectedBot.first_seen).toLocaleString()}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

// Main App with Authentication
const App: React.FC = () => {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return <DashboardContent />;
};

// Wrap with Auth Provider
const AppWithAuth: React.FC = () => (
  <AuthProvider>
    <App />
  </AuthProvider>
);

export default AppWithAuth;
