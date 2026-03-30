import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  Server, Map as MapIcon, Bell, LogOut, Building2,
  ChevronDown, TrendingUp, AlertTriangle, CheckCircle, XCircle,
  Layers, Eye, EyeOff, ExternalLink, X, Loader, Menu, FileDown
} from 'lucide-react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap, useMapEvents, Marker, Polyline, Polygon as LeafletPolygon, WMSTileLayer } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import ChatBot from '../components/ChatBot';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Custom icons for map markers
const createIcon = (color, size = 10) => L.divIcon({
  className: 'custom-icon',
  html: `<div style="width:${size}px;height:${size}px;background:${color};border:2px solid #fff;border-radius:50%;box-shadow:0 2px 4px rgba(0,0,0,0.5);"></div>`,
  iconSize: [size, size],
  iconAnchor: [size/2, size/2],
});

const posteIcon = (tension, s3renr) => {
  // S3REnR-based coloring: green=disponible, orange=contraint, red=saturé, default=by tension
  let color;
  let borderColor = '#fff';
  if (s3renr) {
    const etat = s3renr.etat;
    if (etat === 'disponible') { color = '#2ed573'; borderColor = '#fff'; }
    else if (etat === 'contraint') { color = '#ffa502'; borderColor = '#fff'; }
    else if (etat === 'sature') { color = '#ff4757'; borderColor = '#fff'; }
    else if (etat === 'non_reference') { color = tension >= 400 ? '#ff4757' : tension >= 225 ? '#ffa502' : '#3b82f6'; borderColor = '#555'; }
    else { color = tension >= 400 ? '#ff4757' : tension >= 225 ? '#ffa502' : '#3b82f6'; }
  } else {
    color = tension >= 400 ? '#ff4757' : tension >= 225 ? '#ffa502' : '#3b82f6';
  }
  const mwLabel = s3renr && s3renr.mw_dispo != null && s3renr.mw_dispo > 0
    ? `<div style="position:absolute;top:-18px;left:50%;transform:translateX(-50%);background:${color};color:#000;font-size:8px;font-weight:bold;padding:0 3px;border-radius:2px;white-space:nowrap;">${s3renr.mw_dispo}MW</div>`
    : '';
  return L.divIcon({
    className: 'poste-icon',
    html: `<div style="position:relative;">${mwLabel}<div style="width:14px;height:14px;background:${color};border:2px solid ${borderColor};transform:rotate(45deg);box-shadow:0 2px 4px rgba(0,0,0,0.5);"></div></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  });
};

const landingIcon = L.divIcon({
  className: 'landing-icon',
  html: `<div style="width:16px;height:16px;background:#00d4aa;border:2px solid #fff;display:flex;align-items:center;justify-content:center;font-size:10px;color:#0a0a0f;font-weight:bold;">⚓</div>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

const dcIcon = L.divIcon({
  className: 'dc-icon',
  html: `<div style="width:14px;height:14px;background:#8b5cf6;border:2px solid #fff;border-radius:2px;box-shadow:0 2px 4px rgba(0,0,0,0.5);"></div>`,
  iconSize: [14, 14],
  iconAnchor: [7, 7],
});

// Map component to handle viewport-based dynamic parcel loading
function MapEventHandler({ onBoundsChange, onZoomChange }) {
  const map = useMapEvents({
    moveend: () => {
      const bounds = map.getBounds();
      const zoom = map.getZoom();
      onZoomChange(zoom);
      onBoundsChange({
        min_lon: bounds.getWest(),
        min_lat: bounds.getSouth(),
        max_lon: bounds.getEast(),
        max_lat: bounds.getNorth(),
        zoom,
      });
    },
    zoomend: () => {
      onZoomChange(map.getZoom());
    },
  });
  
  return null;
}

// Component to fly to parcels when they are loaded
function FlyToParcels({ parcels, trigger }) {
  const map = useMap();
  const lastTrigger = useRef(0);
  
  useEffect(() => {
    if (trigger > lastTrigger.current && parcels.length > 0) {
      lastTrigger.current = trigger;
      const bounds = L.latLngBounds(
        parcels.slice(0, 50).map(p => [p.latitude, p.longitude])
      );
      if (bounds.isValid()) {
        map.flyToBounds(bounds, { padding: [60, 60], maxZoom: 15, duration: 1.2 });
      }
    }
  }, [trigger, parcels, map]);
  
  return null;
}

function FlyToTarget({ target }) {
  const map = useMap();
  const lastTarget = useRef(null);
  
  useEffect(() => {
    if (target && JSON.stringify(target) !== JSON.stringify(lastTarget.current)) {
      lastTarget.current = target;
      map.flyTo([target.lat, target.lng], target.zoom || 10, { duration: 1.5 });
    }
  }, [target, map]);
  
  return null;
}


// Convert MultiPolygon/Polygon GeoJSON to Leaflet positions [[lat, lng], ...]
function geoJsonToPositions(geometry) {
  if (!geometry || !geometry.coordinates) return [];
  try {
    if (geometry.type === 'MultiPolygon') {
      // Take the first polygon of the multi
      return geometry.coordinates[0][0].map(([lng, lat]) => [lat, lng]);
    } else if (geometry.type === 'Polygon') {
      return geometry.coordinates[0].map(([lng, lat]) => [lat, lng]);
    }
  } catch { return []; }
  return [];
}

// Score color helper
function getScoreColor(score) {
  if (score >= 70) return '#00d4aa';
  if (score >= 50) return '#ffa502';
  return '#ff4757';
}

// Verdict badge
function VerdictBadge({ verdict }) {
  const styles = {
    'GO': 'verdict-go',
    'A_ETUDIER': 'verdict-conditionnel',
    'DEFAVORABLE': 'verdict-no-go',
    'EXCLU': 'verdict-no-go',
  };
  
  const icons = {
    'GO': <CheckCircle size={12} />,
    'A_ETUDIER': <AlertTriangle size={12} />,
    'DEFAVORABLE': <XCircle size={12} />,
    'EXCLU': <XCircle size={12} />,
  };

  const labels = {
    'GO': 'GO',
    'A_ETUDIER': 'À ÉTUDIER',
    'DEFAVORABLE': 'DÉFAVORABLE',
    'EXCLU': 'EXCLU',
  };
  
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-mono uppercase ${styles[verdict] || 'verdict-conditionnel'}`}>
      {icons[verdict] || <AlertTriangle size={12} />}
      {labels[verdict] || verdict?.replace('_', ' ')}
    </span>
  );
}

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [selectedParcel, setSelectedParcel] = useState(null);
  const [compareList, setCompareList] = useState([]);
  const [showComparePanel, setShowComparePanel] = useState(false);
  
  // Mobile state
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [mobilePanel, setMobilePanel] = useState(null); // 'filters' | 'layers' | 'detail' | null
  const [mobileSidebar, setMobileSidebar] = useState(false);
  const [chatFlyTarget, setChatFlyTarget] = useState(null);
  const [externalChatMessage, setExternalChatMessage] = useState(null);
  
  // Map layers data
  const [landingPoints, setLandingPoints] = useState([]);
  const [dcExistants, setDcExistants] = useState([]);
  const [submarineCables, setSubmarineCables] = useState([]);
  const [electricalAssets, setElectricalAssets] = useState([]);
  const [s3renrSummary, setS3renrSummary] = useState([]);
  
  // RTE Future 400kV line data
  const [futureLine400kv, setFutureLine400kv] = useState(null);
  
  // Layer visibility
  const [showLayers, setShowLayers] = useState(false);
  const [layers, setLayers] = useState({
    parcels: true,
    postes_htb: true,
    lignes_400kv: true,
    lignes_225kv: false,
    landing_points: true,
    submarine_cables: true,
    dc_existants: true,
    rte_future_400kv: true,
    zones_industrielles: false,
    zones_inondables: false,
    heatmap_mw: false,
    cours_eau: false,
    fond_routier: false,
  });
  
  // SIREN modal
  const [sirenModal, setSirenModal] = useState(null);
  
  // Parcels loaded via map or AI
  const [franceParcels, setFranceParcels] = useState([]);
  
  // Viewport-based dynamic loading
  const [mapZoom, setMapZoom] = useState(6);
  const [bboxLoading, setBboxLoading] = useState(false);
  const bboxTimerRef = useRef(null);
  const MIN_ZOOM_FOR_PARCELS = 14;
  const [flyTrigger, setFlyTrigger] = useState(0);
  const [gpuZones, setGpuZones] = useState([]);

  // Load parcels dynamically from viewport BBox
  const loadBboxParcels = useCallback(async (bounds) => {
    if (bounds.zoom < MIN_ZOOM_FOR_PARCELS) return;
    
    setBboxLoading(true);
    try {
      const response = await axios.get(
        `${API}/france/parcelles/bbox?min_lon=${bounds.min_lon}&min_lat=${bounds.min_lat}&max_lon=${bounds.max_lon}&max_lat=${bounds.max_lat}&limit=200`
      );
      const newParcels = response.data.parcelles || [];
      setFranceParcels(prev => {
        const existing = new Set(prev.map(p => p.parcel_id));
        const unique = newParcels.filter(p => !existing.has(p.parcel_id));
        if (unique.length === 0) return prev;
        return [...prev, ...unique];
      });
    } catch (error) {
      console.error('Error loading bbox parcels:', error);
    } finally {
      setBboxLoading(false);
    }
  }, []);

  // Debounced BBox handler
  const handleBoundsChange = useCallback((bounds) => {
    if (bboxTimerRef.current) clearTimeout(bboxTimerRef.current);
    bboxTimerRef.current = setTimeout(() => {
      loadBboxParcels(bounds);
      // Load GPU industrial zones when layer active and zoom >= 12
      if (layers.zones_industrielles && bounds.zoom >= 12) {
        axios.get(`${API}/france/gpu-zones?min_lon=${bounds.min_lon}&min_lat=${bounds.min_lat}&max_lon=${bounds.max_lon}&max_lat=${bounds.max_lat}`)
          .then(res => setGpuZones(res.data.zones || []))
          .catch(() => {});
      }
    }, 600);
  }, [loadBboxParcels, layers.zones_industrielles]);

  // Fetch map layers data (infrastructure)
  useEffect(() => {
    fetchMapLayers();
  }, []);
  
  // Responsive resize listener
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  // Close mobile panel when selecting a parcel
  useEffect(() => {
    if (selectedParcel && isMobile) {
      setMobilePanel('detail');
    }
  }, [selectedParcel, isMobile]);
  
  // All parcels displayed — filtering done via AI chatbot
  const filteredParcels = franceParcels;

  // Load parcels around a geographic point (used by poste HTB / landing point popups)
  const loadParcelsAroundPoint = useCallback(async (lon, lat, radiusMeters, label) => {
    const delta = radiusMeters / 111000; // rough degree conversion
    const bounds = {
      min_lon: lon - delta,
      min_lat: lat - delta,
      max_lon: lon + delta,
      max_lat: lat + delta,
      zoom: 15,
    };
    setBboxLoading(true);
    try {
      const response = await axios.get(
        `${API}/france/parcelles/bbox?min_lon=${bounds.min_lon}&min_lat=${bounds.min_lat}&max_lon=${bounds.max_lon}&max_lat=${bounds.max_lat}&limit=200`
      );
      const newParcels = response.data.parcelles || [];
      setFranceParcels(prev => {
        const existing = new Set(prev.map(p => p.parcel_id));
        const unique = newParcels.filter(p => !existing.has(p.parcel_id));
        if (unique.length === 0) return prev;
        return [...prev, ...unique];
      });
      setFlyTrigger(t => t + 1);
      setChatFlyTarget({ lat, lng: lon, zoom: 14 });
    } catch (error) {
      console.error(`Erreur chargement parcelles autour de ${label}:`, error);
    } finally {
      setBboxLoading(false);
    }
  }, []);

  const fetchMapLayers = async () => {
    try {
      const [lpRes, dcRes, cablesRes, elecRes, s3renrRes, futureLineRes] = await Promise.all([
        axios.get(`${API}/map/landing-points`),
        axios.get(`${API}/map/dc`),
        axios.get(`${API}/map/submarine-cables`),
        axios.get(`${API}/map/electrical-assets`),
        axios.get(`${API}/s3renr/summary`),
        axios.get(`${API}/map/rte-future-400kv`),
      ]);
      setLandingPoints(lpRes.data.landing_points || []);
      setDcExistants(dcRes.data.dc_existants || []);
      setSubmarineCables(cablesRes.data.submarine_cables || []);
      setElectricalAssets(elecRes.data.electrical_assets || []);
      setS3renrSummary(s3renrRes.data.summary || []);
      setFutureLine400kv(futureLineRes.data || null);
    } catch (error) {
      console.error('Error fetching map layers:', error);
    }
  };

  const handleParcelClick = (parcel) => {
    setSelectedParcel(parcel);
  };

  const addToCompare = (parcel) => {
    if (compareList.length >= 3) return;
    if (compareList.find(p => p.parcel_id === parcel.parcel_id)) return;
    setCompareList(prev => [...prev, parcel]);
  };
  const removeFromCompare = (id) => {
    setCompareList(prev => prev.filter(p => p.parcel_id !== id));
  };

  const toggleLayer = (layerName) => {
    setLayers(prev => ({ ...prev, [layerName]: !prev[layerName] }));
  };

  // Filter electrical assets by type
  const postes = electricalAssets.filter(a => a.type === 'poste_htb');
  const lignes400 = electricalAssets.filter(a => a.type === 'ligne_400kv');
  const lignes225 = electricalAssets.filter(a => a.type === 'ligne_225kv');

  return (
    <div className="h-screen flex flex-col" style={{ background: '#0a0a0f' }}>
      {/* Main content */}
      <div className="main-content flex flex-col h-full">
        {/* Top bar */}
        <header 
          className="h-12 flex items-center justify-between px-3 md:px-4 shrink-0"
          style={{ background: '#12121a', borderBottom: '1px solid #1f1f2e' }}
        >
          <div className="flex items-center gap-2 md:gap-4">
            <div className="flex items-center gap-2">
              <Server size={isMobile ? 16 : 20} style={{ color: '#00d4aa' }} />
              <span className="font-bold text-sm md:text-base" style={{ color: '#e8e8ed' }}>COCKPIT IMMO</span>
            </div>
            
            {/* Mode indicator */}
            {!isMobile && (
              <span className="ml-8 h-8 px-3 flex items-center gap-2 text-xs font-mono uppercase text-[#00d4aa] border-b-2 border-[#00d4aa]" data-testid="nav-map">
                <MapIcon size={14} />
                Carte
              </span>
            )}
          </div>

          <div className="flex items-center gap-2 md:gap-4">
            {isMobile && (
              <button 
                onClick={() => setMobileSidebar(!mobileSidebar)}
                className="h-8 w-8 flex items-center justify-center text-[#8f8f9d]"
                data-testid="mobile-menu-btn"
              >
                <Menu size={18} />
              </button>
            )}
            {!isMobile && (
              <>
                <button className="h-8 w-8 flex items-center justify-center text-[#8f8f9d] hover:text-[#e8e8ed]">
                  <Bell size={16} />
                </button>
                <div className="flex items-center gap-2">
                  {user?.picture && (
                    <img src={user.picture} alt="" className="w-6 h-6 rounded-full" />
                  )}
                  <span className="text-xs" style={{ color: '#8f8f9d' }}>{user?.name}</span>
                </div>
              </>
            )}
            <button 
              onClick={logout}
              className="h-8 w-8 flex items-center justify-center text-[#8f8f9d] hover:text-[#ff4757]"
              data-testid="logout-btn"
            >
              <LogOut size={16} />
            </button>
          </div>
        </header>

        {/* Status bar - desktop */}
        {!isMobile && (
          <div 
            className="h-10 flex items-center gap-4 px-4 shrink-0"
            style={{ background: '#0a0a0f', borderBottom: '1px solid #1f1f2e' }}
          >
            <span className="text-xs font-mono" style={{ color: '#8f8f9d' }} data-testid="status-bar">
              {filteredParcels.length} sites
              {mapZoom < MIN_ZOOM_FOR_PARCELS && ' · Zoomez (z≥14) pour voir les parcelles'}
              {mapZoom >= MIN_ZOOM_FOR_PARCELS && ` · z${mapZoom}`}
              {' · '}{postes.length} postes · {dcExistants.length} DC · {landingPoints.length} LP
            </span>
            {bboxLoading && (
              <span className="flex items-center gap-1 text-xs" style={{ color: '#3b82f6' }}>
                <Loader size={12} className="animate-spin" />
                Chargement parcelles...
              </span>
            )}
            {franceParcels.length > 0 && (
              <button
                onClick={() => setFranceParcels([])}
                className="text-xs flex items-center gap-1 hover:text-[#ff4757]"
                style={{ color: '#8f8f9d' }}
                data-testid="clear-parcels-btn"
              >
                <XCircle size={12} />
                Effacer parcelles
              </button>
            )}
          </div>
        )}

        {/* Mobile top controls */}
        {isMobile && (
          <div 
            className="flex items-center gap-2 px-3 py-2 shrink-0"
            style={{ background: '#0a0a0f', borderBottom: '1px solid #1f1f2e' }}
          >
            <span className="text-[10px] font-mono flex-1" style={{ color: '#8f8f9d' }}>
              {filteredParcels.length} sites
              {bboxLoading && <Loader size={10} className="inline ml-1 animate-spin" />}
            </span>
            <button
              onClick={() => setMobilePanel(mobilePanel === 'layers' ? null : 'layers')}
              className={`h-8 w-8 flex items-center justify-center rounded ${mobilePanel === 'layers' ? 'bg-[#00d4aa22] text-[#00d4aa]' : 'text-[#8f8f9d]'}`}
              data-testid="mobile-layers-btn"
            >
              <Layers size={16} />
            </button>
          </div>
        )}

        {/* Main content area */}
        <div className="flex-1 flex overflow-hidden relative">
            <>
              {/* Map - full width on mobile */}
              <div className="flex-1 relative">
                <MapContainer
                  center={[46.5, 2.5]}
                  zoom={6}
                  style={{ height: '100%', width: '100%' }}
                >
                  <TileLayer
                    url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                  />
                  <MapEventHandler 
                    onBoundsChange={handleBoundsChange}
                    onZoomChange={setMapZoom}
                  />
                    
                    {/* RTE Future 400kV Line + Buffers */}
                    {layers.rte_future_400kv && futureLine400kv && (
                      <>
                        {/* Buffer 5km (bottom layer) */}
                        {futureLine400kv.buffers?.['5km']?.coordinates?.[0] && (
                          <LeafletPolygon
                            positions={futureLine400kv.buffers['5km'].coordinates[0].map(c => [c[1], c[0]])}
                            pathOptions={{ color: '#ffd32a', fillColor: '#ffd32a', fillOpacity: 0.08, weight: 1, opacity: 0.4, dashArray: '4,4' }}
                          >
                            <Popup><div className="p-2"><p className="font-bold text-xs">Zone opportunité (5 km)</p><p className="text-xs text-gray-400">Ligne future 400kV Fos → Jonquières</p></div></Popup>
                          </LeafletPolygon>
                        )}
                        {/* Buffer 3km */}
                        {futureLine400kv.buffers?.['3km']?.coordinates?.[0] && (
                          <LeafletPolygon
                            positions={futureLine400kv.buffers['3km'].coordinates[0].map(c => [c[1], c[0]])}
                            pathOptions={{ color: '#ffa502', fillColor: '#ffa502', fillOpacity: 0.12, weight: 1, opacity: 0.5, dashArray: '4,4' }}
                          >
                            <Popup><div className="p-2"><p className="font-bold text-xs">Zone stratégique (3 km)</p><p className="text-xs text-gray-400">Ligne future 400kV Fos → Jonquières</p></div></Popup>
                          </LeafletPolygon>
                        )}
                        {/* Buffer 1km */}
                        {futureLine400kv.buffers?.['1km']?.coordinates?.[0] && (
                          <LeafletPolygon
                            positions={futureLine400kv.buffers['1km'].coordinates[0].map(c => [c[1], c[0]])}
                            pathOptions={{ color: '#ff4757', fillColor: '#ff4757', fillOpacity: 0.20, weight: 1, opacity: 0.6 }}
                          >
                            <Popup><div className="p-2"><p className="font-bold text-xs">Zone chaude (1 km)</p><p className="text-xs text-gray-400">Potentiel raccordement futur élevé</p></div></Popup>
                          </LeafletPolygon>
                        )}
                        {/* The line itself */}
                        <Polyline
                          positions={futureLine400kv.line.coordinates.map(c => [c[1], c[0]])}
                          pathOptions={{ color: '#ff0040', weight: 3.5, opacity: 0.95, dashArray: '12,6' }}
                        >
                          <Popup>
                            <div className="p-2" style={{ minWidth: 240 }}>
                              <p className="font-bold text-sm">{futureLine400kv.metadata?.nom}</p>
                              <p className="text-xs text-gray-400 mt-1">
                                {futureLine400kv.metadata?.tension_kv} kV · Mise en service : {futureLine400kv.metadata?.mise_en_service_estimee}
                              </p>
                              <p className="text-xs text-gray-500 mt-1">{futureLine400kv.metadata?.description}</p>
                              <p className="text-[10px] text-gray-500 mt-1 italic">Source : {futureLine400kv.metadata?.source}</p>
                            </div>
                          </Popup>
                        </Polyline>
                      </>
                    )}

                    {/* Submarine cables */}
                    {layers.submarine_cables && submarineCables.map(cable => (
                      <Polyline
                        key={cable.cable_id}
                        positions={cable.geometry.coordinates.map(c => [c[1], c[0]])}
                        pathOptions={{ 
                          color: cable.statut === 'operationnel' ? '#00d4aa' : '#ffa502',
                          weight: 3,
                          opacity: 0.7,
                          dashArray: cable.statut === 'en_construction' ? '10,5' : null
                        }}
                      >
                        <Popup>
                          <div className="p-2">
                            <p className="font-bold">{cable.nom}</p>
                            <p className="text-xs text-gray-400">
                              {cable.capacite_tbps} Tbps · {cable.statut === 'operationnel' ? 'Opérationnel' : 'En construction'}
                            </p>
                          </div>
                        </Popup>
                      </Polyline>
                    ))}
                    
                    {/* Lignes 400kV */}
                    {layers.lignes_400kv && lignes400.map(ligne => (
                      <Polyline
                        key={ligne.asset_id}
                        positions={ligne.geometry.coordinates.map(c => [c[1], c[0]])}
                        pathOptions={{ color: '#ff4757', weight: 3, opacity: 0.8 }}
                      >
                        <Popup>
                          <div className="p-2">
                            <p className="font-bold">{ligne.nom}</p>
                            <p className="text-xs text-gray-400">Ligne 400 kV</p>
                          </div>
                        </Popup>
                      </Polyline>
                    ))}
                    
                    {/* Lignes 225kV */}
                    {layers.lignes_225kv && lignes225.map(ligne => (
                      <Polyline
                        key={ligne.asset_id}
                        positions={ligne.geometry.coordinates.map(c => [c[1], c[0]])}
                        pathOptions={{ color: '#ffa502', weight: 2, opacity: 0.7 }}
                      >
                        <Popup>
                          <div className="p-2">
                            <p className="font-bold">{ligne.nom}</p>
                            <p className="text-xs text-gray-400">Ligne 225 kV</p>
                          </div>
                        </Popup>
                      </Polyline>
                    ))}
                    
                    {/* Postes HTB */}
                    {layers.postes_htb && postes.map(poste => (
                      <Marker
                        key={poste.asset_id}
                        position={[poste.geometry.coordinates[1], poste.geometry.coordinates[0]]}
                        icon={posteIcon(poste.tension_kv, poste.s3renr)}
                      >
                        <Popup>
                          <div className="p-2" style={{ minWidth: 220 }}>
                            <p className="font-bold text-sm">{poste.nom}</p>
                            <p className="text-xs text-gray-400">
                              {poste.tension_kv} kV · {poste.puissance_mva} MVA · {poste.region}
                            </p>
                            {poste.s3renr && (
                              <div className="mt-2 pt-2" style={{ borderTop: '1px solid #333' }}>
                                <p className="text-xs font-bold" style={{ 
                                  color: poste.s3renr.etat === 'disponible' ? '#2ed573' 
                                       : poste.s3renr.etat === 'contraint' ? '#ffa502' 
                                       : poste.s3renr.etat === 'sature' ? '#ff4757' 
                                       : '#8f8f9d' 
                                }}>
                                  S3REnR: {poste.s3renr.etat === 'disponible' ? 'DISPONIBLE' 
                                         : poste.s3renr.etat === 'contraint' ? 'CONTRAINT' 
                                         : poste.s3renr.etat === 'sature' ? 'SATURE' 
                                         : poste.s3renr.etat === 'non_reference' ? 'Non référencé' 
                                         : poste.s3renr.etat?.toUpperCase()}
                                </p>
                                {poste.s3renr.mw_dispo != null && (
                                  <div className="mt-1">
                                    <div className="flex justify-between text-xs">
                                      <span style={{ color: '#8f8f9d' }}>MW Disponible</span>
                                      <span className="font-bold" style={{ color: '#2ed573' }}>{poste.s3renr.mw_dispo} MW</span>
                                    </div>
                                    {poste.s3renr.mw_reserve != null && (
                                      <div className="flex justify-between text-xs">
                                        <span style={{ color: '#8f8f9d' }}>Réserve / Consommé</span>
                                        <span>{poste.s3renr.mw_reserve} / {poste.s3renr.mw_consomme || 0} MW</span>
                                      </div>
                                    )}
                                    {poste.s3renr.mw_reserve > 0 && (
                                      <div className="mt-1" style={{ background: '#1a1a2e', borderRadius: 4, overflow: 'hidden', height: 6 }}>
                                        <div style={{ 
                                          width: `${Math.min(100, ((poste.s3renr.mw_consomme || 0) / poste.s3renr.mw_reserve) * 100)}%`,
                                          height: '100%',
                                          background: poste.s3renr.etat === 'disponible' ? '#2ed573' : poste.s3renr.etat === 'contraint' ? '#ffa502' : '#ff4757',
                                          borderRadius: 4,
                                        }} />
                                      </div>
                                    )}
                                  </div>
                                )}
                                {poste.s3renr.score_dc != null && poste.s3renr.score_dc > 0 && (
                                  <div className="flex justify-between text-xs mt-1">
                                    <span style={{ color: '#8f8f9d' }}>Score DC</span>
                                    <span className="font-bold">{poste.s3renr.score_dc}/10</span>
                                  </div>
                                )}
                                {poste.s3renr.renforcement && (
                                  <p className="text-xs mt-1" style={{ color: '#00d4aa' }}>
                                    Renforcement: {poste.s3renr.renforcement}
                                  </p>
                                )}
                                {poste.s3renr.note && (
                                  <p className="text-xs mt-1" style={{ color: '#ff4757' }}>
                                    {poste.s3renr.note}
                                  </p>
                                )}
                              </div>
                            )}
                            <button
                              onClick={() => loadParcelsAroundPoint(
                                poste.geometry.coordinates[0],
                                poste.geometry.coordinates[1],
                                5000,
                                poste.nom
                              )}
                              className="mt-2 w-full text-xs px-2 py-1 bg-[#ffa502] text-[#0a0a0f] font-mono uppercase"
                            >
                              Parcelles à 5km
                            </button>
                          </div>
                        </Popup>
                      </Marker>
                    ))}
                    
                    {/* Landing points */}
                    {layers.landing_points && landingPoints.map(lp => (
                      <Marker
                        key={lp.landing_id}
                        position={[lp.geometry.coordinates[1], lp.geometry.coordinates[0]]}
                        icon={landingIcon}
                      >
                        <Popup>
                          <div className="p-2">
                            <p className="font-bold">{lp.nom}</p>
                            <p className="text-xs text-gray-400">
                              {lp.nb_cables_connectes} câbles · {lp.is_major_hub ? 'Hub majeur' : 'Landing point'}
                            </p>
                            {lp.cables_noms && (
                              <p className="text-xs mt-1">{lp.cables_noms.slice(0,3).join(', ')}</p>
                            )}
                            <button
                              onClick={() => loadParcelsAroundPoint(
                                lp.geometry.coordinates[0],
                                lp.geometry.coordinates[1],
                                10000,
                                lp.nom
                              )}
                              className="mt-2 w-full text-xs px-2 py-1 bg-[#00d4aa] text-[#0a0a0f] font-mono uppercase"
                            >
                              Parcelles à 10km
                            </button>
                          </div>
                        </Popup>
                      </Marker>
                    ))}
                    
                    {/* DC existants */}
                    {layers.dc_existants && dcExistants.map(dc => (
                      <Marker
                        key={dc.dc_id}
                        position={[dc.geometry.coordinates[1], dc.geometry.coordinates[0]]}
                        icon={dcIcon}
                      >
                        <Popup>
                          <div className="p-2">
                            <p className="font-bold">{dc.nom}</p>
                            <p className="text-xs text-gray-400">
                              {dc.operateur} · {dc.puissance_mw} MW · {dc.tier}
                            </p>
                          </div>
                        </Popup>
                      </Marker>
                    ))}

                    {/* Zones industrielles GPU */}
                    {layers.zones_industrielles && gpuZones.map((zone, idx) => {
                      const positions = geoJsonToPositions(zone.geometry);
                      if (!positions.length) return null;
                      return (
                        <LeafletPolygon
                          key={`gpu-zone-${idx}`}
                          positions={positions}
                          pathOptions={{ color: '#3b82f6', fillColor: '#3b82f6', fillOpacity: 0.15, weight: 1 }}
                        >
                          <Popup>
                            <div className="text-xs">
                              <b>{zone.properties?.typezone}</b> — {zone.properties?.libelle || 'Zone activités'}
                            </div>
                          </Popup>
                        </LeafletPolygon>
                      );
                    })}

                    {/* Heatmap MW S3REnR */}
                    {layers.heatmap_mw && postes.map((poste, idx) => {
                      const s3renr = poste.s3renr || {};
                      const etat = s3renr.etat || 'inconnu';
                      const mw = s3renr.mw_dispo || 0;
                      let color = '#ffa502';
                      let opacity = 0.08;
                      if (etat === 'disponible' && mw > 50) { color = '#2ed573'; opacity = 0.12; }
                      else if (etat === 'disponible') { color = '#2ed573'; opacity = 0.08; }
                      else if (etat === 'sature') { color = '#ff4757'; opacity = 0.15; }
                      else if (etat === 'contraint') { color = '#ffa502'; opacity = 0.10; }
                      return (
                        <CircleMarker
                          key={`heatmap-${idx}`}
                          center={[poste.geometry.coordinates[1], poste.geometry.coordinates[0]]}
                          radius={40}
                          pathOptions={{ color, fillColor: color, fillOpacity: opacity, weight: 0.5 }}
                        />
                      );
                    })}

                    {/* Zones inondables */}
                    {layers.zones_inondables && filteredParcels.filter(p => p.ppri_zone).map(p => (
                      <CircleMarker
                        key={`flood-${p.parcel_id}`}
                        center={[p.latitude, p.longitude]}
                        radius={20}
                        pathOptions={{ color: '#ff4757', fillColor: '#ff4757', fillOpacity: 0.2, weight: 1, dashArray: '4' }}
                      >
                        <Popup><span className="text-xs text-red-400">Zone inondable (PPRI)</span></Popup>
                      </CircleMarker>
                    ))}

                    {/* Cours d'eau WMS */}
                    {layers.cours_eau && (
                      <WMSTileLayer
                        url="https://data.geopf.fr/wms-r"
                        layers="HYDROGRAPHY.HYDROGRAPHY"
                        format="image/png"
                        transparent={true}
                        opacity={0.5}
                        attribution="IGN"
                      />
                    )}

                    {/* Fond routier */}
                    {layers.fond_routier && (
                      <TileLayer
                        url="https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png"
                        opacity={0.4}
                        attribution="OpenStreetMap HOT"
                      />
                    )}
                    
                    {/* Parcels - rendered as cadastral polygons */}
                    {layers.parcels && filteredParcels.map(parcel => {
                      const score = parcel.score?.score || parcel.score?.score_net || 0;
                      const positions = geoJsonToPositions(parcel.geometry);
                      const color = getScoreColor(score);
                      const isSelected = selectedParcel?.parcel_id === parcel.parcel_id;
                      
                      if (positions.length > 2) {
                        return (
                          <LeafletPolygon
                            key={parcel.parcel_id}
                            positions={positions}
                            pathOptions={{
                              fillColor: color,
                              fillOpacity: isSelected ? 0.7 : 0.35,
                              color: isSelected ? '#ffffff' : '#00d4aa',
                              weight: isSelected ? 3 : 1,
                              opacity: 0.8,
                            }}
                            eventHandlers={{
                              click: () => handleParcelClick(parcel)
                            }}
                          >
                            <Popup>
                              <div className="p-2" style={{ minWidth: 220 }}>
                                <p className="font-bold text-sm">{parcel.commune}</p>
                                <p className="text-xs text-gray-400">{parcel.ref_cadastrale} · {parcel.surface_ha?.toFixed(1)} ha</p>
                                <p className="text-xs text-gray-400">HTB: {(parcel.dist_poste_htb_m/1000).toFixed(1)} km · LP: {parcel.dist_landing_point_km} km</p>
                                {parcel.future_400kv_buffer && (
                                  <p className="text-xs font-bold" style={{ color: '#ff0040' }}>
                                    400kV Future: {parcel.future_400kv_buffer} (+{parcel.future_400kv_score_bonus}pts)
                                  </p>
                                )}
                                <div className="mt-2 flex items-center gap-2">
                                  <span className="font-mono text-lg" style={{ color }}>
                                    {score.toFixed(0)}/100
                                  </span>
                                  <VerdictBadge verdict={parcel.score?.verdict} />
                                </div>
                              </div>
                            </Popup>
                          </LeafletPolygon>
                        );
                      }
                      
                      // Fallback: CircleMarker if no polygon geometry
                      return (
                        <CircleMarker
                          key={parcel.parcel_id}
                          center={[parcel.latitude, parcel.longitude]}
                          radius={8}
                          fillColor={color}
                          fillOpacity={0.7}
                          color="#00d4aa"
                          weight={1.5}
                          eventHandlers={{
                            click: () => handleParcelClick(parcel)
                          }}
                        >
                          <Popup>
                            <div className="p-2" style={{ minWidth: 200 }}>
                              <p className="font-bold text-sm">{parcel.commune}</p>
                              <p className="text-xs text-gray-400">{parcel.ref_cadastrale} · {parcel.surface_ha?.toFixed(1)} ha</p>
                              <div className="mt-2 flex items-center gap-2">
                                <span className="font-mono text-lg" style={{ color }}>
                                  {score.toFixed(0)}/100
                                </span>
                                <VerdictBadge verdict={parcel.score?.verdict} />
                              </div>
                            </div>
                          </Popup>
                        </CircleMarker>
                      );
                    })}
                    
                    <FlyToParcels parcels={franceParcels} trigger={flyTrigger} />
                    <FlyToTarget target={chatFlyTarget} />
                  </MapContainer>
                
                {/* Zoom indicator overlay */}
                {mapZoom < MIN_ZOOM_FOR_PARCELS && (
                  <div 
                    className={`absolute left-1/2 -translate-x-1/2 z-[1000] px-3 py-1.5 text-xs font-mono ${isMobile ? 'bottom-16' : 'bottom-4'}`}
                    style={{ background: 'rgba(18,18,26,0.9)', border: '1px solid #1f1f2e', color: '#ffa502', maxWidth: isMobile ? '90%' : 'auto', textAlign: 'center' }}
                    data-testid="zoom-indicator"
                  >
                    Zoom 14+ pour parcelles · z{mapZoom}
                  </div>
                )}
                
                {/* Loading indicator for bbox */}
                {bboxLoading && (
                  <div 
                    className="absolute top-4 left-1/2 -translate-x-1/2 z-[1000] px-3 py-1.5 flex items-center gap-2 text-xs font-mono"
                    style={{ background: 'rgba(18,18,26,0.9)', border: '1px solid #3b82f6', color: '#3b82f6' }}
                  >
                    <Loader size={12} className="animate-spin" />
                    Chargement des parcelles IGN...
                  </div>
                )}
                
                {/* Layer control - desktop only (mobile uses bottom sheet) */}
                {!isMobile && (
                <div 
                  className="absolute top-4 right-4 z-[1000]"
                  style={{ minWidth: 200 }}
                >
                  <button
                    onClick={() => setShowLayers(!showLayers)}
                    className="w-full flex items-center justify-between gap-2 px-3 py-2 text-xs font-mono uppercase"
                    style={{ background: '#12121a', border: '1px solid #1f1f2e', color: '#e8e8ed' }}
                    data-testid="layers-toggle"
                  >
                    <span className="flex items-center gap-2">
                      <Layers size={14} />
                      Couches
                    </span>
                    <ChevronDown size={14} className={`transition-transform ${showLayers ? 'rotate-180' : ''}`} />
                  </button>
                  
                  {showLayers && (
                    <div 
                      className="mt-1 p-2 space-y-1"
                      style={{ background: '#12121a', border: '1px solid #1f1f2e' }}
                    >
                      <LayerToggle 
                        label="Parcelles" 
                        color="#00d4aa" 
                        active={layers.parcels} 
                        onClick={() => toggleLayer('parcels')} 
                      />
                      <LayerToggle 
                        label="Postes HTB" 
                        color="#ffa502" 
                        icon="◆"
                        active={layers.postes_htb} 
                        onClick={() => toggleLayer('postes_htb')} 
                      />
                      <LayerToggle 
                        label="Lignes 400kV" 
                        color="#ff4757" 
                        icon="─"
                        active={layers.lignes_400kv} 
                        onClick={() => toggleLayer('lignes_400kv')} 
                      />
                      <LayerToggle 
                        label="Lignes 225kV" 
                        color="#ffa502" 
                        icon="─"
                        active={layers.lignes_225kv} 
                        onClick={() => toggleLayer('lignes_225kv')} 
                      />
                      <LayerToggle 
                        label="Landing Points" 
                        color="#00d4aa" 
                        icon="⚓"
                        active={layers.landing_points} 
                        onClick={() => toggleLayer('landing_points')} 
                      />
                      <LayerToggle 
                        label="Câbles sous-marins" 
                        color="#00d4aa" 
                        icon="〰"
                        active={layers.submarine_cables} 
                        onClick={() => toggleLayer('submarine_cables')} 
                      />
                      <LayerToggle 
                        label="DC existants" 
                        color="#8b5cf6" 
                        icon="■"
                        active={layers.dc_existants} 
                        onClick={() => toggleLayer('dc_existants')} 
                      />
                      <LayerToggle 
                        label="400kV Future Fos→Jonq." 
                        color="#ff0040" 
                        icon="⚡"
                        active={layers.rte_future_400kv} 
                        onClick={() => toggleLayer('rte_future_400kv')} 
                      />
                      <div className="mt-2 pt-2" style={{ borderTop: '1px solid #1f1f2e' }}>
                        <div className="text-[10px] text-[#8f8f9d] uppercase mb-1">Environnement</div>
                      </div>
                      <LayerToggle label="Zones industrielles" color="#3b82f6" icon="▬" active={layers.zones_industrielles} onClick={() => toggleLayer('zones_industrielles')} />
                      <LayerToggle label="Heatmap MW dispo" color="#2ed573" icon="◉" active={layers.heatmap_mw} onClick={() => toggleLayer('heatmap_mw')} />
                      <LayerToggle label="Zones inondables" color="#ff4757" icon="◌" active={layers.zones_inondables} onClick={() => toggleLayer('zones_inondables')} />
                      <LayerToggle label="Cours d'eau" color="#0ea5e9" icon="〰" active={layers.cours_eau} onClick={() => toggleLayer('cours_eau')} />
                      <LayerToggle label="Réseau routier" color="#a78bfa" icon="═" active={layers.fond_routier} onClick={() => toggleLayer('fond_routier')} />
                    </div>
                  )}
                </div>
                )}
              </div>

              {/* Side panel - desktop: right sidebar, mobile: bottom sheet */}
              {(!isMobile || mobileSidebar || selectedParcel) && (
              <div 
                className={isMobile 
                  ? "fixed bottom-0 left-0 right-0 z-30 flex flex-col" 
                  : "w-96 flex flex-col"
                }
                style={{ 
                  background: '#12121a', 
                  borderLeft: isMobile ? 'none' : '1px solid #1f1f2e',
                  borderTop: isMobile ? '1px solid #1f1f2e' : 'none',
                  maxHeight: isMobile ? '55vh' : '100%',
                  borderRadius: isMobile ? '12px 12px 0 0' : 0,
                }}
              >
                {/* Mobile drag handle */}
                {isMobile && (
                  <div className="flex justify-center py-2" onClick={() => { setMobileSidebar(false); setSelectedParcel(null); }}>
                    <div style={{ width: 36, height: 4, borderRadius: 2, background: '#3f3f5f' }} />
                  </div>
                )}
                {selectedParcel ? (
                  <ParcelDetail 
                    parcel={selectedParcel} 
                    onClose={() => setSelectedParcel(null)}
                    onShowSiren={(p) => setSirenModal(p)}
                    addToCompare={addToCompare}
                    compareList={compareList}
                  />
                ) : (
                  <EmptyStatePanel
                    postes={postes}
                    onSendChat={(query) => {
                      setExternalChatMessage(query);
                    }}
                  />
                )}
              </div>
              )}
            </>

        </div>
      </div>

      {/* Mobile Layers Overlay */}
      {isMobile && mobilePanel === 'layers' && (
        <div 
          className="fixed bottom-0 left-0 right-0 z-40 p-3"
          style={{ background: '#12121a', borderTop: '1px solid #1f1f2e', borderRadius: '12px 12px 0 0' }}
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-mono uppercase" style={{ color: '#00d4aa' }}>Couches</span>
            <button onClick={() => setMobilePanel(null)} className="text-[#8f8f9d]"><X size={16} /></button>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <LayerToggle label="Parcelles" color="#00d4aa" active={layers.parcels} onClick={() => toggleLayer('parcels')} />
            <LayerToggle label="Postes HTB" color="#ffa502" icon="◆" active={layers.postes_htb} onClick={() => toggleLayer('postes_htb')} />
            <LayerToggle label="Lignes 400kV" color="#ff4757" icon="─" active={layers.lignes_400kv} onClick={() => toggleLayer('lignes_400kv')} />
            <LayerToggle label="Lignes 225kV" color="#ffa502" icon="─" active={layers.lignes_225kv} onClick={() => toggleLayer('lignes_225kv')} />
            <LayerToggle label="Landing Points" color="#00d4aa" icon="⚓" active={layers.landing_points} onClick={() => toggleLayer('landing_points')} />
            <LayerToggle label="Câbles sous-marins" color="#00d4aa" icon="〰" active={layers.submarine_cables} onClick={() => toggleLayer('submarine_cables')} />
            <LayerToggle label="DC existants" color="#8b5cf6" icon="■" active={layers.dc_existants} onClick={() => toggleLayer('dc_existants')} />
            <LayerToggle label="400kV Future" color="#ff0040" icon="⚡" active={layers.rte_future_400kv} onClick={() => toggleLayer('rte_future_400kv')} />
            <LayerToggle label="Zones indus." color="#3b82f6" icon="▬" active={layers.zones_industrielles} onClick={() => toggleLayer('zones_industrielles')} />
            <LayerToggle label="Heatmap MW" color="#2ed573" icon="◉" active={layers.heatmap_mw} onClick={() => toggleLayer('heatmap_mw')} />
            <LayerToggle label="Inondables" color="#ff4757" icon="◌" active={layers.zones_inondables} onClick={() => toggleLayer('zones_inondables')} />
            <LayerToggle label="Cours d'eau" color="#0ea5e9" icon="〰" active={layers.cours_eau} onClick={() => toggleLayer('cours_eau')} />
            <LayerToggle label="Routes" color="#a78bfa" icon="═" active={layers.fond_routier} onClick={() => toggleLayer('fond_routier')} />
          </div>
        </div>
      )}

      {/* AI Chat Assistant */}
      <ChatBot
        onFlyTo={(lat, lng, zoom) => setChatFlyTarget({ lat, lng, zoom })}
        onHighlightSites={(ids) => { /* Future: highlight sites on map */ }}
        onSelectParcelFromChat={(parcel) => {
          setSelectedParcel({
            ...parcel,
            source: 'chat_assistant',
          });
        }}
        externalMessage={externalChatMessage}
        onExternalMessageHandled={() => setExternalChatMessage(null)}
      />

      {/* SIREN Modal */}
      {sirenModal && sirenModal.proprietaire_siren && (
        <SirenModal 
          parcel={sirenModal} 
          onClose={() => setSirenModal(null)} 
        />
      )}

      {/* Compare bar */}
      {compareList.length >= 2 && (
        <div className="fixed bottom-0 left-0 right-0 z-50 p-3 flex items-center justify-between"
          style={{ background: '#12121aee', borderTop: '2px solid #3b82f6', backdropFilter: 'blur(10px)' }}
          data-testid="compare-bar">
          <div className="flex gap-2">
            {compareList.map(p => (
              <div key={p.parcel_id} className="px-3 py-1 text-xs font-mono flex items-center gap-2" style={{ background: '#1f1f2e', color: '#e8e8ed', borderRadius: 4 }}>
                {p.commune || p.ref_cadastrale} — {p.score?.score || 0}/100
                <button onClick={() => removeFromCompare(p.parcel_id)} style={{ color: '#ff4757' }} data-testid="compare-remove-btn">×</button>
              </div>
            ))}
          </div>
          <button onClick={() => setShowComparePanel(true)}
            className="px-4 py-2 text-xs font-mono uppercase rounded hover:opacity-90 transition-opacity"
            style={{ background: '#3b82f6', color: '#fff' }}
            data-testid="compare-open-btn">
            Comparer
          </button>
        </div>
      )}

      {/* Compare panel modal */}
      {showComparePanel && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center" style={{ background: '#0008' }}>
          <div className="w-full max-w-4xl max-h-[85vh] overflow-auto rounded-lg p-4" style={{ background: '#0a0a0f', border: '1px solid #1f1f2e' }}>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold" style={{ color: '#e8e8ed' }}>Comparaison de parcelles</h2>
              <button onClick={() => setShowComparePanel(false)} style={{ color: '#8f8f9d' }} data-testid="compare-close-btn"><X size={20} /></button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-xs font-mono" style={{ color: '#e8e8ed' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #1f1f2e' }}>
                    <th className="py-2 px-3 text-left" style={{ color: '#8f8f9d' }}>Critère</th>
                    {compareList.map(p => (
                      <th key={p.parcel_id} className="py-2 px-3 text-center" style={{ color: '#00d4aa' }}>
                        {p.commune || p.ref_cadastrale}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[
                    { label: 'Score', render: p => { const s = p.score?.score || 0; const c = s >= 70 ? '#2ed573' : s >= 40 ? '#ffa502' : '#ff4757'; return <span style={{color: c, fontWeight: 'bold'}}>{s}/100</span>; }},
                    { label: 'Verdict', render: p => <VerdictBadge verdict={p.score?.verdict} /> },
                    { label: 'Surface', render: p => `${p.surface_ha?.toFixed(2) || '-'} ha` },
                    { label: 'Dist. HTB', render: p => p.dist_poste_htb_m ? `${(p.dist_poste_htb_m/1000).toFixed(1)} km` : '-' },
                    { label: 'Tension', render: p => p.tension_htb_kv ? `${p.tension_htb_kv} kV` : '-' },
                    { label: 'MW dispo', render: p => `${p.mw_dispo || '-'} (${p.zone_saturation || '-'})` },
                    { label: 'Zone PLU', render: p => p.plu_zone || '-' },
                    { label: 'Prix DVF', render: p => p.dvf_prix_median_m2 ? `${p.dvf_prix_median_m2} €/m²` : '-' },
                    { label: "Cours d'eau", render: p => p.dist_cours_eau_m ? `${p.nom_cours_eau || '-'}: ${(p.dist_cours_eau_m/1000).toFixed(1)}km` : '-' },
                    { label: 'Route', render: p => p.dist_route_m ? `${p.nom_route || '-'}: ${(p.dist_route_m/1000).toFixed(1)}km` : '-' },
                    { label: 'Fibre', render: p => p.dist_backbone_fibre_m ? `${(p.dist_backbone_fibre_m/1000).toFixed(1)} km` : '-' },
                    { label: 'Risques', render: p => (p.score?.flags || []).join(', ') || 'Aucun' },
                    { label: 'Projet Fos', render: p => p.projet_fos || '-' },
                  ].map((row, ri) => (
                    <tr key={ri} style={{ borderBottom: '1px solid #1f1f2e08', background: ri % 2 === 0 ? '#12121a' : 'transparent' }}>
                      <td className="py-2 px-3" style={{ color: '#8f8f9d' }}>{row.label}</td>
                      {compareList.map(p => (
                        <td key={p.parcel_id} className="py-2 px-3 text-center">{row.render(p)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// SIREN Modal Component
function SirenModal({ parcel, onClose }) {
  const siren = parcel.proprietaire_siren;
  
  if (!siren) return null;
  
  return (
    <div 
      className="fixed inset-0 z-[2000] flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.8)' }}
      onClick={onClose}
    >
      <div 
        className="w-full max-w-lg"
        style={{ background: '#12121a', border: '1px solid #1f1f2e' }}
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div 
          className="flex items-center justify-between p-4"
          style={{ borderBottom: '1px solid #1f1f2e' }}
        >
          <div className="flex items-center gap-3">
            <Building2 size={20} style={{ color: '#3b82f6' }} />
            <div>
              <h3 className="font-bold" style={{ color: '#e8e8ed' }}>
                {siren.raison_sociale}
              </h3>
              <p className="text-xs" style={{ color: '#8f8f9d' }}>
                Fiche entreprise
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="text-[#8f8f9d] hover:text-[#e8e8ed]"
          >
            <X size={20} />
          </button>
        </div>
        
        {/* Content */}
        <div className="p-4 space-y-4">
          {/* Identifiants */}
          <div className="grid grid-cols-2 gap-4">
            <div className="panel p-3">
              <p className="text-xs font-mono uppercase mb-1" style={{ color: '#8f8f9d' }}>SIREN</p>
              <p className="text-lg font-mono font-bold" style={{ color: '#00d4aa' }}>
                {siren.siren}
              </p>
            </div>
            <div className="panel p-3">
              <p className="text-xs font-mono uppercase mb-1" style={{ color: '#8f8f9d' }}>SIRET (siège)</p>
              <p className="text-lg font-mono font-bold" style={{ color: '#e8e8ed' }}>
                {siren.siret}
              </p>
            </div>
          </div>
          
          {/* Infos société */}
          <div className="panel p-3 space-y-2">
            <div className="flex justify-between text-xs">
              <span style={{ color: '#8f8f9d' }}>Forme juridique</span>
              <span className="font-mono badge badge-info">{siren.forme_juridique}</span>
            </div>
            <div className="flex justify-between text-xs">
              <span style={{ color: '#8f8f9d' }}>Capital social</span>
              <span className="font-mono" style={{ color: '#e8e8ed' }}>
                {(siren.capital / 1000000).toFixed(0)} M€
              </span>
            </div>
            <div className="flex justify-between text-xs">
              <span style={{ color: '#8f8f9d' }}>Date création</span>
              <span className="font-mono" style={{ color: '#e8e8ed' }}>
                {siren.date_creation}
              </span>
            </div>
            <div className="flex justify-between text-xs">
              <span style={{ color: '#8f8f9d' }}>Effectif</span>
              <span className="font-mono" style={{ color: '#e8e8ed' }}>
                {siren.effectif}
              </span>
            </div>
          </div>
          
          {/* Activité */}
          <div className="panel p-3 space-y-2">
            <div className="flex justify-between text-xs">
              <span style={{ color: '#8f8f9d' }}>Code NAF</span>
              <span className="font-mono" style={{ color: '#3b82f6' }}>
                {siren.code_naf}
              </span>
            </div>
            <div className="text-xs">
              <span style={{ color: '#8f8f9d' }}>Activité: </span>
              <span style={{ color: '#e8e8ed' }}>{siren.activite}</span>
            </div>
          </div>
          
          {/* Adresse */}
          <div className="panel p-3">
            <p className="text-xs font-mono uppercase mb-1" style={{ color: '#8f8f9d' }}>Adresse siège</p>
            <p className="text-sm" style={{ color: '#e8e8ed' }}>
              {siren.adresse}
            </p>
          </div>
          
          {/* Parcelle concernée */}
          <div 
            className="p-3 flex items-center justify-between"
            style={{ background: '#0a0a0f' }}
          >
            <div>
              <p className="text-xs" style={{ color: '#8f8f9d' }}>Parcelle concernée</p>
              <p className="font-mono text-sm" style={{ color: '#e8e8ed' }}>
                {parcel.ref_cadastrale} · {parcel.commune}
              </p>
            </div>
            <a
              href={`https://www.pappers.fr/entreprise/${siren.siren}`}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary flex items-center gap-1"
            >
              Voir sur Pappers
              <ExternalLink size={12} />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

// Layer toggle component
function LayerToggle({ label, color, icon, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className="w-full flex items-center justify-between px-2 py-1.5 text-xs hover:bg-[#1f1f2e] transition-colors"
      style={{ color: active ? '#e8e8ed' : '#8f8f9d' }}
    >
      <span className="flex items-center gap-2">
        <span style={{ color, fontSize: icon ? 12 : 10 }}>
          {icon || '●'}
        </span>
        {label}
      </span>
      {active ? <Eye size={12} /> : <EyeOff size={12} />}
    </button>
  );
}

// Parcel Detail Panel
function ParcelDetail({ parcel, onClose, onShowSiren, addToCompare, compareList }) {
  const score = parcel.score || {};
  
  return (
    <div className="flex flex-col h-full overflow-auto">
      {/* Header */}
      <div className="panel-header flex items-center justify-between">
        <div>
          <h3 className="font-bold" style={{ color: '#e8e8ed' }}>{parcel.commune}</h3>
          <p className="text-xs" style={{ color: '#8f8f9d' }}>{parcel.region} · {parcel.departement}</p>
        </div>
        <button onClick={onClose} className="text-[#8f8f9d] hover:text-[#e8e8ed]">
          <XCircle size={18} />
        </button>
      </div>

      <div className="p-4 space-y-4">
        {/* Verdict + Score */}
        <div className="flex items-center gap-3">
          <VerdictBadge verdict={score.verdict} />
          <span className="text-2xl font-mono font-bold" style={{ color: getScoreColor(score.score || 0) }}>
            {(score.score || 0)}/100
          </span>
        </div>

        {/* Resume */}
        {score.resume && (
          <p className="text-xs leading-relaxed" style={{ color: '#c8c8d5', background: '#0a0a0f', padding: 8, borderRadius: 4, border: '1px solid #1f1f2e' }}>
            {score.resume}
          </p>
        )}

        {/* Score breakdown */}
        {score.detail && (
          <div className="panel p-3">
            <p className="text-xs font-mono uppercase mb-2" style={{ color: '#8f8f9d' }}>Détail du score</p>
            <div className="space-y-1.5">
              <DetailBar label="Distance RTE" value={score.detail.distance_rte || 0} max={40} />
              <DetailBar label="MW disponibles" value={score.detail.mw_disponibles || 0} max={30} />
              <DetailBar label="PLU" value={score.detail.plu || 0} max={20} />
              <DetailBar label="Surface" value={score.detail.surface || 0} max={10} />
              {score.detail.malus < 0 && (
                <div className="flex justify-between text-xs mt-1">
                  <span style={{ color: '#ff4757' }}>Malus</span>
                  <span className="font-mono font-bold" style={{ color: '#ff4757' }}>{score.detail.malus}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Flags */}
        {score.flags && score.flags.length > 0 && (
          <div className="panel p-3">
            <p className="text-xs font-mono uppercase mb-2" style={{ color: '#ff4757' }}>Risques</p>
            <div className="space-y-1">
              {score.flags.map((f, i) => (
                <p key={i} className="text-xs flex items-center gap-1" style={{ color: '#ff4757' }}>
                  <AlertTriangle size={10} /> {f}
                </p>
              ))}
            </div>
          </div>
        )}

        {/* Key metrics */}
        <div className="grid grid-cols-2 gap-3">
          <div className="panel p-3">
            <p className="text-xs font-mono uppercase" style={{ color: '#8f8f9d' }}>Surface</p>
            <p className="text-lg font-mono font-bold" style={{ color: '#e8e8ed' }}>
              {parcel.surface_ha?.toFixed(1)} ha
            </p>
          </div>
          <div className="panel p-3">
            <p className="text-xs font-mono uppercase" style={{ color: '#8f8f9d' }}>MW dispo</p>
            <p className="text-lg font-mono font-bold" style={{ color: '#00d4aa' }}>
              {parcel.mw_dispo || parcel.zone_saturation || '-'}
            </p>
          </div>
          <div className="panel p-3">
            <p className="text-xs font-mono uppercase" style={{ color: '#8f8f9d' }}>Dist. HTB</p>
            <p className="text-lg font-mono font-bold" style={{ color: '#3b82f6' }}>
              {parcel.dist_poste_htb_m ? `${(parcel.dist_poste_htb_m/1000).toFixed(1)} km` : '-'}
            </p>
          </div>
          <div className="panel p-3">
            <p className="text-xs font-mono uppercase" style={{ color: '#8f8f9d' }}>Zone PLU</p>
            <p className="text-lg font-mono font-bold" style={{ color: '#e8e8ed' }}>
              {parcel.plu_zone || '-'}
            </p>
          </div>
        </div>

        {/* Propriétaire & Foncier */}
        <div className="panel p-3">
          <p className="text-xs font-mono uppercase mb-2" style={{ color: '#8f8f9d' }}>Propriétaire & Foncier</p>
          <div className="space-y-2">
            <div>
              <p className="text-sm font-bold flex items-center gap-2" style={{ color: '#e8e8ed' }}>
                <Building2 size={14} style={{ color: '#3b82f6' }} />
                {parcel.proprietaire_nom || 'Propriétaire inconnu'}
              </p>
              <p className="text-xs" style={{ color: '#8f8f9d' }}>
                {parcel.proprietaire_type === 'sci' ? 'SCI / Société civile' : 
                 parcel.proprietaire_type === 'fonciere' ? 'Foncière / Investisseur' :
                 parcel.proprietaire_type === 'prive' ? 'Propriétaire privé' : 
                 'Type inconnu'}
              </p>
            </div>
            <div className="flex justify-between items-center text-xs pt-2" style={{ borderTop: '1px solid #1f1f2e' }}>
              <span style={{ color: '#8f8f9d' }}>Réf. cadastrale</span>
              <a
                href={`https://www.google.com/maps/@${parcel.latitude},${parcel.longitude},17z/data=!3m1!1e1`}
                target="_blank"
                rel="noopener noreferrer"
                className="font-mono flex items-center gap-1 hover:underline"
                style={{ color: '#3b82f6' }}
                data-testid="ref-cadastrale-btn"
              >
                {parcel.ref_cadastrale || '-'}
                <ExternalLink size={10} />
              </a>
            </div>
            {parcel.proprietaire_siren && (
              <div className="flex justify-between text-xs">
                <span style={{ color: '#8f8f9d' }}>SIREN</span>
                <button
                  onClick={() => onShowSiren && onShowSiren(parcel)}
                  className="font-mono flex items-center gap-1 hover:underline"
                  style={{ color: '#00d4aa' }}
                  data-testid="siren-btn"
                >
                  {parcel.proprietaire_siren.siren}
                  <ExternalLink size={10} />
                </button>
              </div>
            )}
            <div className="flex justify-between text-xs">
              <span style={{ color: '#8f8f9d' }}>Prix DVF (€/m²)</span>
              <span className="font-mono" style={{ color: '#ffa502' }}>
                {parcel.dvf_prix_median_m2 ? `${parcel.dvf_prix_median_m2} €` : parcel.dvf_prix_m2_p50 ? `${parcel.dvf_prix_m2_p50.toFixed(0)} €` : '-'}
              </span>
            </div>
            <div className="flex justify-between text-xs">
              <span style={{ color: '#8f8f9d' }}>Transactions DVF</span>
              <span className="font-mono" style={{ color: '#8f8f9d' }}>
                {parcel.dvf_nb_transactions || 0} dans le secteur
              </span>
            </div>
            <div className="flex justify-between text-xs">
              <span style={{ color: '#8f8f9d' }}>Type de site</span>
              <span className={`badge ${
                parcel.site_type === 'zac' ? 'badge-success' :
                parcel.site_type === 'friche_industrielle' ? 'badge-info' :
                parcel.site_type === 'brownfield' ? 'badge-warning' : ''
              }`}>
                {parcel.site_type?.replace('_', ' ') || 'greenfield'}
              </span>
            </div>
          </div>
        </div>

        {/* Infrastructure */}
        <div className="panel p-3">
          <p className="text-xs font-mono uppercase mb-2" style={{ color: '#8f8f9d' }}>Infrastructure</p>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between">
              <span style={{ color: '#8f8f9d' }}>Poste HTB</span>
              <span className="font-mono" style={{ color: '#e8e8ed' }}>
                {parcel.dist_poste_htb_m ? `${(parcel.dist_poste_htb_m/1000).toFixed(1)} km` : '-'}
              </span>
            </div>
            <div className="flex justify-between">
              <span style={{ color: '#8f8f9d' }}>Tension HTB</span>
              <span className="font-mono" style={{ color: parcel.tension_htb_kv >= 225 ? '#00d4aa' : '#ffa502' }}>
                {parcel.tension_htb_kv ? `${parcel.tension_htb_kv} kV` : '-'}
              </span>
            </div>
            <div className="flex justify-between">
              <span style={{ color: '#8f8f9d' }}>Zone saturation</span>
              <span className={`badge ${
                parcel.zone_saturation === 'disponible' ? 'badge-success' :
                parcel.zone_saturation === 'tendu' ? 'badge-warning' :
                parcel.zone_saturation === 'sature' ? 'badge-danger' : ''
              }`}>
                {parcel.zone_saturation || 'inconnu'}
              </span>
            </div>
            <div className="flex justify-between">
              <span style={{ color: '#8f8f9d' }}>Landing point</span>
              <span className="font-mono" style={{ color: '#e8e8ed' }}>
                {parcel.landing_point_nom || '-'} ({parcel.dist_landing_point_km?.toFixed(0)} km)
              </span>
            </div>
            <div className="flex justify-between">
              <span style={{ color: '#8f8f9d' }}>Câbles sous-marins</span>
              <span className="font-mono" style={{ color: '#00d4aa' }}>
                {parcel.landing_point_nb_cables || 0} câbles
              </span>
            </div>
          </div>
        </div>

        {/* Future 400kV Line — Raccordement futur */}
        {parcel.dist_future_400kv_m != null && (
          <div className="panel p-3" data-testid="future-400kv-section">
            <p className="text-xs font-mono uppercase mb-2" style={{ color: '#ff0040' }}>
              Future ligne 400 kV Fos → Jonquières
            </p>
            <div className="space-y-1 text-xs">
              <div className="flex justify-between">
                <span style={{ color: '#8f8f9d' }}>Distance à la ligne</span>
                <span className="font-mono font-bold" style={{ 
                  color: parcel.dist_future_400kv_m < 1000 ? '#ff4757' 
                       : parcel.dist_future_400kv_m < 3000 ? '#ffa502' 
                       : parcel.dist_future_400kv_m < 5000 ? '#ffd32a' 
                       : '#8f8f9d' 
                }}>
                  {parcel.dist_future_400kv_m < 1000 
                    ? `${parcel.dist_future_400kv_m} m` 
                    : `${(parcel.dist_future_400kv_m / 1000).toFixed(1)} km`}
                </span>
              </div>
              {parcel.future_400kv_buffer && (
                <div className="flex justify-between">
                  <span style={{ color: '#8f8f9d' }}>Zone</span>
                  <span className={`badge ${
                    parcel.future_400kv_buffer === '1km' ? 'badge-danger' :
                    parcel.future_400kv_buffer === '3km' ? 'badge-warning' : 'badge-info'
                  }`}>
                    {parcel.future_400kv_buffer === '1km' ? 'Zone chaude (1 km)' :
                     parcel.future_400kv_buffer === '3km' ? 'Zone stratégique (3 km)' :
                     'Zone opportunité (5 km)'}
                  </span>
                </div>
              )}
              <div className="flex justify-between">
                <span style={{ color: '#8f8f9d' }}>Bonus scoring</span>
                <span className="font-mono font-bold" style={{ color: '#00d4aa' }}>
                  +{parcel.future_400kv_score_bonus || 0} pts
                </span>
              </div>
              {parcel.future_grid_potential && (
                <div className="flex justify-between mt-1 pt-1" style={{ borderTop: '1px solid #1f1f2e' }}>
                  <span style={{ color: '#8f8f9d' }}>Potentiel réseau futur</span>
                  <span className="font-mono font-bold" style={{ 
                    color: parcel.future_grid_potential.future_grid_potential_score >= 60 ? '#00d4aa' 
                         : parcel.future_grid_potential.future_grid_potential_score >= 40 ? '#ffa502' 
                         : '#8f8f9d' 
                  }}>
                    {parcel.future_grid_potential.future_grid_potential_score}/100
                  </span>
                </div>
              )}
              {parcel.future_400kv_buffer && (
                <p className="text-[10px] mt-2 px-2 py-1 rounded" style={{ 
                  background: '#ff004015', color: '#ff4757', border: '1px solid #ff004030' 
                }}>
                  Potentiel raccordement futur élevé — Mise en service estimée ~2029
                </p>
              )}
            </div>
          </div>
        )}

        {/* Score breakdown */}
        <div className="panel p-3">
          <p className="text-xs font-mono uppercase mb-3" style={{ color: '#8f8f9d' }}>Score technique</p>
          <div className="space-y-2">
            <ScoreBar label="Électricité" value={score.score_electricite} max={44} />
            <ScoreBar label="Fibre" value={score.score_fibre} max={23} />
            <ScoreBar label="Eau" value={score.score_eau} max={12} />
            <ScoreBar label="Surface" value={score.score_surface} max={11} />
            <ScoreBar label="Marché" value={score.score_marche} max={8} />
            <ScoreBar label="Climat" value={score.score_climat} max={8} />
          </div>
          {score.malus_total > 0 && (
            <div className="mt-2 pt-2" style={{ borderTop: '1px solid #1f1f2e' }}>
              <p className="text-xs" style={{ color: '#ff4757' }}>
                Malus: -{score.malus_total?.toFixed(0)} pts
              </p>
            </div>
          )}
        </div>

        {/* Urbanisme — PLU Scoring DC */}
        <div className="panel p-3" data-testid="plu-scoring-section">
          <p className="text-xs font-mono uppercase mb-2" style={{ color: '#8f8f9d' }}>Urbanisme — Scoring PLU</p>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-bold font-mono px-2 py-0.5 rounded" style={{ 
              color: parcel.plu_zone === 'U' ? '#2ed573' 
                   : parcel.plu_zone === 'AU' ? '#ffa502' 
                   : parcel.plu_zone === 'A' ? '#8b5cf6'
                   : parcel.plu_zone === 'N' ? '#3b82f6' 
                   : '#8f8f9d',
              background: parcel.plu_zone === 'U' ? '#2ed57315' 
                        : parcel.plu_zone === 'AU' ? '#ffa50215' 
                        : parcel.plu_zone === 'A' ? '#8b5cf615'
                        : parcel.plu_zone === 'N' ? '#3b82f615' 
                        : '#8f8f9d15',
            }}>
              PLU: {parcel.plu_zone || 'inconnu'}
              {parcel.plu_libelle ? ` (${parcel.plu_libelle})` : ''}
            </span>
          </div>
          {parcel.plu_libelong && (
            <p className="text-xs mb-2" style={{ color: '#8f8f9d' }}>{parcel.plu_libelong}</p>
          )}
          
          {/* PLU Score bar */}
          {parcel.plu_scoring && (
            <div className="space-y-2 mt-2">
              <div className="flex items-center justify-between">
                <span className="text-xs" style={{ color: '#8f8f9d' }}>Score PLU DC</span>
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-sm" style={{ 
                    color: parcel.plu_scoring.plu_score >= 85 ? '#2ed573' 
                         : parcel.plu_scoring.plu_score >= 65 ? '#ffa502' 
                         : parcel.plu_scoring.plu_score >= 45 ? '#f0932b' 
                         : '#ff4757' 
                  }}>
                    {parcel.plu_scoring.plu_score}/100
                  </span>
                  <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                    parcel.plu_scoring.plu_status === 'FAVORABLE' ? 'text-green-400 bg-green-400/10' :
                    parcel.plu_scoring.plu_status === 'WATCHLIST' ? 'text-yellow-400 bg-yellow-400/10' :
                    parcel.plu_scoring.plu_status === 'CONDITIONAL' ? 'text-orange-400 bg-orange-400/10' :
                    parcel.plu_scoring.plu_status === 'EXCLUDED' ? 'text-red-500 bg-red-500/10' :
                    'text-red-400 bg-red-400/10'
                  }`} data-testid="plu-status-badge">
                    {parcel.plu_scoring.plu_status}
                  </span>
                </div>
              </div>
              {/* Score bar */}
              <div className="w-full h-1.5 rounded-full" style={{ background: '#1f1f2e' }}>
                <div className="h-full rounded-full transition-all" style={{ 
                  width: `${parcel.plu_scoring.plu_score}%`,
                  background: parcel.plu_scoring.plu_score >= 85 ? '#2ed573' 
                            : parcel.plu_scoring.plu_score >= 65 ? '#ffa502' 
                            : parcel.plu_scoring.plu_score >= 45 ? '#f0932b' 
                            : '#ff4757',
                }} />
              </div>
              
              {/* Risk level */}
              <div className="flex items-center justify-between text-xs">
                <span style={{ color: '#8f8f9d' }}>Risque urbanistique</span>
                <span className="font-mono" style={{ 
                  color: parcel.plu_scoring.urbanism_risk === 'faible' ? '#2ed573'
                       : parcel.plu_scoring.urbanism_risk === 'modere' ? '#ffa502'
                       : '#ff4757' 
                }}>
                  {parcel.plu_scoring.urbanism_risk}
                </span>
              </div>
              
              {/* Recommended action */}
              <div className="flex items-center justify-between text-xs">
                <span style={{ color: '#8f8f9d' }}>Action recommandée</span>
                <span className={`font-mono text-[10px] px-1.5 py-0.5 rounded ${
                  parcel.plu_scoring.recommended_action === 'prospect_now' ? 'text-green-400 bg-green-400/10' :
                  parcel.plu_scoring.recommended_action === 'check_regulation_and_mayor' ? 'text-yellow-400 bg-yellow-400/10' :
                  parcel.plu_scoring.recommended_action === 'manual_review' ? 'text-orange-400 bg-orange-400/10' :
                  'text-red-400 bg-red-400/10'
                }`}>
                  {parcel.plu_scoring.recommended_action === 'prospect_now' ? 'Prospecter maintenant' :
                   parcel.plu_scoring.recommended_action === 'check_regulation_and_mayor' ? 'Vérifier réglementation' :
                   parcel.plu_scoring.recommended_action === 'manual_review' ? 'Revue manuelle' :
                   'Rejeter'}
                </span>
              </div>
              
              {/* Flags */}
              {parcel.plu_scoring.flags && parcel.plu_scoring.flags.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {parcel.plu_scoring.flags.map((flag, idx) => (
                    <span key={idx} className="text-[9px] px-1 py-0.5 rounded" style={{ 
                      background: flag.includes('bonus') || flag.includes('favorable') ? '#2ed57315' : '#ff475715',
                      color: flag.includes('bonus') || flag.includes('favorable') ? '#2ed573' : '#ff4757',
                    }}>
                      {flag.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              )}
              
              {/* Exclusion reason */}
              {parcel.plu_scoring.exclusion_reason && (
                <p className="text-[10px] px-2 py-1 rounded mt-1" style={{ 
                  background: '#ff475715', color: '#ff4757', border: '1px solid #ff475730' 
                }}>
                  {parcel.plu_scoring.exclusion_reason}
                </p>
              )}
              
              {/* GPU dynamic source indicator */}
              {parcel.plu_scoring.gpu_source === 'dynamic' && (
                <div className="mt-2 space-y-1">
                  <div className="flex items-center gap-1 text-[9px]">
                    <span className="px-1.5 py-0.5 rounded" style={{ background: '#00d4aa15', color: '#00d4aa', border: '1px solid #00d4aa33' }}>
                      GPU Dynamique
                    </span>
                    {parcel.plu_scoring.plu_score_base != null && parcel.plu_scoring.plu_score_dynamic_adj !== 0 && (
                      <span style={{ color: '#8f8f9d' }}>
                        Base {parcel.plu_scoring.plu_score_base} {parcel.plu_scoring.plu_score_dynamic_adj > 0 ? '+' : ''}{parcel.plu_scoring.plu_score_dynamic_adj}
                      </span>
                    )}
                  </div>
                  {parcel.plu_scoring.gpu_data?.prescriptions_count > 0 && (
                    <p className="text-[9px]" style={{ color: '#8f8f9d' }}>
                      {parcel.plu_scoring.gpu_data.prescriptions_count} prescription(s) analysée(s)
                    </p>
                  )}
                  {parcel.plu_scoring.gpu_data?.informations_count > 0 && (
                    <p className="text-[9px]" style={{ color: '#8f8f9d' }}>
                      {parcel.plu_scoring.gpu_data.informations_count} information(s) GPU
                    </p>
                  )}
                  {parcel.plu_scoring.gpu_data?.risk_labels?.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {parcel.plu_scoring.gpu_data.risk_labels.map((r, idx) => (
                        <span key={idx} className="text-[9px] px-1 py-0.5 rounded" style={{ 
                          background: '#ff475715', color: '#ff4757' 
                        }}>
                          {r}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}
              
              {/* Confidence indicator */}
              {parcel.plu_scoring.confidence && (
                <div className="flex items-center justify-between text-[10px] mt-2 pt-2" style={{ borderTop: '1px solid #1f1f2e' }} data-testid="plu-confidence">
                  <span style={{ color: '#8f8f9d' }}>Fiabilité</span>
                  <div className="flex items-center gap-1.5">
                    <div className="flex gap-0.5">
                      {[1, 2, 3].map(i => (
                        <div key={i} className="w-2 h-2 rounded-full" style={{ 
                          background: parcel.plu_scoring.confidence === 'haute' ? (i <= 3 ? '#2ed573' : '#1f1f2e')
                                    : parcel.plu_scoring.confidence === 'moyenne' ? (i <= 2 ? '#ffa502' : '#1f1f2e')
                                    : (i <= 1 ? '#ff4757' : '#1f1f2e'),
                        }} />
                      ))}
                    </div>
                    <span className="font-mono" style={{ 
                      color: parcel.plu_scoring.confidence === 'haute' ? '#2ed573' 
                           : parcel.plu_scoring.confidence === 'moyenne' ? '#ffa502' 
                           : '#ff4757' 
                    }}>
                      {parcel.plu_scoring.confidence}
                    </span>
                  </div>
                </div>
              )}
              {parcel.plu_scoring.confidence_detail && (
                <p className="text-[9px] mt-0.5" style={{ color: '#8f8f9d55' }}>
                  {parcel.plu_scoring.confidence_detail}
                </p>
              )}
            </div>
          )}
          
          {/* Legacy scoring compatibility display */}
          {!parcel.plu_scoring && (
            <div className="flex items-center justify-between text-xs mt-1">
              <span style={{ color: '#8f8f9d' }}>Deal Friction Index</span>
              <span className="font-mono" style={{ color: score.urba_deal_friction_index < 30 ? '#00d4aa' : '#ffa502' }}>
                {score.urba_deal_friction_index || 0}/100
              </span>
            </div>
          )}
        </div>

        {/* Raccordement */}
        <div className="panel p-3">
          <p className="text-xs font-mono uppercase mb-2" style={{ color: '#8f8f9d' }}>Raccordement électrique</p>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between">
              <span style={{ color: '#8f8f9d' }}>Type travaux</span>
              <span className="font-mono" style={{ color: '#e8e8ed' }}>
                {score.racc_type_travaux?.replace(/_/g, ' ') || '-'}
              </span>
            </div>
            <div className="flex justify-between">
              <span style={{ color: '#8f8f9d' }}>Délai estimé</span>
              <span className="font-mono" style={{ color: '#3b82f6' }}>
                {score.racc_delai_min_mois || '-'}-{score.racc_delai_max_mois || '-'} mois
              </span>
            </div>
            <div className="flex justify-between">
              <span style={{ color: '#8f8f9d' }}>Proba obtention MW</span>
              <span className="font-mono" style={{ color: (score.racc_proba_obtention || 0) > 0.6 ? '#00d4aa' : '#ffa502' }}>
                {((score.racc_proba_obtention || 0) * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>

        {/* Economics */}
        <div className="panel p-3">
          <p className="text-xs font-mono uppercase mb-2" style={{ color: '#8f8f9d' }}>Économique</p>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between">
              <span style={{ color: '#8f8f9d' }}>CAPEX P50</span>
              <span className="font-mono" style={{ color: '#e8e8ed' }}>
                {score.capex_p50 ? `${(score.capex_p50 / 1e6).toFixed(0)} M€` : '-'}
              </span>
            </div>
            <div className="flex justify-between">
              <span style={{ color: '#8f8f9d' }}>€/MW</span>
              <span className="font-mono" style={{ color: '#e8e8ed' }}>
                {score.cout_mw_p50?.toFixed(1) || '-'} M€
              </span>
            </div>
            <div className="flex justify-between">
              <span style={{ color: '#8f8f9d' }}>EBITDA maturité</span>
              <span className="font-mono" style={{ color: '#00d4aa' }}>
                {score.ebitda_maturite ? `${(score.ebitda_maturite / 1e6).toFixed(1)} M€/an` : '-'}
              </span>
            </div>
          </div>
        </div>

        {/* DVF Prix foncier */}
        {parcel.dvf_prix_median_m2 > 0 && (
          <div className="panel p-3" data-testid="dvf-section">
            <p className="text-xs font-mono uppercase mb-2" style={{ color: '#8f8f9d' }}>DVF — Prix foncier (département)</p>
            <div className="space-y-1 text-xs">
              <div className="flex justify-between">
                <span style={{ color: '#8f8f9d' }}>Prix médian terrain</span>
                <span className="font-mono font-bold" style={{ color: '#ffa502' }}>
                  {parcel.dvf_prix_median_m2} €/m²
                </span>
              </div>
              <div className="flex justify-between">
                <span style={{ color: '#8f8f9d' }}>Fourchette (Q1-Q3)</span>
                <span className="font-mono" style={{ color: '#e8e8ed' }}>
                  {parcel.dvf_prix_q1_m2} - {parcel.dvf_prix_q3_m2} €/m²
                </span>
              </div>
              {parcel.surface_m2 > 0 && (
                <div className="flex justify-between mt-1 pt-1" style={{ borderTop: '1px solid #1f1f2e' }}>
                  <span style={{ color: '#8f8f9d' }}>Estimation terrain</span>
                  <span className="font-mono font-bold" style={{ color: '#00d4aa' }}>
                    {((parcel.surface_m2 * parcel.dvf_prix_median_m2) / 1e6).toFixed(2)} M€
                  </span>
                </div>
              )}
              <p className="text-[9px] mt-1" style={{ color: '#555' }}>{parcel.dvf_source}</p>
            </div>
          </div>
        )}

        {/* Projet RTE Fos-Jonquières */}
        {parcel.projet_fos && (
          <div className="p-3 rounded mb-3" style={{ background: '#ff475712', border: '1px solid #ff475733' }} data-testid="projet-fos-panel">
            <p className="text-xs font-mono uppercase font-bold mb-1" style={{ color: '#ff4757' }}>Projet RTE Fos-Jonquières</p>
            <p className="text-xs" style={{ color: '#e8e8ed' }}>{parcel.projet_fos}</p>
            <p className="text-[10px] mt-1 font-mono" style={{ color: '#ff475799' }}>+3700 MW · 400 M€ · Horizon 2029</p>
          </div>
        )}

        {/* Compare button */}
        {addToCompare && (
          <button
            onClick={() => addToCompare(parcel)}
            disabled={(compareList || []).length >= 3 || (compareList || []).find(p => p.parcel_id === parcel.parcel_id)}
            className="w-full flex items-center justify-center gap-2 py-2 text-xs font-mono uppercase rounded mb-2 hover:opacity-80 transition-opacity"
            style={{
              background: '#3b82f622', color: '#3b82f6', border: '1px solid #3b82f633',
              opacity: (compareList || []).length >= 3 || (compareList || []).find(p => p.parcel_id === parcel.parcel_id) ? 0.5 : 1
            }}
            data-testid="compare-add-btn"
          >
            {(compareList || []).find(p => p.parcel_id === parcel.parcel_id) ? 'Déjà ajouté' : `Comparer (${(compareList || []).length}/3)`}
          </button>
        )}

        {/* Google Maps + Street View links */}
        <div className="flex gap-2 mb-2">
          <a href={`https://www.google.com/maps/@${parcel.latitude},${parcel.longitude},17z/data=!3m1!1e3`}
            target="_blank" rel="noopener noreferrer"
            className="flex-1 flex items-center justify-center gap-1 py-2 text-xs font-mono rounded hover:opacity-80 transition-opacity"
            style={{ background: '#1f1f2e', color: '#8f8f9d', border: '1px solid #2a2a3e' }}
            data-testid="satellite-link">
            <MapIcon size={12} /> Satellite
          </a>
          <a href={`https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${parcel.latitude},${parcel.longitude}`}
            target="_blank" rel="noopener noreferrer"
            className="flex-1 flex items-center justify-center gap-1 py-2 text-xs font-mono rounded hover:opacity-80 transition-opacity"
            style={{ background: '#1f1f2e', color: '#8f8f9d', border: '1px solid #2a2a3e' }}
            data-testid="streetview-link">
            <Eye size={12} /> Street View
          </a>
        </div>

        {/* Export PDF */}
        <button
          onClick={async () => {
            try {
              const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/export/pdf`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(parcel),
              });
              if (!res.ok) {
                const errText = await res.text();
                console.error('PDF error:', res.status, errText);
                alert('Erreur lors de la génération du PDF.');
                return;
              }
              const blob = await res.blob();
              if (blob.size < 100) {
                alert('Le PDF généré est vide.');
                return;
              }
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `cockpit_immo_${parcel.commune || 'site'}.pdf`;
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
              URL.revokeObjectURL(url);
            } catch (e) {
              console.error('PDF export error:', e);
              alert('Erreur réseau lors de l export PDF.');
            }
          }}
          className="w-full flex items-center justify-center gap-2 py-2 text-xs font-mono uppercase rounded"
          style={{ background: '#00d4aa22', color: '#00d4aa', border: '1px solid #00d4aa33' }}
          data-testid="export-pdf-btn"
        >
          <FileDown size={14} />
          Exporter Fiche PDF
        </button>

        {/* Confidence */}
        <div className="flex items-center justify-between text-xs p-2" style={{ background: '#0a0a0f' }}>
          <span style={{ color: '#8f8f9d' }}>Source</span>
          <span className="font-mono" style={{ color: '#8f8f9d' }}>
            {parcel.source === 'chat_assistant' ? 'Chatbot IA' : 'Carte IGN'}
          </span>
        </div>
      </div>
    </div>
  );
}

// Score bar component
function ScoreBar({ label, value, max }) {
  const pct = max > 0 ? (value || 0) / max * 100 : 0;
  
  return (
    <div className="flex items-center gap-2">
      <span className="w-20 text-xs" style={{ color: '#8f8f9d' }}>{label}</span>
      <div className="flex-1 h-1" style={{ background: '#1f1f2e' }}>
        <div 
          className="h-full transition-all"
          style={{ 
            width: `${pct}%`,
            background: pct > 70 ? '#00d4aa' : pct > 40 ? '#ffa502' : '#ff4757'
          }}
        />
      </div>
      <span className="w-10 text-right text-xs font-mono" style={{ color: '#e8e8ed' }}>
        {(value || 0).toFixed(0)}
      </span>
    </div>
  );
}

// Detail bar for score breakdown in ParcelDetail
function DetailBar({ label, value, max }) {
  const pct = max > 0 ? Math.min(100, (value || 0) / max * 100) : 0;
  const color = pct >= 75 ? '#2ed573' : pct >= 50 ? '#ffa502' : pct >= 25 ? '#f0932b' : '#ff4757';
  return (
    <div className="flex items-center gap-2">
      <span className="w-24 text-xs text-right" style={{ color: '#8f8f9d' }}>{label}</span>
      <div className="flex-1 h-2 rounded-full" style={{ background: '#1f1f2e' }}>
        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="w-10 text-right text-xs font-mono" style={{ color }}>{value}/{max}</span>
    </div>
  );
}

// End of file

function EmptyStatePanel({ postes, onSendChat }) {
  const totalPostes = postes?.length || 0;

  const quickSearches = [
    { label: "PACA 2ha+", query: "Parcelles en PACA de 2 hectares minimum" },
    { label: "Fos-sur-Mer", query: "Parcelles à Fos-sur-Mer pour data center" },
    { label: "Hauts-de-France", query: "Parcelles en Hauts-de-France de 2 hectares minimum" },
    { label: "Score > 70", query: "Parcelles avec un score supérieur à 70 en PACA" },
    { label: "> 5 hectares", query: "Parcelles de 5 hectares minimum en France" },
    { label: "Étang de Berre", query: "Parcelles de 3 hectares près de l étang de Berre" },
  ];

  return (
    <div className="p-4 overflow-y-auto" style={{ maxHeight: '100%' }} data-testid="empty-state-panel">
      <h3 className="text-sm font-mono uppercase mb-4" style={{ color: '#00d4aa' }}>Cockpit Immo</h3>

      {/* Recherche rapide */}
      <div className="mb-4" data-testid="quick-search-section">
        <p className="text-[10px] font-mono uppercase mb-2" style={{ color: '#8f8f9d' }}>Recherche rapide</p>
        <div className="flex flex-wrap gap-1.5">
          {quickSearches.map((qs, i) => (
            <button
              key={i}
              onClick={() => onSendChat && onSendChat(qs.query)}
              className="px-2.5 py-1 text-[10px] font-mono rounded-full hover:opacity-80"
              style={{ background: '#1f1f2e', border: '1px solid #2a2a3e', color: '#8f8f9d' }}
              data-testid={`quick-search-${i}`}
            >
              {qs.label}
            </button>
          ))}
        </div>
      </div>

      {/* Projet Fos-Jonquières */}
      <div className="p-3 rounded mb-4" style={{ background: '#ff475712', border: '1px solid #ff475733' }} data-testid="fos-project-card">
        <p className="text-[10px] font-mono uppercase font-bold mb-1" style={{ color: '#ff4757' }}>Projet RTE Fos-Jonquières</p>
        <p className="text-[10px]" style={{ color: '#e8e8ed' }}>Nouvelle ligne 400kV 2 circuits</p>
        <p className="text-[9px]" style={{ color: '#8f8f9d' }}>Feuillane → Jonquières · ~65 km</p>
        <div className="flex gap-3 mt-2">
          <div className="text-center">
            <p className="text-sm font-bold" style={{ color: '#ff4757' }}>3700</p>
            <p className="text-[8px]" style={{ color: '#8f8f9d' }}>MW nouveaux</p>
          </div>
          <div className="text-center">
            <p className="text-sm font-bold" style={{ color: '#ffa502' }}>400</p>
            <p className="text-[8px]" style={{ color: '#8f8f9d' }}>M€ invest.</p>
          </div>
          <div className="text-center">
            <p className="text-sm font-bold" style={{ color: '#00d4aa' }}>2029</p>
            <p className="text-[8px]" style={{ color: '#8f8f9d' }}>horizon</p>
          </div>
        </div>
      </div>

      {/* Capacités réseau */}
      <div className="mb-4" data-testid="network-capacity-section">
        <p className="text-[10px] font-mono uppercase mb-2" style={{ color: '#8f8f9d' }}>Capacités réseau</p>
        {[
          { name: 'PACA', mw: '3258 MW', pct: '52%', color: '#2ed573', desc: '76 postes · 52 dispo · 12 sat.' },
          { name: 'Hauts-de-France', mw: '2925 MW', pct: '46%', color: '#2ed573', desc: '66 postes · 58 dispo · 5 sat.' },
          { name: 'Île-de-France', mw: 'SATURÉ', pct: '100%', color: '#ff4757', desc: '10 postes · 0 dispo · 10 sat.' },
        ].map((r, i) => (
          <div key={i} className="p-2 rounded mb-1" style={{ background: '#0a0a0f', border: '1px solid #1e1e35' }}>
            <div className="flex justify-between items-center">
              <span className="text-[10px] font-bold" style={{ color: '#e8e8ed' }}>{r.name}</span>
              <span className="text-[10px] font-mono" style={{ color: r.color }}>{r.mw}</span>
            </div>
            <p className="text-[9px]" style={{ color: '#555' }}>{r.desc}</p>
          </div>
        ))}
      </div>

      {/* Infrastructure KPIs */}
      <div className="mb-4" data-testid="infra-kpis">
        <p className="text-[10px] font-mono uppercase mb-2" style={{ color: '#8f8f9d' }}>Infrastructure</p>
        <div className="grid grid-cols-2 gap-2">
          {[
            { val: totalPostes || 1091, label: 'Postes HTB', color: '#00d4aa' },
            { val: 61, label: 'DC existants', color: '#3b82f6' },
            { val: 8, label: 'Landing points', color: '#8b5cf6' },
            { val: 49, label: 'Lignes THT', color: '#ffa502' },
          ].map((k, i) => (
            <div key={i} className="p-2 rounded text-center" style={{ background: '#0a0a0f', border: '1px solid #1e1e35' }}>
              <p className="text-lg font-bold font-mono" style={{ color: k.color }}>{k.val}</p>
              <p className="text-[8px]" style={{ color: '#8f8f9d' }}>{k.label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Guide rapide */}
      <div data-testid="quick-guide">
        <p className="text-[10px] font-mono uppercase mb-2" style={{ color: '#8f8f9d' }}>Comment utiliser</p>
        {[
          "Cliquez sur un poste HTB puis \"Parcelles à 5km\"",
          "Ou utilisez l'Assistant IA en bas à droite",
          "Sélectionnez une parcelle pour voir le score",
          "Comparez jusqu'à 3 parcelles côte-à-côte",
          "Exportez la Fiche PDF pour vos clients",
        ].map((step, i) => (
          <p key={i} className="text-[10px] mb-1" style={{ color: '#8f8f9d' }}>
            {i + 1}. {step}
          </p>
        ))}
      </div>
    </div>
  );
}
