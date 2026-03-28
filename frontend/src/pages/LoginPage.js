import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Server, Zap, Map, TrendingUp, Shield } from 'lucide-react';

export default function LoginPage() {
  const { login } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = () => {
    setIsLoading(true);
    login();
  };

  return (
    <div 
      className="min-h-screen flex"
      style={{ background: '#0a0a0f' }}
    >
      {/* Left panel - Login */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center px-8 lg:px-16">
        <div className="max-w-md mx-auto w-full">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-12">
            <div className="w-10 h-10 flex items-center justify-center" style={{ background: '#00d4aa' }}>
              <Server size={24} style={{ color: '#0a0a0f' }} />
            </div>
            <div>
              <h1 className="text-xl font-bold" style={{ color: '#e8e8ed' }}>COCKPIT IMMO</h1>
              <p className="text-xs font-mono" style={{ color: '#8f8f9d' }}>DC LAND PROSPECTION</p>
            </div>
          </div>

          {/* Title */}
          <h2 className="text-3xl font-bold mb-4" style={{ color: '#e8e8ed' }}>
            Plateforme de prospection foncière Data Center
          </h2>
          <p className="text-sm mb-8" style={{ color: '#8f8f9d' }}>
            Identifiez les meilleures parcelles pour vos projets de data centers en France. 
            Scoring multi-critères, analyse urbanistique, estimation raccordement électrique.
          </p>

          {/* Features */}
          <div className="grid grid-cols-2 gap-4 mb-8">
            <div className="flex items-start gap-2">
              <Zap size={16} style={{ color: '#00d4aa' }} className="mt-1" />
              <div>
                <p className="text-xs font-medium" style={{ color: '#e8e8ed' }}>Raccordement</p>
                <p className="text-xs" style={{ color: '#8f8f9d' }}>Estimation MW & délai</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <Map size={16} style={{ color: '#3b82f6' }} className="mt-1" />
              <div>
                <p className="text-xs font-medium" style={{ color: '#e8e8ed' }}>Cartographie</p>
                <p className="text-xs" style={{ color: '#8f8f9d' }}>Infrastructure réseau</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <TrendingUp size={16} style={{ color: '#00d4aa' }} className="mt-1" />
              <div>
                <p className="text-xs font-medium" style={{ color: '#e8e8ed' }}>Économique</p>
                <p className="text-xs" style={{ color: '#8f8f9d' }}>CAPEX, IRR, P&L</p>
              </div>
            </div>
            <div className="flex items-start gap-2">
              <Shield size={16} style={{ color: '#3b82f6' }} className="mt-1" />
              <div>
                <p className="text-xs font-medium" style={{ color: '#e8e8ed' }}>Urbanisme</p>
                <p className="text-xs" style={{ color: '#8f8f9d' }}>PLU, ICPE, ZAN</p>
              </div>
            </div>
          </div>

          {/* Login button */}
          <button
            onClick={handleLogin}
            disabled={isLoading}
            className="w-full h-12 flex items-center justify-center gap-2 font-mono text-sm uppercase tracking-wider transition-all duration-75"
            style={{
              background: isLoading ? '#1f1f2e' : '#00d4aa',
              color: '#0a0a0f',
              border: 'none'
            }}
            data-testid="google-login-btn"
          >
            {isLoading ? (
              <>
                <div className="loader" style={{ width: 16, height: 16, borderWidth: 2 }}></div>
                Connexion...
              </>
            ) : (
              <>
                <svg width="18" height="18" viewBox="0 0 24 24">
                  <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Connexion avec Google
              </>
            )}
          </button>

          <p className="text-xs text-center mt-4" style={{ color: '#8f8f9d' }}>
            En vous connectant, vous acceptez nos conditions d'utilisation
          </p>
        </div>
      </div>

      {/* Right panel - Visual */}
      <div 
        className="hidden lg:flex w-1/2 items-center justify-center relative overflow-hidden"
        style={{ 
          background: 'linear-gradient(135deg, #12121a 0%, #0a0a0f 100%)',
          borderLeft: '1px solid #1f1f2e'
        }}
      >
        {/* Grid pattern */}
        <div 
          className="absolute inset-0 opacity-30"
          style={{
            backgroundImage: `
              linear-gradient(to right, #1f1f2e 1px, transparent 1px),
              linear-gradient(to bottom, #1f1f2e 1px, transparent 1px)
            `,
            backgroundSize: '40px 40px'
          }}
        />
        
        {/* Stats cards */}
        <div className="relative z-10 space-y-4 p-8">
          <div className="panel p-4" style={{ minWidth: 280 }}>
            <p className="text-xs font-mono uppercase mb-2" style={{ color: '#8f8f9d' }}>Parcelles analysées</p>
            <p className="text-4xl font-mono font-bold" style={{ color: '#00d4aa' }}>60+</p>
            <p className="text-xs mt-1" style={{ color: '#8f8f9d' }}>IDF, PACA, AuRA, HdF, Occitanie</p>
          </div>
          
          <div className="panel p-4">
            <p className="text-xs font-mono uppercase mb-2" style={{ color: '#8f8f9d' }}>Sources de données</p>
            <p className="text-4xl font-mono font-bold" style={{ color: '#3b82f6' }}>25+</p>
            <p className="text-xs mt-1" style={{ color: '#8f8f9d' }}>Cadastre, Enedis, RTE, Géorisques...</p>
          </div>
          
          <div className="panel p-4">
            <p className="text-xs font-mono uppercase mb-2" style={{ color: '#8f8f9d' }}>Critères de scoring</p>
            <div className="flex gap-2 mt-2 flex-wrap">
              <span className="badge badge-success">Électricité</span>
              <span className="badge badge-info">Fibre</span>
              <span className="badge badge-success">Eau</span>
              <span className="badge badge-info">Surface</span>
              <span className="badge badge-warning">PLU</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
