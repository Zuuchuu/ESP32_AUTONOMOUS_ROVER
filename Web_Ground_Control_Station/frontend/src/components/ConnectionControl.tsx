/**
 * Connection Control Component
 * 
 * Allows user to input rover IP and port, then connect/disconnect.
 */

import { useState } from 'react';

interface ConnectionControlProps {
    onConnect: (host: string, port: number) => Promise<any>;
    onDisconnect: () => Promise<any>;
    isConnected: boolean;
}

export function ConnectionControl({ onConnect, onDisconnect, isConnected }: ConnectionControlProps) {
    const [host, setHost] = useState('192.168.1.100');
    const [port, setPort] = useState('8080');
    const [isConnecting, setIsConnecting] = useState(false);

    const handleConnect = async () => {
        if (isConnecting) return;

        setIsConnecting(true);
        try {
            const portNum = parseInt(port, 10);
            if (isNaN(portNum) || portNum < 1 || portNum > 65535) {
                alert('Invalid port number');
                return;
            }

            const result = await onConnect(host, portNum);
            if (!result.success) {
                alert(result.message || 'Connection failed');
            }
        } catch (error) {
            console.error('Connection error:', error);
            alert('Failed to connect to rover');
        } finally {
            setIsConnecting(false);
        }
    };

    const handleDisconnect = async () => {
        if (isConnecting) return;

        setIsConnecting(true);
        try {
            await onDisconnect();
        } catch (error) {
            console.error('Disconnect error:', error);
        } finally {
            setIsConnecting(false);
        }
    };

    return (
        <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 px-2 py-1 bg-gcs-dark/80 border border-gcs-border rounded-lg">
                <input
                    type="text"
                    value={host}
                    onChange={(e) => setHost(e.target.value)}
                    placeholder="192.168.1.100"
                    disabled={isConnected}
                    className="w-28 bg-transparent text-white text-xs outline-none placeholder-slate-500 disabled:opacity-50"
                />
                <span className="text-slate-500 text-xs">:</span>
                <input
                    type="text"
                    value={port}
                    onChange={(e) => setPort(e.target.value)}
                    placeholder="8080"
                    disabled={isConnected}
                    className="w-12 bg-transparent text-white text-xs outline-none placeholder-slate-500 disabled:opacity-50"
                />
            </div>

            {isConnected ? (
                <button
                    onClick={handleDisconnect}
                    disabled={isConnecting}
                    className="px-3 py-1 bg-gcs-danger hover:bg-gcs-danger/80 text-white text-xs font-medium rounded-lg transition-colors disabled:opacity-50"
                >
                    {isConnecting ? 'Disconnecting...' : 'Disconnect'}
                </button>
            ) : (
                <button
                    onClick={handleConnect}
                    disabled={isConnecting}
                    className="px-3 py-1 bg-gcs-success hover:bg-gcs-success/80 text-white text-xs font-medium rounded-lg transition-colors disabled:opacity-50"
                >
                    {isConnecting ? 'Connecting...' : 'Connect'}
                </button>
            )}
        </div>
    );
}
