/**
 * Map View Component
 * 
 * Optimized for performance using component isolation.
 * Main MapView is static; child components subscribe individually to store updates.
 */

import { useEffect, useRef, useState, memo } from 'react';
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

// Reuse icons to prevent recreation on render
const ROVER_ICON = new L.DivIcon({
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

// Memoized Icon creation for waypoints
const getWaypointIcon = (index: number, isActive: boolean) => {
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
};

interface MapViewProps {
    onWaypointClick?: (lat: number, lng: number) => void;
    allowWaypointPlacement?: boolean;
}

// 1. MAIN CONTAINER - STATIC (No high freq subscriptions)
export function MapView({ onWaypointClick, allowWaypointPlacement = true }: MapViewProps) {
    // Only subscribe to user interaction state, NOT telemetry
    const [followRover, setFollowRover] = useState(true);
    const waypointsCount = useRoverStore(state => state.waypoints.length);

    console.log('[MapView] Rendering container'); // Debug only

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
                        {waypointsCount} waypoint{waypointsCount !== 1 ? 's' : ''}
                    </span>
                </div>
            </div>

            <MapContainer
                center={[10.762622, 106.660172]} // Default center
                zoom={18}
                className="w-full h-[calc(100%-32px)] rounded-lg"
                style={{ minHeight: '360px' }}
                scrollWheelZoom={true}
            >
                <TileLayer
                    attribution='Tiles &copy; Esri'
                    url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                    maxZoom={19}
                />

                {/* Sub-components handle their own logic/subscriptions */}

                {allowWaypointPlacement && <MapClickHandler onWaypointClick={onWaypointClick} />}

                <MapFollower enabled={followRover} />

                <RoverMarker />

                <MissionLayer />

            </MapContainer>
        </div>
    );
}

// 2. ROVER MARKER - Subscribes to GPS (10Hz)
const RoverMarker = memo(function RoverMarker() {
    // Select specific fields using shallow comparison if needed, 
    // but here we just need lat/lon. 
    // Optimization: separate lat/lon selectors to avoid object creation if possible,
    // or rely on store memoization.
    const lat = useRoverStore(state => state.vehicleState.gps.latitude);
    const lng = useRoverStore(state => state.vehicleState.gps.longitude);

    if (lat === 0 && lng === 0) return null;

    return <Marker position={[lat, lng]} icon={ROVER_ICON} zIndexOffset={1000} />;
});

// 3. MAP FOLLOWER - Subscribes to GPS, Handles Panning
const MapFollower = memo(function MapFollower({ enabled }: { enabled: boolean }) {
    const map = useMap();
    const lat = useRoverStore(state => state.vehicleState.gps.latitude);
    const lng = useRoverStore(state => state.vehicleState.gps.longitude);

    // Use ref to track internal state for interaction handling
    const isUserInteracting = useRef(false);

    // Register interaction events to pause following while dragging
    useEffect(() => {
        const onDragStart = () => { isUserInteracting.current = true; };
        const onDragEnd = () => { isUserInteracting.current = false; };

        map.on('dragstart', onDragStart);
        map.on('dragend', onDragEnd);
        map.on('zoomstart', onDragStart);
        map.on('zoomend', onDragEnd);

        return () => {
            map.off('dragstart', onDragStart);
            map.off('dragend', onDragEnd);
            map.off('zoomstart', onDragStart);
            map.off('zoomend', onDragEnd);
        };
    }, [map]);

    useEffect(() => {
        if (!enabled || (lat === 0 && lng === 0) || isUserInteracting.current) return;

        // Smooth pan
        map.panTo([lat, lng], { animate: true, duration: 0.1 });
    }, [map, lat, lng, enabled]);

    return null;
});

// 4. MISSION LAYER - Subscribes to Mission/Waypoints
const MissionLayer = memo(function MissionLayer() {
    const waypoints = useRoverStore(state => state.waypoints);
    const currentWpIndex = useRoverStore(state => state.vehicleState.mission.currentWaypointIndex);

    const pathPoints: [number, number][] = waypoints.map(wp => [wp.lat, wp.lng]);

    return (
        <>
            {pathPoints.length > 1 && (
                <Polyline
                    positions={pathPoints}
                    color="#0ea5e9"
                    weight={3}
                    opacity={0.8}
                    dashArray="10, 10"
                />
            )}

            {waypoints.map((wp, index) => (
                <Marker
                    key={wp.id}
                    position={[wp.lat, wp.lng]}
                    icon={getWaypointIcon(index, index === currentWpIndex)}
                />
            ))}
        </>
    );
});

// 5. CLICK HANDLER
function MapClickHandler({ onWaypointClick }: { onWaypointClick?: (lat: number, lng: number) => void }) {
    const addWaypoint = useRoverStore(state => state.addWaypoint);
    const waypointsLength = useRoverStore(state => state.waypoints.length);

    useMapEvents({
        click: (e) => {
            if (waypointsLength < 10) {
                // Determine ID based on existing max ID or simple length
                // Ideally this logic should be in the store action, but here is fine for now
                const newWaypoint: Waypoint = {
                    id: Date.now(), // Simple unique ID
                    lat: e.latlng.lat,
                    lng: e.latlng.lng,
                };
                addWaypoint(newWaypoint);
                onWaypointClick?.(e.latlng.lat, e.latlng.lng);
            }
        },
    });
    return null;
}
