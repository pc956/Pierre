import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  Server, Map as MapIcon, Table, Briefcase, Bell, Settings, LogOut, 
  Search, Filter, ChevronDown, Plus, Zap, Wifi, Droplets, Square,
  TrendingUp, Clock, AlertTriangle, CheckCircle, XCircle, RefreshCw,
  Layers, Eye, EyeOff, Anchor, Cable
} from 'lucide-react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap, Marker, Polyline } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Custom icons for map markers
const createIcon = (color, size = 10) => L.divIcon({
  className: 'custom-icon',
  html: `<div style="width:${size}px;height:${size}px;background:${color};border:2px solid #fff;border-radius:50%;box-shadow:0 2px 4px rgba(0,0,0,0.5);"></div>`,
  iconSize: [size, size],
  iconAnchor: [size/2, size/2],
});

const posteIcon = (tension) => {
  const color = tension >= 400 ? '#ff4757' : tension >= 225 ? '#ffa502' : '#3b82f6';
  return L.divIcon({
    className: 'poste-icon',
    html: `<div style="width:14px;height:14px;background:${color};border:2px solid #fff;transform:rotate(45deg);box-shadow:0 2px 4px rgba(0,0,0,0.5);"></div>`,
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

// Map component to handle bounds
function MapBounds({ parcels }) {
  const map = useMap();
  
  useEffect(() => {
    if (parcels.length > 0) {
      const bounds = parcels.map(p => [p.latitude, p.longitude]);
      if (bounds.length > 0) {
        map.fitBounds(bounds, { padding: [50, 50] });
      }
    }
  }, [parcels, map]);
  
  return null;
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
    'CONDITIONNEL': 'verdict-conditionnel',
    'NO_GO': 'verdict-no-go'
  };
  
  const icons = {
    'GO': <CheckCircle size={12} />,
    'CONDITIONNEL': <AlertTriangle size={12} />,
    'NO_GO': <XCircle size={12} />
  };
  
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-mono uppercase ${styles[verdict] || 'verdict-conditionnel'}`}>
      {icons[verdict]}
      {verdict?.replace('_', ' ')}
    </span>
  );
}

export default function Dashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeView, setActiveView] = useState('map');
  const [parcels, setParcels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedParcel, setSelectedParcel] = useState(null);
  const [projectType, setProjectType] = useState('colocation_t3');
  const [regionFilter, setRegionFilter] = useState('');
  const [scoreMin, setScoreMin] = useState(0);
  const [stats, setStats] = useState(null);
  
  // Map layers data
  const [landingPoints, setLandingPoints] = useState([]);
  const [dcExistants, setDcExistants] = useState([]);
  const [submarineCables, setSubmarineCables] = useState([]);
  const [electricalAssets, setElectricalAssets] = useState([]);
  
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
  });

  // Fetch parcels
  useEffect(() => {
    fetchParcels();
    fetchStats();
  }, [projectType, regionFilter, scoreMin]);

  // Fetch map layers data
  useEffect(() => {
    fetchMapLayers();
  }, []);

  const fetchParcels = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        project_type: projectType,
        limit: '100'
      });
      if (regionFilter) params.append('region', regionFilter);
      if (scoreMin > 0) params.append('score_min', scoreMin.toString());
      
      const response = await axios.get(`${API}/parcels?${params}`, { withCredentials: true });
      setParcels(response.data.parcels || []);
    } catch (error) {
      console.error('Error fetching parcels:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/admin/stats`, { withCredentials: true });
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchMapLayers = async () => {
    try {
      const [lpRes, dcRes, cablesRes, elecRes] = await Promise.all([
        axios.get(`${API}/map/landing-points`),
        axios.get(`${API}/map/dc`),
        axios.get(`${API}/map/submarine-cables`),
        axios.get(`${API}/map/electrical-assets`),
      ]);
      setLandingPoints(lpRes.data.landing_points || []);
      setDcExistants(dcRes.data.dc_existants || []);
      setSubmarineCables(cablesRes.data.submarine_cables || []);
      setElectricalAssets(elecRes.data.electrical_assets || []);
    } catch (error) {
      console.error('Error fetching map layers:', error);
    }
  };

  const handleParcelClick = (parcel) => {
    setSelectedParcel(parcel);
  };

  const toggleLayer = (layerName) => {
    setLayers(prev => ({ ...prev, [layerName]: !prev[layerName] }));
  };

  const PROJECT_TYPES = [
    { value: 'colocation_t3', label: 'Colocation T3' },
    { value: 'colocation_t4', label: 'Colocation T4' },
    { value: 'hyperscale', label: 'Hyperscale' },
    { value: 'edge', label: 'Edge DC' },
    { value: 'ai_campus', label: 'AI Campus' },
  ];

  const REGIONS = [
    { value: '', label: 'Toutes régions' },
    { value: 'IDF', label: 'Île-de-France' },
    { value: 'PACA', label: 'PACA' },
    { value: 'AuRA', label: 'Auvergne-Rhône-Alpes' },
    { value: 'HdF', label: 'Hauts-de-France' },
    { value: 'Occitanie', label: 'Occitanie' },
  ];

  // Filter electrical assets by type
  const postes = electricalAssets.filter(a => a.type === 'poste_htb');
  const lignes400 = electricalAssets.filter(a => a.type === 'ligne_400kv');
  const lignes225 = electricalAssets.filter(a => a.type === 'ligne_225kv');

  return (
    <div className="h-screen flex flex-col" style={{ background: '#0a0a0f' }}>
      {/* Desktop warning for mobile */}
      <div 
        className="desktop-warning hidden fixed inset-0 z-50 items-center justify-center p-8"
        style={{ background: '#0a0a0f' }}
      >
        <div className="text-center">
          <Server size={48} className="mx-auto mb-4" style={{ color: '#00d4aa' }} />
          <h2 className="text-xl font-bold mb-2" style={{ color: '#e8e8ed' }}>
            Application Desktop
          </h2>
          <p className="text-sm" style={{ color: '#8f8f9d' }}>
            Cockpit Immo est optimisé pour les écrans de 1280px minimum.
            Veuillez utiliser un ordinateur pour accéder à cette application.
          </p>
        </div>
      </div>

      {/* Main content */}
      <div className="main-content flex flex-col h-full">
        {/* Top bar */}
        <header 
          className="h-12 flex items-center justify-between px-4"
          style={{ background: '#12121a', borderBottom: '1px solid #1f1f2e' }}
        >
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Server size={20} style={{ color: '#00d4aa' }} />
              <span className="font-bold" style={{ color: '#e8e8ed' }}>COCKPIT IMMO</span>
            </div>
            
            {/* Navigation */}
            <nav className="flex items-center gap-1 ml-8">
              <button
                onClick={() => setActiveView('map')}
                className={`h-8 px-3 flex items-center gap-2 text-xs font-mono uppercase transition-colors ${
                  activeView === 'map' ? 'text-[#00d4aa] border-b-2 border-[#00d4aa]' : 'text-[#8f8f9d] hover:text-[#e8e8ed]'
                }`}
                data-testid="nav-map"
              >
                <MapIcon size={14} />
                Carte
              </button>
              <button
                onClick={() => setActiveView('table')}
                className={`h-8 px-3 flex items-center gap-2 text-xs font-mono uppercase transition-colors ${
                  activeView === 'table' ? 'text-[#00d4aa] border-b-2 border-[#00d4aa]' : 'text-[#8f8f9d] hover:text-[#e8e8ed]'
                }`}
                data-testid="nav-table"
              >
                <Table size={14} />
                Tableau
              </button>
              <button
                onClick={() => setActiveView('crm')}
                className={`h-8 px-3 flex items-center gap-2 text-xs font-mono uppercase transition-colors ${
                  activeView === 'crm' ? 'text-[#00d4aa] border-b-2 border-[#00d4aa]' : 'text-[#8f8f9d] hover:text-[#e8e8ed]'
                }`}
                data-testid="nav-crm"
              >
                <Briefcase size={14} />
                CRM
              </button>
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <button className="h-8 w-8 flex items-center justify-center text-[#8f8f9d] hover:text-[#e8e8ed]">
              <Bell size={16} />
            </button>
            <div className="flex items-center gap-2">
              {user?.picture && (
                <img src={user.picture} alt="" className="w-6 h-6 rounded-full" />
              )}
              <span className="text-xs" style={{ color: '#8f8f9d' }}>{user?.name}</span>
            </div>
            <button 
              onClick={logout}
              className="h-8 w-8 flex items-center justify-center text-[#8f8f9d] hover:text-[#ff4757]"
              data-testid="logout-btn"
            >
              <LogOut size={16} />
            </button>
          </div>
        </header>

        {/* Filters bar */}
        <div 
          className="h-12 flex items-center gap-4 px-4"
          style={{ background: '#0a0a0f', borderBottom: '1px solid #1f1f2e' }}
        >
          <div className="flex items-center gap-2">
            <label className="text-xs font-mono uppercase" style={{ color: '#8f8f9d' }}>Type projet:</label>
            <select
              value={projectType}
              onChange={(e) => setProjectType(e.target.value)}
              className="h-7 px-2 text-xs"
              style={{ minWidth: 140 }}
              data-testid="project-type-select"
            >
              {PROJECT_TYPES.map(pt => (
                <option key={pt.value} value={pt.value}>{pt.label}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-xs font-mono uppercase" style={{ color: '#8f8f9d' }}>Région:</label>
            <select
              value={regionFilter}
              onChange={(e) => setRegionFilter(e.target.value)}
              className="h-7 px-2 text-xs"
              style={{ minWidth: 140 }}
              data-testid="region-select"
            >
              {REGIONS.map(r => (
                <option key={r.value} value={r.value}>{r.label}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-xs font-mono uppercase" style={{ color: '#8f8f9d' }}>Score min:</label>
            <input
              type="range"
              min="0"
              max="90"
              step="10"
              value={scoreMin}
              onChange={(e) => setScoreMin(parseInt(e.target.value))}
              className="w-24"
            />
            <span className="text-xs font-mono" style={{ color: '#00d4aa' }}>{scoreMin}</span>
          </div>

          <button
            onClick={fetchParcels}
            className="btn-primary flex items-center gap-1"
            data-testid="refresh-btn"
          >
            <RefreshCw size={12} />
            Actualiser
          </button>

          <div className="ml-auto flex items-center gap-4">
            <span className="text-xs font-mono" style={{ color: '#8f8f9d' }}>
              {parcels.length} sites · {postes.length} postes · {landingPoints.length} landing pts
            </span>
          </div>
        </div>

        {/* Main content area */}
        <div className="flex-1 flex overflow-hidden">
          {activeView === 'map' && (
            <>
              {/* Map */}
              <div className="flex-1 relative">
                {loading ? (
                  <div className="absolute inset-0 flex items-center justify-center" style={{ background: '#0a0a0f' }}>
                    <div className="loader"></div>
                  </div>
                ) : (
                  <MapContainer
                    center={[46.5, 2.5]}
                    zoom={6}
                    style={{ height: '100%', width: '100%' }}
                  >
                    <TileLayer
                      url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    />
                    <MapBounds parcels={parcels} />
                    
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
                        icon={posteIcon(poste.tension_kv)}
                      >
                        <Popup>
                          <div className="p-2">
                            <p className="font-bold">{poste.nom}</p>
                            <p className="text-xs text-gray-400">
                              {poste.tension_kv} kV · {poste.puissance_mva} MVA
                            </p>
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
                    
                    {/* Parcels */}
                    {layers.parcels && parcels.map(parcel => {
                      const score = parcel.score?.score_net || 0;
                      const mw = parcel.score?.power_mw_p50 || 10;
                      
                      return (
                        <CircleMarker
                          key={parcel.parcel_id}
                          center={[parcel.latitude, parcel.longitude]}
                          radius={Math.max(6, Math.min(20, mw / 2))}
                          fillColor={getScoreColor(score)}
                          fillOpacity={0.8}
                          color={getScoreColor(score)}
                          weight={1}
                          eventHandlers={{
                            click: () => handleParcelClick(parcel)
                          }}
                        >
                          <Popup>
                            <div className="p-2" style={{ minWidth: 200 }}>
                              <p className="font-bold text-sm">{parcel.commune}</p>
                              <p className="text-xs text-gray-400">{parcel.region} · {parcel.surface_ha?.toFixed(1)} ha</p>
                              <div className="mt-2 flex items-center gap-2">
                                <span className="font-mono text-lg" style={{ color: getScoreColor(score) }}>
                                  {score.toFixed(0)}/100
                                </span>
                                <VerdictBadge verdict={parcel.score?.verdict} />
                              </div>
                            </div>
                          </Popup>
                        </CircleMarker>
                      );
                    })}
                  </MapContainer>
                )}
                
                {/* Layer control */}
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
                    </div>
                  )}
                </div>
              </div>

              {/* Side panel */}
              <div 
                className="w-96 flex flex-col"
                style={{ background: '#12121a', borderLeft: '1px solid #1f1f2e' }}
              >
                {selectedParcel ? (
                  <ParcelDetail parcel={selectedParcel} projectType={projectType} onClose={() => setSelectedParcel(null)} />
                ) : (
                  <div className="p-4">
                    <h3 className="text-sm font-mono uppercase mb-4" style={{ color: '#8f8f9d' }}>
                      Sélectionnez une parcelle
                    </h3>
                    <p className="text-xs" style={{ color: '#8f8f9d' }}>
                      Cliquez sur un cercle sur la carte pour voir les détails de la parcelle.
                    </p>
                    
                    {/* Legend */}
                    <div className="mt-6 space-y-2">
                      <p className="text-xs font-mono uppercase" style={{ color: '#8f8f9d' }}>Légende</p>
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 text-xs">
                          <span style={{ width: 12, height: 12, background: '#ff4757', transform: 'rotate(45deg)' }}></span>
                          <span style={{ color: '#e8e8ed' }}>Poste 400kV</span>
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                          <span style={{ width: 12, height: 12, background: '#ffa502', transform: 'rotate(45deg)' }}></span>
                          <span style={{ color: '#e8e8ed' }}>Poste 225kV</span>
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                          <span style={{ width: 12, height: 12, background: '#3b82f6', transform: 'rotate(45deg)' }}></span>
                          <span style={{ color: '#e8e8ed' }}>Poste 63kV</span>
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                          <span style={{ color: '#00d4aa', fontSize: 14 }}>⚓</span>
                          <span style={{ color: '#e8e8ed' }}>Landing point</span>
                        </div>
                        <div className="flex items-center gap-2 text-xs">
                          <span style={{ width: 12, height: 12, background: '#8b5cf6', borderRadius: 2 }}></span>
                          <span style={{ color: '#e8e8ed' }}>DC existant</span>
                        </div>
                      </div>
                    </div>
                    
                    {/* Quick stats */}
                    <div className="mt-6 space-y-3">
                      <p className="text-xs font-mono uppercase" style={{ color: '#8f8f9d' }}>Statistiques</p>
                      <div className="flex items-center justify-between">
                        <span className="text-xs" style={{ color: '#8f8f9d' }}>Sites GO</span>
                        <span className="font-mono text-sm" style={{ color: '#00d4aa' }}>
                          {parcels.filter(p => p.score?.verdict === 'GO').length}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-xs" style={{ color: '#8f8f9d' }}>Sites CONDITIONNEL</span>
                        <span className="font-mono text-sm" style={{ color: '#ffa502' }}>
                          {parcels.filter(p => p.score?.verdict === 'CONDITIONNEL').length}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-xs" style={{ color: '#8f8f9d' }}>Sites NO-GO</span>
                        <span className="font-mono text-sm" style={{ color: '#ff4757' }}>
                          {parcels.filter(p => p.score?.verdict === 'NO_GO').length}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}

          {activeView === 'table' && (
            <div className="flex-1 overflow-auto p-4">
              <ParcelsTable parcels={parcels} projectType={projectType} onSelect={handleParcelClick} />
            </div>
          )}

          {activeView === 'crm' && (
            <div className="flex-1 p-4">
              <CRMView />
            </div>
          )}
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
function ParcelDetail({ parcel, projectType, onClose }) {
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
        {/* Verdict */}
        <div className="flex items-center gap-3">
          <VerdictBadge verdict={score.verdict} />
          <span className="text-2xl font-mono font-bold" style={{ color: getScoreColor(score.score_net || 0) }}>
            {(score.score_net || 0).toFixed(0)}/100
          </span>
        </div>

        {/* Key metrics */}
        <div className="grid grid-cols-2 gap-3">
          <div className="panel p-3">
            <p className="text-xs font-mono uppercase" style={{ color: '#8f8f9d' }}>Surface</p>
            <p className="text-lg font-mono font-bold" style={{ color: '#e8e8ed' }}>
              {parcel.surface_ha?.toFixed(1)} ha
            </p>
          </div>
          <div className="panel p-3">
            <p className="text-xs font-mono uppercase" style={{ color: '#8f8f9d' }}>MW P50</p>
            <p className="text-lg font-mono font-bold" style={{ color: '#00d4aa' }}>
              {score.power_mw_p50?.toFixed(1) || '-'} MW
            </p>
          </div>
          <div className="panel p-3">
            <p className="text-xs font-mono uppercase" style={{ color: '#8f8f9d' }}>TTM</p>
            <p className="text-lg font-mono font-bold" style={{ color: '#3b82f6' }}>
              {score.ttm_min_months || '-'}-{score.ttm_max_months || '-'} mois
            </p>
          </div>
          <div className="panel p-3">
            <p className="text-xs font-mono uppercase" style={{ color: '#8f8f9d' }}>IRR Levered</p>
            <p className="text-lg font-mono font-bold" style={{ color: '#00d4aa' }}>
              {score.irr_levered_pct?.toFixed(1) || '-'}%
            </p>
          </div>
        </div>

        {/* Propriétaire & Foncier */}
        <div className="panel p-3">
          <p className="text-xs font-mono uppercase mb-2" style={{ color: '#8f8f9d' }}>Propriétaire & Foncier</p>
          <div className="space-y-2">
            <div>
              <p className="text-sm font-bold" style={{ color: '#e8e8ed' }}>
                {parcel.proprietaire_nom || 'Propriétaire inconnu'}
              </p>
              <p className="text-xs" style={{ color: '#8f8f9d' }}>
                {parcel.proprietaire_type === 'sci' ? 'SCI / Société civile' : 
                 parcel.proprietaire_type === 'fonciere' ? 'Foncière / Investisseur' :
                 parcel.proprietaire_type === 'prive' ? 'Propriétaire privé' : 
                 'Type inconnu'}
              </p>
            </div>
            <div className="flex justify-between text-xs pt-2" style={{ borderTop: '1px solid #1f1f2e' }}>
              <span style={{ color: '#8f8f9d' }}>Réf. cadastrale</span>
              <span className="font-mono" style={{ color: '#e8e8ed' }}>
                {parcel.ref_cadastrale || '-'}
              </span>
            </div>
            <div className="flex justify-between text-xs">
              <span style={{ color: '#8f8f9d' }}>Prix DVF (€/m²)</span>
              <span className="font-mono" style={{ color: '#ffa502' }}>
                {parcel.dvf_prix_m2_p50 ? `${parcel.dvf_prix_m2_p50.toFixed(0)} €` : '-'}
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

        {/* Urbanisme */}
        <div className="panel p-3">
          <p className="text-xs font-mono uppercase mb-2" style={{ color: '#8f8f9d' }}>Urbanisme</p>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-sm font-mono" style={{ color: '#e8e8ed' }}>
              Zone PLU: {parcel.plu_zone || 'N/A'}
            </span>
            <span className={`badge ${
              score.urba_compatibilite === 'compatible' ? 'badge-success' :
              score.urba_compatibilite === 'compatible_sous_conditions' ? 'badge-warning' : 'badge-danger'
            }`}>
              {score.urba_compatibilite?.replace(/_/g, ' ')}
            </span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span style={{ color: '#8f8f9d' }}>Deal Friction Index</span>
            <span className="font-mono" style={{ color: score.urba_deal_friction_index < 30 ? '#00d4aa' : '#ffa502' }}>
              {score.urba_deal_friction_index || 0}/100
            </span>
          </div>
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

        {/* Confidence */}
        <div className="flex items-center justify-between text-xs p-2" style={{ background: '#0a0a0f' }}>
          <span style={{ color: '#8f8f9d' }}>Confiance</span>
          <span className="font-mono" style={{ color: score.confidence_score > 70 ? '#00d4aa' : '#ffa502' }}>
            {score.confidence_score?.toFixed(0) || 0}/100
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

// Parcels Table
function ParcelsTable({ parcels, projectType, onSelect }) {
  const sortedParcels = [...parcels].sort((a, b) => 
    (b.score?.score_net || 0) - (a.score?.score_net || 0)
  );

  return (
    <div className="panel overflow-hidden">
      <div className="panel-header">
        <span className="text-xs font-mono uppercase" style={{ color: '#8f8f9d' }}>
          {parcels.length} sites · {projectType.replace('_', ' ')}
        </span>
      </div>
      <div className="overflow-auto" style={{ maxHeight: 'calc(100vh - 200px)' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Commune</th>
              <th>Région</th>
              <th>Verdict</th>
              <th>Score</th>
              <th>MW P50</th>
              <th>TTM</th>
              <th>DFI</th>
              <th>IRR Lev</th>
              <th>CAPEX</th>
            </tr>
          </thead>
          <tbody>
            {sortedParcels.map(parcel => {
              const score = parcel.score || {};
              return (
                <tr 
                  key={parcel.parcel_id}
                  onClick={() => onSelect(parcel)}
                  className="cursor-pointer"
                >
                  <td style={{ color: '#e8e8ed' }}>{parcel.commune}</td>
                  <td style={{ color: '#8f8f9d' }}>{parcel.region}</td>
                  <td><VerdictBadge verdict={score.verdict} /></td>
                  <td style={{ color: getScoreColor(score.score_net || 0) }}>
                    {(score.score_net || 0).toFixed(0)}
                  </td>
                  <td style={{ color: '#00d4aa' }}>{score.power_mw_p50?.toFixed(1) || '-'}</td>
                  <td style={{ color: '#3b82f6' }}>
                    {score.ttm_min_months || '-'}-{score.ttm_max_months || '-'}
                  </td>
                  <td style={{ color: (score.urba_deal_friction_index || 0) < 30 ? '#00d4aa' : '#ffa502' }}>
                    {score.urba_deal_friction_index || 0}
                  </td>
                  <td style={{ color: '#00d4aa' }}>{score.irr_levered_pct?.toFixed(1) || '-'}%</td>
                  <td style={{ color: '#e8e8ed' }}>
                    {score.capex_p50 ? `${(score.capex_p50 / 1e6).toFixed(0)}M` : '-'}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// CRM View
function CRMView() {
  const [shortlists, setShortlists] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchShortlists();
  }, []);

  const fetchShortlists = async () => {
    try {
      const response = await axios.get(`${API}/shortlists`, { withCredentials: true });
      setShortlists(response.data.shortlists || []);
    } catch (error) {
      console.error('Error fetching shortlists:', error);
    } finally {
      setLoading(false);
    }
  };

  const createShortlist = async () => {
    const name = prompt('Nom de la shortlist:');
    if (!name) return;
    
    try {
      await axios.post(`${API}/shortlists`, { nom: name }, { withCredentials: true });
      fetchShortlists();
    } catch (error) {
      console.error('Error creating shortlist:', error);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold" style={{ color: '#e8e8ed' }}>Pipeline CRM</h2>
        <button onClick={createShortlist} className="btn-primary flex items-center gap-1">
          <Plus size={14} />
          Nouvelle shortlist
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8">
          <div className="loader"></div>
        </div>
      ) : shortlists.length === 0 ? (
        <div className="panel p-8 text-center">
          <Briefcase size={48} className="mx-auto mb-4" style={{ color: '#8f8f9d' }} />
          <p style={{ color: '#8f8f9d' }}>Aucune shortlist. Créez-en une pour commencer.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {shortlists.map(sl => (
            <div key={sl.shortlist_id} className="panel p-4">
              <h3 className="font-bold mb-2" style={{ color: '#e8e8ed' }}>{sl.nom}</h3>
              <p className="text-xs mb-3" style={{ color: '#8f8f9d' }}>
                {sl.item_count || 0} sites · {sl.project_type || 'Tous types'}
              </p>
              <button className="btn-secondary w-full text-xs">
                Voir les sites
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
