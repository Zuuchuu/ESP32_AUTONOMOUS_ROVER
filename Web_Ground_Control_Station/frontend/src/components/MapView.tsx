/**
 * Map View Component
 * 
 * Displays rover position and waypoints on an interactive map.
 */

import { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useRoverStore, Waypoint } from '../store/roverStore';

// Fix default marker icons
delete (L.Icon.Default.prototype as unknown as { _getIconUrl?: unknown })._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Custom rover icon
const roverIcon = new L.DivIcon({
    className: 'rover-marker',
    html: `
    <div class="w-8 h-8 flex items-center justify-center">
      <div class="w-6 h-6 bg-gcs-danger rounded-full border-2 border-white shadow-lg flex items-center justify-center">
        <div class="w-0 h-0 border-l-4 border-r-4 border-b-6 border-transparent border-b-white -mt-0.5"></div>
      </div>
    </div>
  `,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
});

// Waypoint icon generator
function createWaypointIcon(index: number, isActive: boolean = false) {
    return new L.DivIcon({
        className: 'waypoint-marker-container',
        html: `
      <div class="waypoint-marker ${isActive ? 'waypoint-marker-active' : ''}">
        ${index + 1}
      </div>
    `,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
    });
}

interface MapViewProps {
    onWaypointClick?: (lat: number, lng: number) => void;
    allowWaypointPlacement?: boolean;
}

export function MapView({ onWaypointClick, allowWaypointPlacement = true }: MapViewProps) {
    const { vehicleState, addWaypoint } = useRoverStore();
    const { gps, waypoints, mission } = vehicleState;
    const [followRover, setFollowRover] = useState(true);

    const hasValidPosition = gps.latitude !== 0 || gps.longitude !== 0;
    const defaultCenter: [number, number] = hasValidPosition
        ? [gps.latitude, gps.longitude]
        : [10.762622, 106.660172]; // Default to Ho Chi Minh City

    // Waypoint path
    const pathPoints: [number, number][] = waypoints.map(wp => [wp.lat, wp.lng]);

    return (
        <div className="glass-card p-2 h-full min-h-[400px]">
            <div className="flex items-center justify-between mb-2 px-2">
                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
                    Map View
                </h3>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setFollowRover(!followRover)}
                        className={`text-xs px-2 py-1 rounded ${followRover ? 'bg-gcs-primary text-white' : 'bg-gcs-card text-slate-400'
                            }`}
                    >
                        {followRover ? 'Following' : 'Static'}
                    </button>
                    <span className="text-xs text-slate-500">
                        {waypoints.length} waypoint{waypoints.length !== 1 ? 's' : ''}
                    </span>
                </div>
            </div>

            <MapContainer
                center={defaultCenter}
                zoom={16}
                className="w-full h-[calc(100%-32px)] rounded-lg"
                style={{ minHeight: '360px' }}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                {/* Waypoint click handler */}
                {allowWaypointPlacement && (
                    <MapClickHandler
                        onMapClick={(lat, lng) => {
                            if (waypoints.length < 10) {
                                const newWaypoint: Waypoint = {
                                    id: waypoints.length + 1,
                                    lat,
                                    lng,
                                };
                                addWaypoint(newWaypoint);
                                onWaypointClick?.(lat, lng);
                            }
                        }}
                    />
                )}

                {/* Auto-follow rover */}
                {followRover && hasValidPosition && (
                    <MapFollower position={[gps.latitude, gps.longitude]} />
                )}

                {/* Waypoint path */}
                {pathPoints.length > 1 && (
                    <Polyline
                        positions={pathPoints}
                        color="#0ea5e9"
                        weight={3}
                        opacity={0.8}
                        dashArray="10, 10"
                    />
                )}

                {/* Waypoint markers */}
                {waypoints.map((wp, index) => (
                    <Marker
                        key={wp.id}
                        position={[wp.lat, wp.lng]}
                        icon={createWaypointIcon(index, index === mission.currentWaypointIndex)}
                    />
                ))}

                {/* Rover marker */}
                {hasValidPosition && (
                    <Marker
                        position={[gps.latitude, gps.longitude]}
                        icon={roverIcon}
                    />
                )}
            </MapContainer>
        </div>
    );
}

// Component to handle map clicks
function MapClickHandler({ onMapClick }: { onMapClick: (lat: number, lng: number) => void }) {
    useMapEvents({
        click: (e) => {
            onMapClick(e.latlng.lat, e.latlng.lng);
        },
    });
    return null;
}

// Component to follow rover position
function MapFollower({ position }: { position: [number, number] }) {
    const map = useMap();
    const prevPosition = useRef(position);

    useEffect(() => {
        const [lat, lng] = position;
        const [prevLat, prevLng] = prevPosition.current;

        // Only update if position changed significantly
        if (Math.abs(lat - prevLat) > 0.00001 || Math.abs(lng - prevLng) > 0.00001) {
            map.setView(position, map.getZoom(), { animate: true });
            prevPosition.current = position;
        }
    }, [map, position]);

    return null;
}
