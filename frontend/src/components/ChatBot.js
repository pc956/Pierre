import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Loader, MapPin, Zap, ChevronUp } from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

export default function ChatBot({ onFlyTo, onHighlightSites, onSelectParcelFromChat }) {
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
                Recherche autour de : {msg.sites_searched.map(s => `${s.name} (${s.grid.mw_dispo}MW)`).join(', ')}
              </div>
            )}
            {msg.parcels.slice(0, 10).map((p, i) => {
              const scoreVal = p.score?.score_net || 0;
              const scoreColor = scoreVal >= 70 ? '#2ed573' : scoreVal >= 40 ? '#ffa502' : '#ff4757';
              return (
                <div
                  key={p.parcel_id}
                  className="p-2 rounded cursor-pointer hover:opacity-80 transition-all"
                  style={{ background: '#12121a', border: '1px solid #1f1f2e' }}
                  onClick={() => onParcelClick && onParcelClick(p)}
                  data-testid={`chat-parcel-${i}`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-bold text-[11px]" style={{ color: '#e8e8ed' }}>
                      {p.ref_cadastrale || p.parcel_id}
                    </span>
                    <span className="font-mono text-[10px] px-1.5 rounded" style={{
                      background: scoreColor + '22',
                      color: scoreColor,
                    }}>
                      {scoreVal.toFixed(0)}/100
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 mt-1 text-[10px] flex-wrap" style={{ color: '#8f8f9d' }}>
                    <span><MapPin size={9} className="inline" /> {p.commune || p.region}</span>
                    <span className="font-bold" style={{ color: '#00d4aa' }}>{p.surface_ha?.toFixed(2)} ha</span>
                    <span>HTB: {(p.dist_poste_htb_m / 1000).toFixed(1)}km</span>
                    {p.plu_zone && p.plu_zone !== 'inconnu' && (
                      <span className="px-1 rounded" style={{ background: '#3b82f622', color: '#3b82f6' }}>
                        PLU {p.plu_zone}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1.5 mt-0.5 text-[10px]" style={{ color: '#8f8f9d' }}>
                    <span>{p.tension_htb_kv}kV</span>
                    {p.dvf_prix_median_m2 > 0 && <span>{p.dvf_prix_median_m2}€/m²</span>}
                    <span>LP: {p.dist_landing_point_km}km</span>
                    {p.future_400kv_buffer && (
                      <span className="px-1 rounded" style={{ background: '#ff004022', color: '#ff4757' }}>
                        400kV {p.future_400kv_buffer}
                      </span>
                    )}
                  </div>
                  <div className="mt-1 text-[9px]" style={{ color: '#00d4aa88' }}>
                    {p.score?.verdict} · {p.site_origin}
                  </div>
                </div>
              );
            })}
            {msg.total_found > msg.returned && (
              <p className="text-[10px] text-center" style={{ color: '#8f8f9d' }}>
                +{msg.total_found - msg.returned} parcelles non affichées
              </p>
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
