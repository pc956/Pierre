import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Loader, MapPin, Zap, ChevronUp } from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

export default function ChatBot({ onFlyTo, onHighlightSites, onSelectParcelFromChat, externalMessage, onExternalMessageHandled }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'assistant', type: 'text', content: 'Bonjour ! Je suis votre assistant Cockpit Immo. Posez-moi une question sur les terrains pour data centers.\n\nExemples :\n• "Trouve 5 sites pour un DC de 50MW en PACA"\n• "Quels sont les postes non saturés dans le Nord ?"\n• "Résumé des capacités S3REnR"' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => `chat_${Date.now()}`);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  useEffect(() => {
    if (open && inputRef.current) {
      inputRef.current.focus();
    }
  }, [open]);

  useEffect(() => {
    if (externalMessage) {
      setInput(externalMessage);
      if (!open) setOpen(true);
      onExternalMessageHandled && onExternalMessageHandled();
    }
  }, [externalMessage]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg = { role: 'user', type: 'text', content: text };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const history = messages.filter(m => m.role === 'user' || m.role === 'assistant').slice(-8).map(m => ({
        role: m.role,
        content: m.content || '',
      }));

      const res = await axios.post(`${API}/api/chat`, {
        message: text,
        session_id: sessionId,
        history,
      });

      const data = res.data;
      handleResponse(data);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant', type: 'text',
        content: 'Désolé, une erreur est survenue. Réessayez.',
      }]);
    }
    setLoading(false);
  };

  const handleResponse = (data) => {
    if (data.type === 'parcel_results') {
      setMessages(prev => [...prev, {
        role: 'assistant',
        type: 'parcel_results',
        content: data.intro || 'Voici les parcelles trouvées :',
        parcels: data.parcels,
        composite_sites: data.composite_sites || [],
        sites_searched: data.sites_searched,
        total_found: data.total_found,
        returned: data.returned,
        params: data.params,
        filters_applied: data.filters_applied,
      }]);
      if (data.fly_to && onFlyTo) {
        onFlyTo(data.fly_to.lat, data.fly_to.lng, data.fly_to.zoom);
      }
    } else if (data.type === 'search_results') {
      setMessages(prev => [...prev, {
        role: 'assistant',
        type: 'search_results',
        content: data.intro || 'Voici les résultats :',
        results: data.results,
        meta: data.meta,
        params: data.params,
      }]);
      if (data.fly_to && onFlyTo) {
        onFlyTo(data.fly_to.lat, data.fly_to.lng, data.fly_to.zoom);
      }
      if (data.results && onHighlightSites) {
        onHighlightSites(data.results.map(r => r.site_id));
      }
    } else if (data.type === 'site_detail') {
      setMessages(prev => [...prev, {
        role: 'assistant',
        type: 'site_detail',
        content: data.intro || 'Voici les détails :',
        site: data.site,
      }]);
      if (data.fly_to && onFlyTo) {
        onFlyTo(data.fly_to.lat, data.fly_to.lng, data.fly_to.zoom);
      }
    } else if (data.type === 'summary') {
      setMessages(prev => [...prev, {
        role: 'assistant',
        type: 'summary',
        content: data.intro || 'Résumé S3REnR :',
        summary: data.summary,
      }]);
    } else {
      setMessages(prev => [...prev, {
        role: 'assistant',
        type: 'text',
        content: data.text || data.response || 'Pas de réponse.',
      }]);
    }
  };

  const quickAction = (text) => {
    setInput(text);
    setTimeout(() => {
      const fakeEvent = { key: 'Enter' };
      setInput(text);
      // Trigger send
      sendMessageDirect(text);
    }, 100);
  };

  const sendMessageDirect = async (text) => {
    if (!text || loading) return;
    const userMsg = { role: 'user', type: 'text', content: text };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/chat`, {
        message: text,
        session_id: sessionId,
        history: [],
      });
      handleResponse(res.data);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant', type: 'text',
        content: 'Erreur. Réessayez.',
      }]);
    }
    setLoading(false);
  };

  // Floating button when closed
  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed z-[1100] flex items-center gap-2 px-4 py-3 rounded-full shadow-lg transition-transform hover:scale-105"
        style={{ background: '#00d4aa', color: '#0a0a0f', bottom: 80, right: 420 }}
        data-testid="chatbot-open-btn"
      >
        <MessageCircle size={20} />
        <span className="text-sm font-bold hidden sm:inline">Assistant IA</span>
      </button>
    );
  }

  return (
    <div
      className="fixed z-[1100] flex flex-col shadow-2xl"
      style={{
        bottom: 20, right: 420,
        width: 'min(380px, calc(100vw - 40px))',
        height: 'min(540px, calc(100vh - 100px))',
        background: '#12121a',
        border: '1px solid #1f1f2e',
        borderRadius: 12,
      }}
      data-testid="chatbot-panel"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 shrink-0" style={{ borderBottom: '1px solid #1f1f2e' }}>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full flex items-center justify-center" style={{ background: '#00d4aa22' }}>
            <Zap size={14} style={{ color: '#00d4aa' }} />
          </div>
          <div>
            <p className="text-xs font-bold" style={{ color: '#e8e8ed' }}>Assistant Cockpit Immo</p>
            <p className="text-[10px]" style={{ color: '#00d4aa' }}>En ligne</p>
          </div>
        </div>
        <button onClick={() => setOpen(false)} className="text-[#8f8f9d] hover:text-[#e8e8ed]" data-testid="chatbot-close-btn">
          <X size={18} />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3" style={{ scrollBehavior: 'smooth' }}>
        {messages.map((msg, i) => (
          <ChatMessage 
            key={i} 
            msg={msg} 
            onSiteClick={(id) => quickAction(`détails du site ${id}`)} 
            onParcelClick={(parcel) => {
              if (onFlyTo) onFlyTo(parcel.latitude, parcel.longitude, 17);
              if (onSelectParcelFromChat) onSelectParcelFromChat(parcel);
            }}
          />
        ))}
        {loading && (
          <div className="flex items-center gap-2 px-3 py-2">
            <Loader size={14} className="animate-spin" style={{ color: '#00d4aa' }} />
            <span className="text-xs" style={{ color: '#8f8f9d' }}>Analyse en cours...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick actions */}
      {messages.length <= 2 && (
        <div className="px-3 py-2 flex flex-wrap gap-1.5 shrink-0" style={{ borderTop: '1px solid #1f1f2e' }}>
          {[
            'Trouve des parcelles 30MW PACA',
            'Terrains 2ha+ près de Fos',
            'Parcelles zone industrielle HdF',
            'Résumé S3REnR',
          ].map(q => (
            <button
              key={q}
              onClick={() => quickAction(q)}
              className="text-[10px] px-2 py-1 rounded-full"
              style={{ background: '#1f1f2e', color: '#8f8f9d' }}
              data-testid={`quick-action-${q.replace(/\s+/g, '-')}`}
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Suggestions rapides */}
      {messages.length <= 1 && (
        <div className="flex flex-wrap gap-2 px-4 pb-3" data-testid="suggestion-pills">
          {[
            { label: "PACA 2ha+", query: "Parcelles en PACA de 2 hectares minimum" },
            { label: "Fos-sur-Mer", query: "Parcelles à Fos-sur-Mer pour data center" },
            { label: "Hauts-de-France", query: "Parcelles en Hauts-de-France de 2 hectares minimum" },
            { label: "Score > 70", query: "Parcelles avec un score supérieur à 70 en PACA" },
            { label: "Grands terrains", query: "Parcelles de 5 hectares minimum en France" },
          ].map((s, i) => (
            <button key={i} onClick={() => { setInput(s.query); }}
              className="px-3 py-1 text-[10px] font-mono rounded-full hover:opacity-80 transition-opacity"
              style={{ background: '#1f1f2e', border: '1px solid #2a2a3e', color: '#8f8f9d' }}
              data-testid={`suggestion-pill-${i}`}>
              {s.label}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <div className="px-3 py-3 shrink-0" style={{ borderTop: '1px solid #1f1f2e' }}>
        <div className="flex items-center gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ex: 30MW PACA en 12 mois..."
            className="flex-1 h-9 px-3 text-sm rounded-lg"
            style={{ background: '#0a0a0f', border: '1px solid #1f1f2e', color: '#e8e8ed' }}
            data-testid="chatbot-input"
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="h-9 w-9 flex items-center justify-center rounded-lg transition-colors"
            style={{
              background: input.trim() ? '#00d4aa' : '#1f1f2e',
              color: input.trim() ? '#0a0a0f' : '#8f8f9d',
            }}
            data-testid="chatbot-send-btn"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}


function ChatMessage({ msg, onSiteClick, onParcelClick }) {
  const isUser = msg.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className="max-w-[85%] px-3 py-2 rounded-lg text-xs"
        style={{
          background: isUser ? '#00d4aa22' : '#0a0a0f',
          border: isUser ? '1px solid #00d4aa33' : '1px solid #1f1f2e',
          color: '#e8e8ed',
        }}
      >
        {/* Text content */}
        {msg.content && (
          <p className="whitespace-pre-wrap" style={{ color: isUser ? '#e8e8ed' : '#c8c8d5' }}>
            {msg.content}
          </p>
        )}

        {/* Search results */}
        {msg.type === 'search_results' && msg.results && (
          <div className="mt-2 space-y-1.5">
            <div className="text-[10px] flex justify-between" style={{ color: '#8f8f9d' }}>
              <span>{msg.meta?.total_results} sites · {msg.meta?.strategy}</span>
              <span>{msg.meta?.search_time_ms}ms</span>
            </div>
            {msg.results.slice(0, 5).map((r, i) => (
              <div
                key={r.site_id}
                className="p-2 rounded cursor-pointer hover:opacity-80 transition-opacity"
                style={{ background: '#12121a', border: '1px solid #1f1f2e' }}
                onClick={() => onSiteClick && onSiteClick(r.site_id)}
                data-testid={`chat-result-${i}`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-[11px]" style={{ color: '#e8e8ed' }}>{r.name}</span>
                  <span className="font-mono text-[10px] px-1.5 rounded" style={{
                    background: r.score.global >= 80 ? '#2ed57322' : r.score.global >= 50 ? '#ffa50222' : '#ff475722',
                    color: r.score.global >= 80 ? '#2ed573' : r.score.global >= 50 ? '#ffa502' : '#ff4757',
                  }}>
                    {r.score.global.toFixed(0)}
                  </span>
                </div>
                <div className="flex items-center gap-2 mt-0.5 text-[10px]" style={{ color: '#8f8f9d' }}>
                  <span><MapPin size={9} className="inline" /> {r.location.region}</span>
                  <span style={{ color: '#00d4aa' }}>{r.grid.available_capacity_mw}MW</span>
                  <span>{r.grid.voltage_level}</span>
                  <span className="px-1 rounded" style={{
                    background: r.grid.saturation_level === 'low' ? '#2ed57322' : r.grid.saturation_level === 'medium' ? '#ffa50222' : '#ff475722',
                    color: r.grid.saturation_level === 'low' ? '#2ed573' : r.grid.saturation_level === 'medium' ? '#ffa502' : '#ff4757',
                  }}>
                    {r.grid.saturation_level}
                  </span>
                </div>
              </div>
            ))}
            {msg.results.length > 5 && (
              <p className="text-[10px] text-center" style={{ color: '#8f8f9d' }}>
                +{msg.results.length - 5} autres résultats
              </p>
            )}
          </div>
        )}

        {/* Parcel results (real cadastral parcels) */}
        {msg.type === 'parcel_results' && msg.parcels && (
          <div className="mt-2 space-y-1.5">
            <div className="text-[10px] flex justify-between" style={{ color: '#8f8f9d' }}>
              <span>{msg.total_found} parcelles trouvées</span>
              <span>{msg.returned} affichées</span>
            </div>
            {/* Active filters summary */}
            {msg.filters_applied && (
              <div className="flex flex-wrap gap-1 text-[9px]">
                {msg.filters_applied.min_surface_ha > 0 && (
                  <span className="px-1.5 py-0.5 rounded" style={{ background: '#00d4aa15', color: '#00d4aa', border: '1px solid #00d4aa33' }}>
                    ≥{msg.filters_applied.min_surface_ha}ha
                  </span>
                )}
                {msg.filters_applied.max_surface_ha && (
                  <span className="px-1.5 py-0.5 rounded" style={{ background: '#00d4aa15', color: '#00d4aa', border: '1px solid #00d4aa33' }}>
                    ≤{msg.filters_applied.max_surface_ha}ha
                  </span>
                )}
                {msg.filters_applied.max_dist_htb_km && (
                  <span className="px-1.5 py-0.5 rounded" style={{ background: '#ffa50215', color: '#ffa502', border: '1px solid #ffa50233' }}>
                    HTB≤{msg.filters_applied.max_dist_htb_km}km
                  </span>
                )}
                {msg.filters_applied.min_tension_kv && (
                  <span className="px-1.5 py-0.5 rounded" style={{ background: '#ff004015', color: '#ff4757', border: '1px solid #ff004033' }}>
                    ≥{msg.filters_applied.min_tension_kv}kV
                  </span>
                )}
                {msg.filters_applied.max_dist_future_line_km && (
                  <span className="px-1.5 py-0.5 rounded" style={{ background: '#ff004015', color: '#ff4757', border: '1px solid #ff004033' }}>
                    400kV≤{msg.filters_applied.max_dist_future_line_km}km
                  </span>
                )}
                {msg.filters_applied.plu_zones && (
                  <span className="px-1.5 py-0.5 rounded" style={{ background: '#3b82f615', color: '#3b82f6', border: '1px solid #3b82f633' }}>
                    PLU: {msg.filters_applied.plu_zones.join(', ')}
                  </span>
                )}
              </div>
            )}
            {msg.sites_searched && msg.sites_searched.length > 0 && (
              <div className="text-[10px] px-2 py-1 rounded" style={{ background: '#0a0a0f', border: '1px solid #1f1f2e', color: '#8f8f9d' }}>
                Recherche autour de : {msg.sites_searched.map(s => s.name).join(', ')}
              </div>
            )}
            {msg.parcels.slice(0, 10).map((p, i) => {
              const scoreVal = p.score?.score || p.score?.score_net || 0;
              const verdict = p.score?.verdict || 'A_ETUDIER';
              const detail = p.score?.detail || {};
              const flags = p.score?.flags || [];
              const resume = p.score?.resume || '';
              const scoreColor = scoreVal >= 70 ? '#2ed573' : scoreVal >= 40 ? '#ffa502' : '#ff4757';
              const verdictLabel = verdict === 'GO' ? 'GO' : verdict === 'A_ETUDIER' ? 'À ÉTUDIER' : verdict === 'EXCLU' ? 'EXCLU' : 'DÉFAVORABLE';

              // Google Maps URL
              const gmapsUrl = `https://www.google.com/maps?q=${p.latitude},${p.longitude}&z=17`;

              return (
                <div
                  key={p.parcel_id}
                  className="p-2 rounded cursor-pointer hover:opacity-80 transition-all"
                  style={{ background: '#12121a', border: `1px solid ${scoreColor}33` }}
                  onClick={() => onParcelClick && onParcelClick(p)}
                  data-testid={`chat-parcel-${i}`}
                >
                  {/* Header: ref + score */}
                  <div className="flex items-center justify-between">
                    <a
                      href={gmapsUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="font-mono font-bold text-[11px] hover:underline"
                      style={{ color: '#e8e8ed' }}
                      data-testid={`parcel-ref-link-${i}`}
                    >
                      {p.ref_cadastrale || p.parcel_id}
                    </a>
                    <div className="flex items-center gap-1.5">
                      <span className="font-mono text-[10px] px-1.5 py-0.5 rounded font-bold" style={{
                        background: scoreColor + '22',
                        color: scoreColor,
                      }}>
                        {scoreVal}/100
                      </span>
                      <span className="text-[9px] px-1.5 py-0.5 rounded font-bold" style={{
                        background: scoreColor + '15',
                        color: scoreColor,
                        border: `1px solid ${scoreColor}33`,
                      }}>
                        {verdictLabel}
                      </span>
                    </div>
                  </div>

                  {/* Resume line */}
                  {resume && (
                    <p className="mt-1 text-[9px] leading-tight" style={{ color: '#aaa' }}>
                      {resume.length > 120 ? resume.substring(0, 120) + '...' : resume}
                    </p>
                  )}

                  {/* Key metrics */}
                  <div className="flex items-center gap-1.5 mt-1.5 text-[10px] flex-wrap" style={{ color: '#8f8f9d' }}>
                    <span><MapPin size={9} className="inline" /> {p.commune || p.region}</span>
                    <span className="font-bold" style={{ color: '#00d4aa' }}>{p.surface_ha?.toFixed(2)} ha</span>
                    <span>HTB: {(p.dist_poste_htb_m / 1000).toFixed(1)}km</span>
                    {p.mw_dispo > 0 && (
                      <span style={{ color: '#ffa502' }}>{p.mw_dispo}MW</span>
                    )}
                    {p.plu_zone && p.plu_zone !== 'inconnu' && (
                      <span className="px-1 rounded" style={{ background: '#3b82f622', color: '#3b82f6' }}>
                        PLU {p.plu_zone}
                      </span>
                    )}
                  </div>

                  {/* Score breakdown bars (Étape 8) */}
                  {detail && Object.keys(detail).length > 0 && (
                    <div className="mt-1.5 space-y-0.5">
                      <ScoreBar label="RTE" value={detail.distance_rte || 0} max={40} />
                      <ScoreBar label="MW" value={detail.mw_disponibles || 0} max={30} />
                      <ScoreBar label="PLU" value={detail.plu || 0} max={20} />
                      <ScoreBar label="Surface" value={detail.surface || 0} max={10} />
                      {detail.malus < 0 && (
                        <div className="flex items-center gap-1 text-[9px]">
                          <span style={{ color: '#ff4757' }}>Malus: {detail.malus}</span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Flags */}
                  {flags.length > 0 && (
                    <div className="mt-1 flex flex-wrap gap-1">
                      {flags.map((f, fi) => (
                        <span key={fi} className="text-[8px] px-1 py-0.5 rounded" style={{ background: '#ff475722', color: '#ff4757' }}>
                          {f}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Extra info */}
                  <div className="flex items-center gap-1.5 mt-0.5 text-[10px] flex-wrap" style={{ color: '#8f8f9d' }}>
                    <span>{p.tension_htb_kv}kV</span>
                    {p.dvf_prix_median_m2 > 0 && <span>{p.dvf_prix_median_m2}€/m²</span>}
                    {p.dist_backbone_fibre_m > 0 && <span>Fibre: {(p.dist_backbone_fibre_m / 1000).toFixed(1)}km</span>}
                    {p.dist_cours_eau_m && (
                      <span style={{ color: '#0ea5e9' }}>{p.nom_cours_eau}: {(p.dist_cours_eau_m / 1000).toFixed(1)}km</span>
                    )}
                    {p.dist_route_m && (
                      <span style={{ color: '#a78bfa' }}>{p.type_route}: {(p.dist_route_m / 1000).toFixed(1)}km</span>
                    )}
                    {p.future_400kv_buffer && (
                      <span className="px-1 rounded" style={{ background: '#ff004022', color: '#ff4757' }}>
                        400kV {p.future_400kv_buffer}
                      </span>
                    )}
                    {p.zone_saturation && p.zone_saturation !== 'inconnu' && (
                      <span className="px-1 rounded" style={{ 
                        background: p.zone_saturation === 'disponible' ? '#2ed57322' : p.zone_saturation === 'sature' ? '#ff475722' : '#ffa50222',
                        color: p.zone_saturation === 'disponible' ? '#2ed573' : p.zone_saturation === 'sature' ? '#ff4757' : '#ffa502',
                      }}>
                        {p.zone_saturation}
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
            {msg.total_found > msg.returned && (
              <p className="text-[10px] text-center" style={{ color: '#8f8f9d' }}>
                +{msg.total_found - msg.returned} parcelles non affichées
              </p>
            )}
            {/* Composite sites (Étape 9) */}
            {msg.composite_sites && msg.composite_sites.length > 0 && (
              <div className="mt-2 pt-2" style={{ borderTop: '1px solid #1f1f2e' }}>
                <p className="text-[10px] font-bold mb-1" style={{ color: '#ffa502' }}>
                  Sites composites détectés ({msg.composite_sites.length})
                </p>
                {msg.composite_sites.map((cs, ci) => {
                  const csScore = cs.score?.score || 0;
                  const csColor = csScore >= 70 ? '#2ed573' : csScore >= 40 ? '#ffa502' : '#ff4757';
                  return (
                    <div
                      key={ci}
                      className="p-2 rounded mt-1 cursor-pointer hover:opacity-80"
                      style={{ background: '#0a0a0f', border: `1px solid ${csColor}33` }}
                      onClick={() => onParcelClick && onParcelClick({ latitude: cs.latitude, longitude: cs.longitude, parcel_id: cs.parcel_ids[0], ref_cadastrale: cs.refs[0], commune: cs.commune, score: cs.score })}
                      data-testid={`composite-site-${ci}`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold" style={{ color: '#ffa502' }}>
                          {cs.nb_parcels} parcelles · {cs.surface_totale_ha} ha
                        </span>
                        <span className="font-mono text-[10px] px-1.5 py-0.5 rounded font-bold" style={{ background: csColor + '22', color: csColor }}>
                          {csScore}/100
                        </span>
                      </div>
                      <p className="text-[9px] mt-0.5" style={{ color: '#8f8f9d' }}>
                        {cs.commune} · Refs: {cs.refs.slice(0, 3).join(', ')}{cs.refs.length > 3 ? '...' : ''}
                      </p>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Site detail */}
        {msg.type === 'site_detail' && msg.site && (
          <div className="mt-2 p-2 rounded" style={{ background: '#12121a', border: '1px solid #1f1f2e' }}>
            <p className="font-bold text-[11px]" style={{ color: '#e8e8ed' }}>{msg.site.name}</p>
            <div className="mt-1 space-y-0.5 text-[10px]" style={{ color: '#8f8f9d' }}>
              <p>Région: {msg.site.location.region} · {msg.site.grid.voltage_level}</p>
              <p style={{ color: '#00d4aa' }}>MW dispo: {msg.site.grid.available_capacity_mw} · Capacité: {msg.site.grid.estimated_capacity_mw}</p>
              <p>Saturation: <span style={{
                color: msg.site.grid.saturation_level === 'low' ? '#2ed573' : msg.site.grid.saturation_level === 'medium' ? '#ffa502' : '#ff4757'
              }}>{msg.site.grid.saturation_level}</span></p>
              <p>Délai: {msg.site.timeline.estimated_connection_delay_months} mois · Risque: {msg.site.timeline.permitting_risk}</p>
              <p>Foncier: {msg.site.land.surface_ha}ha · {msg.site.land.price_per_m2}€/m² · {msg.site.land.type}</p>
              {msg.site.grid.reinforcement_detail && (
                <p style={{ color: '#00d4aa' }}>Renforcement: {msg.site.grid.reinforcement_detail}</p>
              )}
            </div>
          </div>
        )}

        {/* S3REnR Summary */}
        {msg.type === 'summary' && msg.summary && (
          <div className="mt-2 space-y-1">
            {msg.summary.map(r => (
              <div key={r.region} className="flex items-center justify-between p-1.5 rounded" style={{ background: '#12121a' }}>
                <span className="font-bold text-[10px]" style={{ color: '#e8e8ed' }}>{r.region}</span>
                <div className="flex items-center gap-2 text-[10px]">
                  <span style={{ color: '#8f8f9d' }}>{r.nb_postes} postes</span>
                  <span style={{ color: '#00d4aa' }}>{r.mw_total} MW</span>
                  <span className="px-1.5 rounded" style={{
                    background: r.status === 'SATURE' ? '#ff475722' : '#2ed57322',
                    color: r.status === 'SATURE' ? '#ff4757' : '#2ed573',
                  }}>{r.status}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}


function ScoreBar({ label, value, max }) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  const color = pct >= 75 ? '#2ed573' : pct >= 50 ? '#ffa502' : pct >= 25 ? '#f0932b' : '#ff4757';
  return (
    <div className="flex items-center gap-1.5 text-[9px]">
      <span className="w-10 text-right" style={{ color: '#8f8f9d' }}>{label}</span>
      <div className="flex-1 h-1.5 rounded-full" style={{ background: '#1f1f2e' }}>
        <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="w-8 text-right" style={{ color }}>{value}/{max}</span>
    </div>
  );
}
