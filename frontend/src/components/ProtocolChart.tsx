import { useQuery } from '@tanstack/react-query';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { Activity, AlertCircle } from 'lucide-react';
import { statsApi } from '@/lib/api';

interface ProtocolData {
  name: string;
  value: number;
}

// Cyberpunk color palette for protocols
const PROTOCOL_COLORS = [
  '#00ff41', // ops-green
  '#00f3ff', // ops-cyan
  '#ff0000', // ops-red
  '#ff00ff', // magenta
  '#ffff00', // yellow
  '#ff6600', // orange
  '#00ffaa', // mint
  '#aa00ff', // purple
];

export default function ProtocolChart() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['stats', 'overview'],
    queryFn: statsApi.overview,
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  if (isLoading) {
    return (
      <div className="ops-card p-6 h-full flex items-center justify-center">
        <div className="flex flex-col items-center space-y-3">
          <Activity className="w-8 h-8 text-ops-green animate-pulse" />
          <p className="text-ops-green/60 text-sm font-mono">Loading protocol data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="ops-card p-6 h-full flex items-center justify-center">
        <div className="flex flex-col items-center space-y-3">
          <AlertCircle className="w-8 h-8 text-ops-red" />
          <p className="text-ops-red/80 text-sm font-mono">Failed to load chart data</p>
        </div>
      </div>
    );
  }

  const protocolData: ProtocolData[] = stats?.protocol_distribution || [];

  if (protocolData.length === 0) {
    return (
      <div className="ops-card p-6 h-full flex items-center justify-center">
        <div className="flex flex-col items-center space-y-3 text-center">
          <Activity className="w-12 h-12 text-ops-green/30" />
          <p className="text-ops-green/60 text-sm font-mono">No infection data yet</p>
          <p className="text-ops-green/40 text-xs font-mono">
            Waiting for malware traffic...
          </p>
        </div>
      </div>
    );
  }

  const totalInfections = protocolData.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className="ops-card p-6 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Activity className="w-5 h-5 text-ops-cyan" />
          <h3 className="text-lg font-bold text-ops-green font-mono">
            INFECTION DISTRIBUTION
          </h3>
        </div>
        <div className="px-3 py-1 bg-ops-green/10 rounded border border-ops-green/30">
          <span className="text-ops-green font-mono text-sm font-bold">
            {totalInfections} TOTAL
          </span>
        </div>
      </div>

      {/* Chart */}
      <div className="flex-1 min-h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={protocolData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
              outerRadius={100}
              innerRadius={50}
              fill="#8884d8"
              dataKey="value"
              animationBegin={0}
              animationDuration={800}
            >
              {protocolData.map((entry, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={PROTOCOL_COLORS[index % PROTOCOL_COLORS.length]}
                  stroke="#050505"
                  strokeWidth={2}
                />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#0a0a0a',
                border: '1px solid #00ff41',
                borderRadius: '4px',
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '12px',
              }}
              labelStyle={{ color: '#00ff41' }}
              itemStyle={{ color: '#00f3ff' }}
            />
            <Legend
              verticalAlign="bottom"
              height={36}
              iconType="circle"
              wrapperStyle={{
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '12px',
                color: '#00ff41',
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Protocol Breakdown */}
      <div className="mt-4 space-y-2 border-t border-ops-green/20 pt-4">
        {protocolData.map((protocol, index) => {
          const percentage = ((protocol.value / totalInfections) * 100).toFixed(1);
          return (
            <div key={protocol.name} className="flex items-center justify-between text-sm">
              <div className="flex items-center space-x-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: PROTOCOL_COLORS[index % PROTOCOL_COLORS.length] }}
                />
                <span className="text-ops-green/80 font-mono font-medium">
                  {protocol.name}
                </span>
              </div>
              <div className="flex items-center space-x-3">
                <span className="text-ops-cyan font-mono font-bold">
                  {protocol.value}
                </span>
                <span className="text-ops-green/60 font-mono text-xs w-12 text-right">
                  {percentage}%
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
