/**
 * HexViewer Component - The Analyst View
 * 
 * Advanced hexadecimal viewer for inspecting decrypted malware payloads.
 * Features:
 * - Three-column layout: Offset | Hex Bytes | ASCII
 * - Interactive byte selection
 * - Hover highlighting
 * - Copyable sections
 */

import React, { useState, useCallback, useMemo } from 'react';
import { Copy, Check } from 'lucide-react';

interface HexViewerProps {
  data: Uint8Array | string;
  bytesPerRow?: number;
  className?: string;
  showAscii?: boolean;
  showOffset?: boolean;
}

export const HexViewer: React.FC<HexViewerProps> = ({
  data,
  bytesPerRow = 16,
  className = '',
  showAscii = true,
  showOffset = true,
}) => {
  const [selectedByte, setSelectedByte] = useState<number | null>(null);
  const [hoveredByte, setHoveredByte] = useState<number | null>(null);
  const [copied, setCopied] = useState(false);

  // Convert string to Uint8Array if needed
  const bytes = useMemo(() => {
    if (typeof data === 'string') {
      const encoder = new TextEncoder();
      return encoder.encode(data);
    }
    return data;
  }, [data]);

  // Calculate number of rows
  const rows = Math.ceil(bytes.length / bytesPerRow);

  /**
   * Convert byte to hex string with padding
   */
  const byteToHex = (byte: number): string => {
    return byte.toString(16).toUpperCase().padStart(2, '0');
  };

  /**
   * Convert byte to ASCII character (printable only)
   */
  const byteToAscii = (byte: number): string => {
    return byte >= 32 && byte <= 126 ? String.fromCharCode(byte) : '.';
  };

  /**
   * Handle byte click
   */
  const handleByteClick = useCallback((index: number) => {
    setSelectedByte(index === selectedByte ? null : index);
  }, [selectedByte]);

  /**
   * Copy hex data to clipboard
   */
  const copyToClipboard = useCallback(async () => {
    const hexString = Array.from(bytes)
      .map(byteToHex)
      .join(' ');
    
    try {
      await navigator.clipboard.writeText(hexString);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  }, [bytes]);

  /**
   * Get byte style classes
   */
  const getByteClassName = useCallback((index: number): string => {
    const classes = ['hex-byte'];
    
    if (index === selectedByte) {
      classes.push('selected');
    } else if (index === hoveredByte) {
      classes.push('bg-ops-cyan bg-opacity-10');
    }
    
    return classes.join(' ');
  }, [selectedByte, hoveredByte]);

  /**
   * Render a single row
   */
  const renderRow = (rowIndex: number) => {
    const startIndex = rowIndex * bytesPerRow;
    const endIndex = Math.min(startIndex + bytesPerRow, bytes.length);
    const rowBytes = bytes.slice(startIndex, endIndex);

    return (
      <div key={rowIndex} className="flex font-mono text-xs leading-6 hover:bg-ops-gray hover:bg-opacity-30 transition-colors">
        {/* Offset Column */}
        {showOffset && (
          <div className="text-ops-cyan opacity-60 w-20 flex-shrink-0 select-none">
            {startIndex.toString(16).toUpperCase().padStart(8, '0')}
          </div>
        )}

        {/* Hex Bytes Column */}
        <div className="flex-1 flex flex-wrap gap-1 px-4">
          {Array.from(rowBytes).map((byte, i) => {
            const byteIndex = startIndex + i;
            return (
              <span
                key={i}
                className={getByteClassName(byteIndex)}
                onClick={() => handleByteClick(byteIndex)}
                onMouseEnter={() => setHoveredByte(byteIndex)}
                onMouseLeave={() => setHoveredByte(null)}
                title={`Offset: 0x${byteIndex.toString(16).toUpperCase()}, Decimal: ${byte}, Char: ${byteToAscii(byte)}`}
              >
                {byteToHex(byte)}
              </span>
            );
          })}
          {/* Padding for incomplete rows */}
          {Array.from({ length: bytesPerRow - rowBytes.length }).map((_, i) => (
            <span key={`pad-${i}`} className="hex-byte opacity-0">
              00
            </span>
          ))}
        </div>

        {/* ASCII Column */}
        {showAscii && (
          <div className="w-40 flex-shrink-0 text-ops-green opacity-80 border-l border-ops-border pl-4">
            {Array.from(rowBytes).map((byte, i) => {
              const byteIndex = startIndex + i;
              const char = byteToAscii(byte);
              const isHighlighted = byteIndex === selectedByte || byteIndex === hoveredByte;
              
              return (
                <span
                  key={i}
                  className={`inline-block w-4 text-center ${
                    isHighlighted ? 'text-ops-cyan bg-ops-cyan bg-opacity-20' : ''
                  }`}
                  onClick={() => handleByteClick(byteIndex)}
                  onMouseEnter={() => setHoveredByte(byteIndex)}
                  onMouseLeave={() => setHoveredByte(null)}
                >
                  {char}
                </span>
              );
            })}
          </div>
        )}
      </div>
    );
  };

  if (bytes.length === 0) {
    return (
      <div className={`terminal-output ${className}`}>
        <div className="text-gray-500 text-center py-8">No data to display</div>
      </div>
    );
  }

  return (
    <div className={`terminal-output relative ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4 pb-2 border-b border-ops-border">
        <div className="text-ops-green text-xs uppercase tracking-wider">
          Hex Inspector
          <span className="text-gray-500 ml-2">
            ({bytes.length} bytes)
          </span>
        </div>
        <button
          onClick={copyToClipboard}
          className="ops-button text-xs py-1 px-2 flex items-center gap-1"
          title="Copy hex data"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3" />
              Copied
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              Copy
            </>
          )}
        </button>
      </div>

      {/* Column Headers */}
      <div className="flex font-mono text-[10px] text-gray-500 uppercase tracking-wider mb-2 pb-1 border-b border-ops-border">
        {showOffset && <div className="w-20 flex-shrink-0">Offset</div>}
        <div className="flex-1 px-4">Hex Bytes</div>
        {showAscii && <div className="w-40 flex-shrink-0 border-l border-ops-border pl-4">ASCII</div>}
      </div>

      {/* Hex Data Rows */}
      <div className="overflow-auto max-h-[600px]">
        {Array.from({ length: rows }, (_, i) => renderRow(i))}
      </div>

      {/* Selected Byte Info */}
      {selectedByte !== null && (
        <div className="mt-4 pt-4 border-t border-ops-border text-xs">
          <div className="grid grid-cols-4 gap-4">
            <div>
              <span className="text-gray-500">Offset:</span>
              <span className="ml-2 text-ops-cyan">0x{selectedByte.toString(16).toUpperCase().padStart(8, '0')}</span>
            </div>
            <div>
              <span className="text-gray-500">Hex:</span>
              <span className="ml-2 text-ops-green">0x{byteToHex(bytes[selectedByte])}</span>
            </div>
            <div>
              <span className="text-gray-500">Decimal:</span>
              <span className="ml-2 text-ops-yellow">{bytes[selectedByte]}</span>
            </div>
            <div>
              <span className="text-gray-500">ASCII:</span>
              <span className="ml-2 text-ops-green">{byteToAscii(bytes[selectedByte])}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HexViewer;
