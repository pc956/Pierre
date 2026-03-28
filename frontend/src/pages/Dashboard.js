import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  Server, Map as MapIcon, Table, Briefcase, Bell, Settings, LogOut, 
  Search, Filter, ChevronDown, Plus, Zap, Wifi, Droplets, Square,
  TrendingUp, Clock, AlertTriangle, CheckCircle, XCircle, RefreshCw
} from 'lucide-react';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

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

  // Fetch parcels
  useEffect(() => {
    fetchParcels();
    fetchStats();
  }, [projectType, regionFilter, scoreMin]);

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

  const handleParcelClick = (parcel) => {
    setSelectedParcel(parcel);
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
              {parcels.length} sites · {stats?.regions?.IDF || 0} IDF
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
                    center={[48.8566, 2.3522]}
                    zoom={8}
                    style={{ height: '100%', width: '100%' }}
                  >
                    <TileLayer
                      url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    />
                    <MapBounds parcels={parcels} />
                    
                    {parcels.map(parcel => {
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
                    
                    {/* Quick stats */}
                    <div className="mt-6 space-y-3">
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
