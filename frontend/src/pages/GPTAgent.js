import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Server, Copy, Check, ExternalLink, ChevronDown, ChevronUp, ArrowLeft, Zap, Brain, Settings } from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

export default function GPTAgent() {
  const navigate = useNavigate();
  const [config, setConfig] = useState(null);
  const [schema, setSchema] = useState(null);
  const [copied, setCopied] = useState({});
  const [expandSchema, setExpandSchema] = useState(false);
  const [testQuery, setTestQuery] = useState('');
  const [testResult, setTestResult] = useState(null);
  const [testLoading, setTestLoading] = useState(false);

  useEffect(() => {
    Promise.all([
      axios.get(`${API}/api/gpt/config`),
      axios.get(`${API}/api/gpt/openapi-schema`),
    ]).then(([configRes, schemaRes]) => {
      setConfig(configRes.data);
      setSchema(schemaRes.data);
    });
  }, []);

  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopied({ ...copied, [key]: true });
    setTimeout(() => setCopied({ ...copied, [key]: false }), 2000);
  };

  const runTest = async () => {
    if (!testQuery.trim()) return;
    setTestLoading(true);
    setTestResult(null);
    try {
      const params = parseNaturalQuery(testQuery);
      const res = await axios.post(`${API}/api/dc/search`, params);
      setTestResult(res.data);
    } catch (err) {
      setTestResult({ error: err.message });
    }
    setTestLoading(false);
  };

  const parseNaturalQuery = (query) => {
    const q = query.toLowerCase();
    const params = { strategy: 'balanced', per_page: 5 };

    const mwMatch = q.match(/(\d+)\s*mw/);
    if (mwMatch) params.mw_target = parseInt(mwMatch[1]);

    const delayMatch = q.match(/(\d+)\s*mois/);
    if (delayMatch) params.max_delay_months = parseInt(delayMatch[1]);

    if (q.includes('idf') || q.includes('ile-de-france') || q.includes('paris')) params.region = 'IDF';
    else if (q.includes('paca') || q.includes('marseille') || q.includes('sud')) params.region = 'PACA';
    else if (q.includes('nord') || q.includes('hdf') || q.includes('lille') || q.includes('hauts')) params.region = 'HdF';

    if (q.includes('rapid') || q.includes('vite')) params.strategy = 'speed';
    else if (q.includes('cher') || q.includes('cost') || q.includes('prix')) params.strategy = 'cost';
    else if (q.includes('puissan') || q.includes('power') || q.includes('max mw')) params.strategy = 'power';

    if (q.includes('brownfield') || q.includes('industriel')) params.brownfield_only = true;

    return params;
  };

  if (!config) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#0a0a0f' }}>
        <div className="animate-pulse text-[#00d4aa]">Chargement...</div>
      </div>
    );
  }

  const schemaJson = JSON.stringify(schema, null, 2);
  const schemaUrl = `${API}/api/gpt/openapi-schema`;

  return (
    <div className="min-h-screen" style={{ background: '#0a0a0f', color: '#e8e8ed' }}>
      {/* Header */}
      <header className="h-14 flex items-center justify-between px-4 md:px-8" style={{ background: '#12121a', borderBottom: '1px solid #1f1f2e' }}>
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/dashboard')} className="text-[#8f8f9d] hover:text-[#e8e8ed]" data-testid="back-btn">
            <ArrowLeft size={18} />
          </button>
          <Server size={20} style={{ color: '#00d4aa' }} />
          <span className="font-bold text-sm md:text-base">COCKPIT IMMO</span>
          <span className="text-xs font-mono px-2 py-0.5 rounded" style={{ background: '#00d4aa22', color: '#00d4aa' }}>GPT AGENT</span>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-4 md:px-8 py-8 space-y-8">
        {/* Hero */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full" style={{ background: '#00d4aa15', border: '1px solid #00d4aa33' }}>
            <Brain size={18} style={{ color: '#00d4aa' }} />
            <span className="text-sm font-mono" style={{ color: '#00d4aa' }}>Agent IA Cockpit Immo</span>
          </div>
          <h1 className="text-2xl md:text-4xl font-bold" style={{ color: '#e8e8ed' }}>
            {config.name}
          </h1>
          <p className="text-sm md:text-base max-w-2xl mx-auto" style={{ color: '#8f8f9d' }}>
            {config.description}
          </p>
        </div>

        {/* Setup Steps */}
        <div className="p-5 rounded-lg" style={{ background: '#12121a', border: '1px solid #1f1f2e' }} data-testid="setup-steps">
          <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
            <Settings size={18} style={{ color: '#00d4aa' }} />
            Configuration en 3 minutes
          </h2>
          <div className="space-y-4">
            {Object.entries(config.setup_instructions).map(([key, value], i) => (
              <div key={key} className="flex gap-3 items-start">
                <div className="w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-xs font-bold" style={{ background: '#00d4aa22', color: '#00d4aa' }}>
                  {i + 1}
                </div>
                <div className="text-sm pt-1" style={{ color: '#e8e8ed' }}>
                  {value}
                  {i === 0 && (
                    <a href="https://chatgpt.com/gpts/editor" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 ml-2" style={{ color: '#00d4aa' }}>
                      Ouvrir <ExternalLink size={12} />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* System Prompt */}
        <div className="p-5 rounded-lg" style={{ background: '#12121a', border: '1px solid #1f1f2e' }}>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-bold flex items-center gap-2">
              <Brain size={18} style={{ color: '#ffa502' }} />
              System Prompt (Instructions)
            </h2>
            <button
              onClick={() => copyToClipboard(config.system_prompt, 'prompt')}
              className="flex items-center gap-1 px-3 py-1.5 text-xs font-mono rounded"
              style={{ background: copied.prompt ? '#2ed57322' : '#1f1f2e', color: copied.prompt ? '#2ed573' : '#8f8f9d' }}
              data-testid="copy-prompt-btn"
            >
              {copied.prompt ? <Check size={12} /> : <Copy size={12} />}
              {copied.prompt ? 'Copié' : 'Copier'}
            </button>
          </div>
          <pre className="text-xs overflow-auto p-3 rounded max-h-64" style={{ background: '#0a0a0f', color: '#8f8f9d', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
            {config.system_prompt}
          </pre>
        </div>

        {/* OpenAPI Schema */}
        <div className="p-5 rounded-lg" style={{ background: '#12121a', border: '1px solid #1f1f2e' }}>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-bold flex items-center gap-2">
              <Zap size={18} style={{ color: '#3b82f6' }} />
              Schema OpenAPI (Actions)
            </h2>
            <div className="flex items-center gap-2">
              <button
                onClick={() => copyToClipboard(schemaUrl, 'url')}
                className="flex items-center gap-1 px-3 py-1.5 text-xs font-mono rounded"
                style={{ background: copied.url ? '#2ed57322' : '#1f1f2e', color: copied.url ? '#2ed573' : '#8f8f9d' }}
                data-testid="copy-url-btn"
              >
                {copied.url ? <Check size={12} /> : <Copy size={12} />}
                URL
              </button>
              <button
                onClick={() => copyToClipboard(schemaJson, 'schema')}
                className="flex items-center gap-1 px-3 py-1.5 text-xs font-mono rounded"
                style={{ background: copied.schema ? '#2ed57322' : '#1f1f2e', color: copied.schema ? '#2ed573' : '#8f8f9d' }}
                data-testid="copy-schema-btn"
              >
                {copied.schema ? <Check size={12} /> : <Copy size={12} />}
                JSON
              </button>
            </div>
          </div>
          <div className="p-3 rounded mb-3 flex items-center gap-2" style={{ background: '#0a0a0f' }}>
            <span className="text-xs font-mono flex-1 truncate" style={{ color: '#00d4aa' }}>{schemaUrl}</span>
          </div>
          <button
            onClick={() => setExpandSchema(!expandSchema)}
            className="flex items-center gap-1 text-xs font-mono mb-2"
            style={{ color: '#8f8f9d' }}
          >
            {expandSchema ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            {expandSchema ? 'Masquer le schema' : 'Voir le schema complet'}
          </button>
          {expandSchema && (
            <pre className="text-xs overflow-auto p-3 rounded max-h-96" style={{ background: '#0a0a0f', color: '#8f8f9d' }}>
              {schemaJson}
            </pre>
          )}
        </div>

        {/* Live Test */}
        <div className="p-5 rounded-lg" style={{ background: '#12121a', border: '1px solid #1f1f2e' }} data-testid="live-test">
          <h2 className="text-lg font-bold mb-3 flex items-center gap-2">
            <Zap size={18} style={{ color: '#2ed573' }} />
            Test en direct
          </h2>
          <p className="text-xs mb-3" style={{ color: '#8f8f9d' }}>
            Testez comme un agent IA. Tapez en langage naturel :
          </p>
          <div className="flex gap-2 mb-4">
            <input
              type="text"
              value={testQuery}
              onChange={(e) => setTestQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && runTest()}
              placeholder="Ex: Trouve-moi 3 terrains pour un DC de 50MW en PACA"
              className="flex-1 h-10 px-3 text-sm rounded"
              style={{ background: '#0a0a0f', border: '1px solid #1f1f2e', color: '#e8e8ed' }}
              data-testid="test-query-input"
            />
            <button
              onClick={runTest}
              disabled={testLoading}
              className="h-10 px-4 text-xs font-mono uppercase rounded"
              style={{ background: '#00d4aa', color: '#0a0a0f' }}
              data-testid="test-run-btn"
            >
              {testLoading ? '...' : 'Rechercher'}
            </button>
          </div>
          {/* Quick examples */}
          <div className="flex flex-wrap gap-2 mb-4">
            {[
              '20MW en IDF en 12 mois',
              '50MW PACA puissance max',
              '100MW HdF brownfield rapide',
              '10MW pas cher',
            ].map(q => (
              <button
                key={q}
                onClick={() => { setTestQuery(q); }}
                className="text-xs px-2 py-1 rounded"
                style={{ background: '#1f1f2e', color: '#8f8f9d' }}
              >
                {q}
              </button>
            ))}
          </div>
          {testResult && !testResult.error && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs" style={{ color: '#8f8f9d' }}>
                <span>{testResult.meta.total_results} sites trouvés</span>
                <span>{testResult.meta.search_time_ms}ms · stratégie: {testResult.meta.strategy}</span>
              </div>
              <div className="overflow-auto rounded" style={{ background: '#0a0a0f' }}>
                <table className="w-full text-xs">
                  <thead>
                    <tr style={{ borderBottom: '1px solid #1f1f2e' }}>
                      <th className="p-2 text-left font-mono" style={{ color: '#8f8f9d' }}>#</th>
                      <th className="p-2 text-left font-mono" style={{ color: '#8f8f9d' }}>Site</th>
                      <th className="p-2 text-left font-mono" style={{ color: '#8f8f9d' }}>Région</th>
                      <th className="p-2 text-right font-mono" style={{ color: '#8f8f9d' }}>MW</th>
                      <th className="p-2 text-right font-mono" style={{ color: '#8f8f9d' }}>Score</th>
                      <th className="p-2 text-left font-mono hidden md:table-cell" style={{ color: '#8f8f9d' }}>Saturation</th>
                    </tr>
                  </thead>
                  <tbody>
                    {testResult.results.map((r, i) => (
                      <tr key={r.site_id} style={{ borderBottom: '1px solid #1f1f2e08' }}>
                        <td className="p-2" style={{ color: '#8f8f9d' }}>{i + 1}</td>
                        <td className="p-2 font-bold" style={{ color: '#e8e8ed' }}>{r.name}</td>
                        <td className="p-2" style={{ color: '#8f8f9d' }}>{r.location.region}</td>
                        <td className="p-2 text-right font-mono" style={{ color: '#00d4aa' }}>{r.grid.available_capacity_mw}</td>
                        <td className="p-2 text-right font-mono" style={{
                          color: r.score.global >= 80 ? '#2ed573' : r.score.global >= 50 ? '#ffa502' : '#ff4757',
                        }}>{r.score.global.toFixed(0)}</td>
                        <td className="p-2 hidden md:table-cell">
                          <span className="px-1.5 py-0.5 rounded text-xs font-mono" style={{
                            background: r.grid.saturation_level === 'low' ? '#2ed57322' : r.grid.saturation_level === 'medium' ? '#ffa50222' : '#ff475722',
                            color: r.grid.saturation_level === 'low' ? '#2ed573' : r.grid.saturation_level === 'medium' ? '#ffa502' : '#ff4757',
                          }}>
                            {r.grid.saturation_level}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {testResult.results[0] && (
                <div className="p-3 rounded text-xs" style={{ background: '#0a0a0f', border: '1px solid #1f1f2e' }}>
                  <p className="font-mono mb-1" style={{ color: '#00d4aa' }}>Meilleur site :</p>
                  <p style={{ color: '#e8e8ed' }}>{testResult.results[0].comment}</p>
                </div>
              )}
            </div>
          )}
          {testResult?.error && (
            <div className="p-3 rounded text-xs" style={{ background: '#ff475722', color: '#ff4757' }}>
              Erreur: {testResult.error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
