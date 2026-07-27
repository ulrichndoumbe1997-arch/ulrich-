import React, { useEffect, useState, useRef, useCallback } from 'react';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const DEVICE_ICONS = {
  router:      '🔴',
  switch:      '🔵',
  server:      '🟢',
  workstation: '💻',
  printer:     '🖨️',
  ap:          '📡',
  unknown:     '⬡',
};

const DEVICE_COLORS = {
  router:      '#EF4444',
  switch:      '#3B82F6',
  server:      '#10B981',
  workstation: '#8B5CF6',
  printer:     '#F59E0B',
  ap:          '#06B6D4',
  unknown:     '#6B7280',
};

function App() {
  const [status, setStatus]   = useState(null);
  const [stats, setStats]     = useState(null);
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage]       = useState('dashboard'); // dashboard | topology | scan
  const [selected, setSelected] = useState(null);
  const [scanning, setScanning] = useState(false);
  const [scanNet, setScanNet]   = useState('192.168.1.0/24');
  const [scanMsg, setScanMsg]   = useState('');
  const canvasRef = useRef(null);
  const nodesRef  = useRef([]);

  const fetchAll = useCallback(async () => {
    try {
      const [h, s, d] = await Promise.all([
        fetch(`${API}/health`).then(r => r.json()),
        fetch(`${API}/api/v1/dashboard/stats`).then(r => r.json()),
        fetch(`${API}/api/v1/devices/`).then(r => r.json()),
      ]);
      setStatus(h.status);
      setStats(s);
      setDevices(Array.isArray(d) ? d : []);
    } catch {
      setStatus('unreachable');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
    const t = setInterval(fetchAll, 30000);
    return () => clearInterval(t);
  }, [fetchAll]);

  // ─── Dessin de la carte topologique ──────────────────────────────────────
  useEffect(() => {
    if (page !== 'topology') return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width  = canvas.offsetWidth;
    const H = canvas.height = canvas.offsetHeight;

    ctx.clearRect(0, 0, W, H);

    if (devices.length === 0) {
      ctx.fillStyle = '#64748b';
      ctx.font = '16px system-ui';
      ctx.textAlign = 'center';
      ctx.fillText('Aucun équipement — Lance un scan d\'abord', W / 2, H / 2);
      return;
    }

    // Placement en cercle
    const cx = W / 2, cy = H / 2;
    const radius = Math.min(W, H) * 0.35;
    const nodes = devices.map((d, i) => {
      const angle = (i / devices.length) * Math.PI * 2 - Math.PI / 2;
      return {
        id: d.id,
        x: cx + Math.cos(angle) * (devices.length === 1 ? 0 : radius),
        y: cy + Math.sin(angle) * (devices.length === 1 ? 0 : radius),
        device: d,
        r: 28,
      };
    });
    nodesRef.current = nodes;

    // Lignes vers le centre (hub)
    nodes.forEach(n => {
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.lineTo(n.x, n.y);
      ctx.strokeStyle = n.device.is_active !== false ? '#334155' : '#1f2937';
      ctx.lineWidth = 1.5;
      ctx.setLineDash(n.device.is_active !== false ? [] : [4, 4]);
      ctx.stroke();
      ctx.setLineDash([]);
    });

    // Nœuds
    nodes.forEach(n => {
      const color = DEVICE_COLORS[n.device.device_type] || '#6B7280';
      const isUp  = n.device.is_active !== false;

      // Halo statut
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r + 5, 0, Math.PI * 2);
      ctx.fillStyle = isUp ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)';
      ctx.fill();

      // Cercle principal
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
      ctx.fillStyle = '#1e293b';
      ctx.fill();
      ctx.strokeStyle = isUp ? color : '#EF4444';
      ctx.lineWidth = 2.5;
      ctx.stroke();

      // Icône
      ctx.font = '18px system-ui';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(DEVICE_ICONS[n.device.device_type] || '⬡', n.x, n.y);

      // Label IP
      ctx.font = '11px system-ui';
      ctx.fillStyle = '#94a3b8';
      ctx.textBaseline = 'top';
      ctx.fillText(n.device.ip_address, n.x, n.y + n.r + 6);

      // Label hostname
      if (n.device.hostname) {
        ctx.font = '10px system-ui';
        ctx.fillStyle = '#64748b';
        ctx.fillText(n.device.hostname.substring(0, 14), n.x, n.y + n.r + 20);
      }

      // Point statut
      ctx.beginPath();
      ctx.arc(n.x + n.r - 4, n.y - n.r + 4, 5, 0, Math.PI * 2);
      ctx.fillStyle = isUp ? '#10B981' : '#EF4444';
      ctx.fill();
    });

    // Hub central
    ctx.beginPath();
    ctx.arc(cx, cy, 20, 0, Math.PI * 2);
    ctx.fillStyle = '#0f172a';
    ctx.fill();
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.font = '14px system-ui';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('⬡', cx, cy);

  }, [page, devices]);

  // Clic sur la carte
  const handleCanvasClick = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const hit = nodesRef.current.find(n =>
      Math.hypot(n.x - mx, n.y - my) < n.r + 8
    );
    setSelected(hit ? hit.device : null);
  };

  // Lancer un scan
  const launchScan = async () => {
    setScanning(true);
    setScanMsg('');
    try {
      const r = await fetch(`${API}/api/v1/scan/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ network: scanNet, snmp_community: 'public' }),
      });
      const d = await r.json();
      if (r.ok) {
        setScanMsg(`✅ Scan terminé — ${d.discovered} nouveaux, ${d.updated} mis à jour en ${d.duration_seconds}s`);
        await fetchAll();
        setPage('topology');
      } else {
        setScanMsg(`❌ Erreur : ${d.detail || 'Scan échoué'}`);
      }
    } catch (e) {
      setScanMsg(`❌ Erreur réseau : ${e.message}`);
    } finally {
      setScanning(false);
    }
  };

  const st = {
    app:       { fontFamily: 'system-ui, sans-serif', background: '#0f172a', minHeight: '100vh', color: '#e2e8f0' },
    header:    { background: '#1e293b', borderBottom: '1px solid #334155', padding: '12px 24px', display: 'flex', alignItems: 'center', gap: '12px' },
    logo:      { fontSize: '20px', fontWeight: '700', color: '#38bdf8' },
    nav:       { display: 'flex', gap: '4px', marginLeft: '24px' },
    navBtn:    (active) => ({ background: active ? '#0ea5e9' : 'transparent', color: active ? '#fff' : '#94a3b8', border: 'none', borderRadius: '8px', padding: '6px 14px', fontSize: '13px', cursor: 'pointer', fontWeight: active ? '600' : '400' }),
    badge:     (ok) => ({ fontSize: '11px', padding: '3px 10px', borderRadius: '20px', background: ok ? '#064e3b' : '#450a0a', color: ok ? '#34d399' : '#f87171', marginLeft: 'auto' }),
    main:      { padding: '24px' },
    grid:      { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '12px', marginBottom: '24px' },
    card:      { background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '16px' },
    cardLabel: { fontSize: '11px', color: '#64748b', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.05em' },
    cardVal:   (color) => ({ fontSize: '26px', fontWeight: '700', color: color || '#f1f5f9' }),
    table:     { width: '100%', borderCollapse: 'collapse' },
    th:        { textAlign: 'left', padding: '10px 14px', fontSize: '11px', color: '#64748b', borderBottom: '1px solid #334155', textTransform: 'uppercase' },
    td:        { padding: '11px 14px', fontSize: '13px', borderBottom: '1px solid #1a2332' },
    dot:       (up) => ({ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', background: up ? '#34d399' : '#f87171', marginRight: '6px' }),
    typePill:  (type) => ({ fontSize: '11px', padding: '2px 8px', borderRadius: '6px', background: (DEVICE_COLORS[type] || '#6B7280') + '22', color: DEVICE_COLORS[type] || '#6B7280', border: `1px solid ${(DEVICE_COLORS[type] || '#6B7280')}44` }),
    canvas:    { width: '100%', height: '520px', borderRadius: '12px', cursor: 'crosshair', background: '#0f172a', border: '1px solid #334155' },
    panel:     { background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', padding: '16px', marginTop: '16px' },
    input:     { background: '#0f172a', border: '1px solid #334155', borderRadius: '8px', padding: '10px 14px', color: '#e2e8f0', fontSize: '14px', width: '100%', boxSizing: 'border-box' },
    btn:       (color) => ({ background: color || '#0ea5e9', color: '#fff', border: 'none', borderRadius: '8px', padding: '10px 20px', fontSize: '14px', cursor: 'pointer', fontWeight: '600' }),
    msg:       { marginTop: '12px', padding: '10px 14px', borderRadius: '8px', background: '#1e293b', fontSize: '13px', color: '#94a3b8' },
    detail:    { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '13px' },
    detailK:   { color: '#64748b' },
    detailV:   { color: '#e2e8f0', fontWeight: '500' },
  };

  return (
    <div style={st.app}>

      {/* ── Header ─────────────────────────────────────────────── */}
      <div style={st.header}>
        <span style={st.logo}>⬡ ULRICH</span>
        <nav style={st.nav}>
          {[['dashboard','📊 Dashboard'],['topology','🗺️ Carte réseau'],['scan','🔍 Scanner']].map(([id, label]) => (
            <button key={id} style={st.navBtn(page === id)} onClick={() => setPage(id)}>{label}</button>
          ))}
        </nav>
        <span style={st.badge(status === 'ok')}>
          {status === 'ok' ? '● API connectée' : '● API hors ligne'}
        </span>
      </div>

      <div style={st.main}>

        {/* ── DASHBOARD ──────────────────────────────────────────── */}
        {page === 'dashboard' && (
          <>
            {stats && (
              <div style={st.grid}>
                <div style={st.card}><div style={st.cardLabel}>Total</div><div style={st.cardVal()}>  {stats.total_devices}</div></div>
                <div style={st.card}><div style={st.cardLabel}>En ligne</div><div style={st.cardVal('#34d399')}>{stats.devices_up}</div></div>
                <div style={st.card}><div style={st.cardLabel}>Hors ligne</div><div style={st.cardVal(stats.devices_down > 0 ? '#f87171' : '#34d399')}>{stats.devices_down}</div></div>
                <div style={st.card}><div style={st.cardLabel}>Disponibilité</div><div style={st.cardVal('#38bdf8')}>{stats.uptime_percent}%</div></div>
                <div style={st.card}><div style={st.cardLabel}>Incidents</div><div style={st.cardVal(stats.open_incidents > 0 ? '#fb923c' : '#34d399')}>{stats.open_incidents}</div></div>
              </div>
            )}

            {/* Répartition par type */}
            {stats && Object.keys(stats.by_type || {}).length > 0 && (
              <div style={{ ...st.card, marginBottom: '16px' }}>
                <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Répartition par type</div>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  {Object.entries(stats.by_type).map(([type, count]) => (
                    <span key={type} style={{ ...st.typePill(type), padding: '4px 12px', fontSize: '13px' }}>
                      {DEVICE_ICONS[type]} {type} ({count})
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Liste équipements */}
            <div style={{ ...st.card, padding: '0', overflow: 'hidden' }}>
              <div style={{ padding: '14px 16px', borderBottom: '1px solid #334155', fontSize: '13px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Équipements découverts
              </div>
              {loading ? (
                <div style={{ padding: '40px', textAlign: 'center', color: '#475569' }}>Chargement...</div>
              ) : devices.length === 0 ? (
                <div style={{ padding: '60px', textAlign: 'center', color: '#475569' }}>
                  <div style={{ fontSize: '36px', marginBottom: '12px' }}>🔍</div>
                  <div>Aucun équipement — <button style={{ ...st.btn(), padding: '6px 14px', fontSize: '13px' }} onClick={() => setPage('scan')}>Lance un scan</button></div>
                </div>
              ) : (
                <table style={st.table}>
                  <thead>
                    <tr>
                      {['Statut','IP','Hostname','Type','Latence','Uptime 24h'].map(h => (
                        <th key={h} style={st.th}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {devices.map(d => (
                      <tr key={d.id} style={{ cursor: 'pointer' }} onClick={() => { setSelected(d); setPage('topology'); }}>
                        <td style={st.td}><span style={st.dot(d.is_active !== false)}/>{d.is_active !== false ? 'En ligne' : 'Hors ligne'}</td>
                        <td style={{ ...st.td, fontFamily: 'monospace', color: '#7dd3fc' }}>{d.ip_address}</td>
                        <td style={{ ...st.td, color: '#94a3b8' }}>{d.hostname || '—'}</td>
                        <td style={st.td}><span style={st.typePill(d.device_type)}>{DEVICE_ICONS[d.device_type]} {d.device_type}</span></td>
                        <td style={st.td}>{d.latency_ms ? `${d.latency_ms} ms` : '—'}</td>
                        <td style={st.td}>{d.uptime_percent != null ? `${d.uptime_percent}%` : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </>
        )}

        {/* ── CARTE TOPOLOGIQUE ──────────────────────────────────── */}
        {page === 'topology' && (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <span style={{ fontSize: '15px', fontWeight: '600', color: '#94a3b8' }}>Carte du réseau</span>
              <span style={{ fontSize: '12px', color: '#475569' }}>Cliquez sur un équipement pour voir ses détails</span>
              <button style={{ ...st.btn('#1e293b'), border: '1px solid #334155', color: '#94a3b8', marginLeft: 'auto', padding: '6px 14px', fontSize: '12px' }} onClick={() => { setSelected(null); fetchAll(); }}>
                ↻ Rafraîchir
              </button>
            </div>

            <canvas ref={canvasRef} style={st.canvas} onClick={handleCanvasClick}/>

            {/* Légende */}
            <div style={{ display: 'flex', gap: '16px', marginTop: '12px', flexWrap: 'wrap' }}>
              {Object.entries(DEVICE_ICONS).map(([type, icon]) => (
                <span key={type} style={{ fontSize: '12px', color: '#64748b', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: DEVICE_COLORS[type], display: 'inline-block' }}/>
                  {icon} {type}
                </span>
              ))}
              <span style={{ fontSize: '12px', color: '#64748b', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#10B981', display: 'inline-block' }}/> En ligne
              </span>
              <span style={{ fontSize: '12px', color: '#64748b', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#EF4444', display: 'inline-block' }}/> Hors ligne
              </span>
            </div>

            {/* Panneau détail équipement */}
            {selected && (
              <div style={st.panel}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
                  <span style={{ fontSize: '24px' }}>{DEVICE_ICONS[selected.device_type]}</span>
                  <div>
                    <div style={{ fontSize: '15px', fontWeight: '600' }}>{selected.hostname || selected.ip_address}</div>
                    <div style={{ fontSize: '12px', color: '#64748b' }}>{selected.device_type}</div>
                  </div>
                  <span style={{ marginLeft: 'auto', ...st.dot(selected.is_active !== false), width: '10px', height: '10px' }}/>
                  <span style={{ fontSize: '13px', color: selected.is_active !== false ? '#34d399' : '#f87171' }}>
                    {selected.is_active !== false ? 'En ligne' : 'Hors ligne'}
                  </span>
                  <button style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: '18px' }} onClick={() => setSelected(null)}>✕</button>
                </div>
                <div style={st.detail}>
                  <span style={st.detailK}>Adresse IP</span><span style={{ ...st.detailV, fontFamily: 'monospace', color: '#7dd3fc' }}>{selected.ip_address}</span>
                  <span style={st.detailK}>MAC</span><span style={st.detailV}>{selected.mac_address || '—'}</span>
                  <span style={st.detailK}>Fabricant</span><span style={st.detailV}>{selected.vendor || '—'}</span>
                  <span style={st.detailK}>Système</span><span style={st.detailV}>{selected.os_info || '—'}</span>
                  <span style={st.detailK}>Latence</span><span style={st.detailV}>{selected.latency_ms ? `${selected.latency_ms} ms` : '—'}</span>
                  <span style={st.detailK}>Uptime 24h</span><span style={st.detailV}>{selected.uptime_percent != null ? `${selected.uptime_percent}%` : '—'}</span>
                  <span style={st.detailK}>Première vue</span><span style={st.detailV}>{selected.first_seen ? new Date(selected.first_seen).toLocaleString('fr-FR') : '—'}</span>
                  <span style={st.detailK}>Dernière vue</span><span style={st.detailV}>{selected.last_seen ? new Date(selected.last_seen).toLocaleString('fr-FR') : '—'}</span>
                  {selected.open_ports?.length > 0 && (
                    <>
                      <span style={st.detailK}>Ports ouverts</span>
                      <span style={st.detailV}>{selected.open_ports.map(p => `${p.port}/${p.protocol}`).join(', ')}</span>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── SCANNER ────────────────────────────────────────────── */}
        {page === 'scan' && (
          <div style={{ maxWidth: '560px' }}>
            <div style={{ fontSize: '15px', fontWeight: '600', color: '#94a3b8', marginBottom: '20px' }}>Scanner le réseau</div>

            <div style={st.card}>
              <div style={{ marginBottom: '14px' }}>
                <label style={{ fontSize: '12px', color: '#64748b', display: 'block', marginBottom: '6px' }}>PLAGE RÉSEAU (CIDR)</label>
                <input
                  style={st.input}
                  value={scanNet}
                  onChange={e => setScanNet(e.target.value)}
                  placeholder="ex: 192.168.1.0/24"
                />
                <div style={{ fontSize: '11px', color: '#475569', marginTop: '4px' }}>
                  💡 Remplace par ta plage réseau réelle (ex: 192.168.0.0/24)
                </div>
              </div>

              <button
                style={{ ...st.btn(scanning ? '#334155' : '#0ea5e9'), width: '100%', opacity: scanning ? 0.7 : 1 }}
                onClick={launchScan}
                disabled={scanning}
              >
                {scanning ? '⏳ Scan en cours...' : '🔍 Lancer le scan réseau'}
              </button>

              {scanMsg && <div style={st.msg}>{scanMsg}</div>}
            </div>

            <div style={{ ...st.card, marginTop: '16px' }}>
              <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '10px' }}>Comment trouver ta plage réseau ?</div>
              <div style={{ fontSize: '12px', color: '#94a3b8', lineHeight: '1.8' }}>
                Dans le terminal VS Code, tape :<br/>
                <code style={{ background: '#0f172a', padding: '2px 6px', borderRadius: '4px', color: '#7dd3fc' }}>ipconfig</code><br/>
                Cherche <strong>"Passerelle par défaut"</strong> — ex: 192.168.1.1<br/>
                Ta plage est : <strong>192.168.1.0/24</strong>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

export default App;
