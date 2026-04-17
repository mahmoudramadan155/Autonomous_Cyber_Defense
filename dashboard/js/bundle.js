// API Service
const API_BASE_URL = 'http://localhost:8000/api/v1';

const api = {
    async fetch(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const defaultOptions = { headers: { 'Content-Type': 'application/json' } };
        const res = await fetch(url, { ...defaultOptions, ...options });
        if (!res.ok) {
            const error = await res.json().catch(() => ({}));
            throw new Error(error.detail || `HTTP error ${res.status}`);
        }
        return res.status === 204 ? null : await res.json();
    },
    async getDashboardStats() { return this.fetch('/dashboard/'); },
    async getAlerts(params = {}) { return this.fetch(`/alerts/?${new URLSearchParams(params).toString()}`); },
    async getIncidents(params = {}) { return this.fetch(`/incidents/?${new URLSearchParams(params).toString()}`); },
    async getIncidentReport(id) { return this.fetch(`/incidents/${id}/report`); },
    async updateIncidentStatus(id, status) {
        return this.fetch(`/incidents/${id}/status?status=${encodeURIComponent(status)}`, { method: 'PATCH' });
    },
    async executeResponse(data) {
        return this.fetch('/response/execute', { method: 'POST', body: JSON.stringify(data) });
    },
    async getBlockedIPs() { return this.fetch('/blocked-ips/'); },
    async blockIP(ip, reason) {
        return this.fetch('/blocked-ips/', { method: 'POST', body: JSON.stringify({ ip_address: ip, reason }) });
    },
    async unblockIP(ip) { return this.fetch(`/blocked-ips/${encodeURIComponent(ip)}`, { method: 'DELETE' }); },
    async getCases() { return this.fetch('/cases/'); },
    async createCase(data) { return this.fetch('/cases/', { method: 'POST', body: JSON.stringify(data) }); },
    async search(query, kind = null) {
        const params = new URLSearchParams({ q: query });
        if (kind) params.append('kind', kind);
        return this.fetch(`/search/?${params.toString()}`);
    },
    useWebSocket(onMessage) {
        const [status, setStatus] = React.useState('connecting');
        const wsRef = React.useRef(null);
        React.useEffect(() => {
            const connect = () => {
                wsRef.current = new WebSocket(`ws://${window.location.host}/api/v1/ws/alerts`);
                wsRef.current.onopen = () => setStatus('connected');
                wsRef.current.onclose = () => {
                    setStatus('disconnected');
                    setTimeout(connect, 3000);
                };
                wsRef.current.onerror = () => setStatus('error');
                wsRef.current.onmessage = (e) => {
                    const data = JSON.parse(e.data);
                    if (data.type !== 'heartbeat') onMessage(data);
                };
            };
            connect();
            return () => { if (wsRef.current) wsRef.current.close(); };
        }, [onMessage]);
        return status;
    }
};

// ==========================================
// Sidebar Component
// ==========================================
const Sidebar = ({ currentPage, setPage }) => {
    const navItems = [
        { id: 'dashboard', icon: 'fa-chart-line', label: 'Dashboard' },
        { id: 'alerts', icon: 'fa-bell', label: 'Alert Triage' },
        { id: 'incidents', icon: 'fa-shield-halved', label: 'Incidents' },
        { id: 'cases', icon: 'fa-folder-open', label: 'Cases' },
        { id: 'search', icon: 'fa-search', label: 'Investigation' },
    ];
    return (
        <div className="w-64 glass-panel border-r border-slate-700/50 h-screen flex flex-col z-10 transition-all duration-300">
            <div className="p-6 flex items-center gap-3 border-b border-slate-700/50">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary to-indigo-600 flex items-center justify-center shadow-lg shadow-primary/30">
                    <i className="fa-solid fa-shield-virus text-xl text-white"></i>
                </div>
                <div>
                    <h1 className="font-bold text-slate-100 tracking-wide text-sm">DEFENSE</h1>
                    <p className="text-xs text-primary font-medium tracking-widest">PLATFORM</p>
                </div>
            </div>
            <nav className="flex-1 py-6 px-4 space-y-2">
                {navItems.map(item => {
                    const isActive = currentPage === item.id;
                    return (
                        <button key={item.id} onClick={() => setPage(item.id)} className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${isActive ? 'bg-primary/10 text-primary border border-primary/20 shadow-inner' : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'}`}>
                            <i className={`fa-solid ${item.icon} w-5 text-center ${isActive ? 'text-primary' : ''}`}></i>
                            <span className="font-medium">{item.label}</span>
                            {isActive && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></div>}
                        </button>
                    );
                })}
            </nav>
        </div>
    );
};

// ==========================================
// Dashboard Component
// ==========================================
const { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip: RechartsTooltip, ResponsiveContainer, PieChart, Pie, Cell } = window.Recharts;
const StatCard = ({ title, value, icon, color }) => (
    <div className="glass-panel p-6 rounded-xl flex items-center justify-between transition-transform hover:-translate-y-1 duration-300">
        <div>
            <p className="text-slate-400 text-sm font-medium mb-1">{title}</p>
            <h3 className="text-3xl font-bold text-white tracking-tight">{value !== null ? value.toLocaleString() : '...'}</h3>
        </div>
        <div className={`w-12 h-12 rounded-full flex items-center justify-center bg-${color}/10 border border-${color}/20`}><i className={`fa-solid ${icon} text-xl text-${color}`}></i></div>
    </div>
);
const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
const SEV_COLORS = { 'Critical': '#ef4444', 'High': '#f59e0b', 'Medium': '#10b981', 'Low': '#3b82f6' };

const Dashboard = () => {
    const [stats, setStats] = React.useState(null);
    const [loading, setLoading] = React.useState(true);

    const loadStats = async () => {
        try {
            const data = await api.getDashboardStats();
            setStats(data);
            setLoading(false);
        } catch (err) { console.error(err); }
    };

    React.useEffect(() => {
        loadStats();
        const interval = setInterval(loadStats, 10000);
        return () => clearInterval(interval);
    }, []);

    if (loading) return <div className="flex h-full items-center justify-center"><div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin"></div></div>;

    const threatData = Object.keys(stats.threat_type_breakdown).map(k => ({ name: k, count: stats.threat_type_breakdown[k] }));
    const sevData = Object.keys(stats.alert_severity_breakdown).map(k => ({ name: k, value: stats.alert_severity_breakdown[k] }));

    return (
        <div className="p-6 space-y-6 h-full overflow-y-auto">
            <h2 className="text-2xl font-bold text-white">SOC Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard title="Total Logs (24h)" value={stats.summary.total_logs} icon="fa-database" color="primary" />
                <StatCard title="Alerts Fired" value={stats.summary.total_alerts} icon="fa-bell" color="warning" />
                <StatCard title="Active Incidents" value={stats.summary.total_incidents} icon="fa-shield-halved" color="danger" />
                <StatCard title="Blocked IPs" value={stats.summary.total_blocked_ips} icon="fa-ban" color="success" />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 glass-panel p-6 rounded-xl border border-slate-700/50">
                    <h3 className="text-lg font-semibold text-slate-200 mb-4"><i className="fa-solid fa-chart-column text-primary"></i> Top Threat Types</h3>
                    <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={threatData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                                <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
                                <RechartsTooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
                <div className="glass-panel p-6 rounded-xl border border-slate-700/50">
                    <h3 className="text-lg font-semibold text-slate-200 mb-4"><i className="fa-solid fa-chart-pie text-warning"></i> Severity</h3>
                    <div className="h-64 flex items-center justify-center">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie data={sevData} cx="50%" cy="50%" innerRadius={60} outerRadius={80} dataKey="value">
                                    {sevData.map((e, i) => <Cell key={i} fill={SEV_COLORS[e.name] || COLORS[i % COLORS.length]} />)}
                                </Pie>
                                <RechartsTooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    );
};

// ==========================================
// AlertsPage Component
// ==========================================
const AlertsPage = () => {
    const [alerts, setAlerts] = React.useState([]);
    const [loading, setLoading] = React.useState(true);

    React.useEffect(() => {
        api.getAlerts({ limit: 50 }).then(data => { setAlerts(data); setLoading(false); });
    }, []);

    const wsStatus = api.useWebSocket((newAlert) => {
        setAlerts(prev => [newAlert, ...prev].slice(0, 100));
    });

    return (
        <div className="p-6 h-full flex flex-col">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-white">Alert Triage Queue</h2>
                <div className="flex items-center gap-2 text-sm bg-slate-800 px-3 py-1.5 rounded-lg border border-slate-700">
                    <div className={`w-2 h-2 rounded-full ${wsStatus === 'connected' ? 'bg-success animate-pulse' : 'bg-danger'}`}></div>
                    <span className="text-slate-300 font-medium">Stream: {wsStatus}</span>
                </div>
            </div>
            <div className="flex-1 glass-panel rounded-xl overflow-auto border border-slate-700/50">
                <table className="w-full text-left text-sm text-slate-300">
                    <thead className="text-xs text-slate-400 uppercase bg-slate-800/80 sticky top-0">
                        <tr><th className="p-4">Time</th><th className="p-4">Threat Type</th><th className="p-4">Severity</th><th className="p-4">Source IP</th></tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700/50">
                        {loading ? <tr><td colSpan="4" className="text-center p-10">Loading...</td></tr> : 
                            alerts.map(a => (
                                <tr key={a.id} className="hover:bg-slate-800/50">
                                    <td className="p-4 font-mono text-xs">{new Date(a.timestamp).toLocaleString()}</td>
                                    <td className="p-4 text-white font-medium">{a.threat_type}</td>
                                    <td className="p-4"><span className={`badge-${a.severity.toLowerCase()} px-2 py-1 rounded text-xs`}>{a.severity}</span></td>
                                    <td className="p-4 font-mono text-indigo-300">{a.source_ip}</td>
                                </tr>
                            ))
                        }
                    </tbody>
                </table>
            </div>
        </div>
    );
};

// ==========================================
// Other Simple Pages
// ==========================================
// ==========================================
// Incidents Page
// ==========================================
const SEV_BADGE = { Critical: 'bg-red-900/50 text-red-400 border border-red-700', High: 'bg-orange-900/50 text-orange-400 border border-orange-700', Medium: 'bg-yellow-900/50 text-yellow-400 border border-yellow-700', Low: 'bg-blue-900/50 text-blue-400 border border-blue-700' };
const STATUS_BADGE = { open: 'bg-red-900/40 text-red-300', investigating: 'bg-yellow-900/40 text-yellow-300', resolved: 'bg-green-900/40 text-green-300', closed: 'bg-slate-700 text-slate-400' };

const IncidentsPage = () => {
    const [incidents, setIncidents] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [selected, setSelected] = React.useState(null);
    const [report, setReport] = React.useState(null);

    React.useEffect(() => {
        api.getIncidents({ limit: 50 }).then(data => { setIncidents(data); setLoading(false); }).catch(() => setLoading(false));
    }, []);

    const openReport = async (inc) => {
        setSelected(inc);
        setReport(null);
        try { const r = await api.getIncidentReport(inc.id); setReport(r); } catch (e) { setReport({ error: e.message }); }
    };

    const updateStatus = async (id, status) => {
        await api.updateIncidentStatus(id, status);
        setIncidents(prev => prev.map(i => i.id === id ? { ...i, status } : i));
        if (selected && selected.id === id) setSelected(s => ({ ...s, status }));
    };

    if (selected) return (
        <div className="p-6 h-full overflow-y-auto">
            <button onClick={() => setSelected(null)} className="mb-4 flex items-center gap-2 text-primary hover:underline text-sm"><i className="fa-solid fa-arrow-left"></i> Back to Incidents</button>
            <div className="glass-panel rounded-xl border border-slate-700/50 p-6 space-y-4">
                <div className="flex justify-between items-start">
                    <div>
                        <h2 className="text-2xl font-bold text-white">{selected.title}</h2>
                        <p className="text-slate-400 text-sm mt-1">Incident #{selected.id} &bull; Risk Score: <span className="text-danger font-bold">{selected.risk_score ?? '—'}</span></p>
                    </div>
                    <select value={selected.status} onChange={e => updateStatus(selected.id, e.target.value)} className="bg-slate-800 border border-slate-600 text-slate-200 text-sm rounded-lg px-3 py-2">
                        {['open','investigating','resolved','closed'].map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                </div>
                <p className="text-slate-300">{selected.description}</p>
                {!report ? <div className="animate-pulse text-slate-500 text-sm">Loading full report...</div> :
                    report.error ? <div className="text-red-400 text-sm">{report.error}</div> :
                    <div className="space-y-3">
                        <h3 className="font-semibold text-slate-200 border-b border-slate-700 pb-2">Correlated Alerts ({(report.alerts || []).length})</h3>
                        {(report.alerts || []).map(a => (
                            <div key={a.id} className="bg-slate-800/50 rounded-lg p-3 flex justify-between items-center">
                                <div><span className="text-white font-medium">{a.threat_type}</span><span className="ml-3 text-xs text-slate-400">{a.source_ip}</span></div>
                                <span className={`text-xs px-2 py-1 rounded ${SEV_BADGE[a.severity] || ''}`}>{a.severity}</span>
                            </div>
                        ))}
                        <h3 className="font-semibold text-slate-200 border-b border-slate-700 pb-2 pt-2">Response Actions ({(report.response_actions || []).length})</h3>
                        {(report.response_actions || []).length === 0 ? <p className="text-slate-500 text-sm">No automated actions taken yet.</p> :
                            (report.response_actions || []).map(a => (
                                <div key={a.id} className="bg-slate-800/50 rounded-lg p-3 flex justify-between">
                                    <div><span className="text-white font-medium">{a.action_type}</span><span className="ml-2 text-xs text-indigo-300">{a.target}</span></div>
                                    <span className={`text-xs px-2 py-1 rounded ${a.status === 'Success' ? 'bg-green-900/40 text-green-400' : 'bg-yellow-900/40 text-yellow-400'}`}>{a.status}</span>
                                </div>
                            ))
                        }
                    </div>
                }
            </div>
        </div>
    );

    return (
        <div className="p-6 h-full flex flex-col">
            <h2 className="text-2xl font-bold text-white mb-6">Incidents</h2>
            {loading ? <div className="flex justify-center p-10"><div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div></div> :
            <div className="flex-1 overflow-y-auto space-y-3">
                {incidents.length === 0 && <p className="text-slate-500 text-center py-10">No incidents found. Run the pentest simulator to generate some!</p>}
                {incidents.map(inc => (
                    <div key={inc.id} onClick={() => openReport(inc)} className="glass-panel rounded-xl border border-slate-700/50 p-5 cursor-pointer hover:border-primary/50 hover:bg-slate-800/50 transition-all flex items-center justify-between">
                        <div className="flex-1">
                            <div className="flex items-center gap-3">
                                <span className={`text-xs px-2 py-1 rounded ${STATUS_BADGE[inc.status] || ''}`}>{inc.status?.toUpperCase()}</span>
                                <h3 className="text-white font-semibold">{inc.title}</h3>
                            </div>
                            <p className="text-slate-400 text-sm mt-1 truncate">{inc.description}</p>
                        </div>
                        <div className="ml-4 text-right flex-shrink-0">
                            <div className="text-2xl font-bold text-danger">{inc.risk_score ?? '—'}</div>
                            <div className="text-xs text-slate-500">Risk Score</div>
                        </div>
                    </div>
                ))}
            </div>}
        </div>
    );
};

// ==========================================
// Cases Page
// ==========================================
const CasesPage = () => {
    const [cases, setCases] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [showForm, setShowForm] = React.useState(false);
    const [form, setForm] = React.useState({ title: '', description: '', priority: 'Medium' });
    const [saving, setSaving] = React.useState(false);

    const load = () => api.getCases().then(d => { setCases(d); setLoading(false); }).catch(() => setLoading(false));
    React.useEffect(() => { load(); }, []);

    const submit = async (e) => {
        e.preventDefault(); setSaving(true);
        try { await api.createCase(form); setShowForm(false); setForm({ title: '', description: '', priority: 'Medium' }); load(); }
        catch (err) { alert('Error: ' + err.message); }
        setSaving(false);
    };

    return (
        <div className="p-6 h-full flex flex-col">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-white">Cases</h2>
                <button onClick={() => setShowForm(!showForm)} className="flex items-center gap-2 bg-primary hover:bg-primary/80 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                    <i className="fa-solid fa-plus"></i> New Case
                </button>
            </div>
            {showForm && (
                <form onSubmit={submit} className="glass-panel border border-primary/30 rounded-xl p-5 mb-6 space-y-4">
                    <h3 className="font-semibold text-slate-200">Create New Case</h3>
                    <input required value={form.title} onChange={e => setForm(f => ({...f, title: e.target.value}))} placeholder="Case title" className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-slate-200 text-sm" />
                    <textarea value={form.description} onChange={e => setForm(f => ({...f, description: e.target.value}))} placeholder="Description" rows={3} className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-slate-200 text-sm" />
                    <select value={form.priority} onChange={e => setForm(f => ({...f, priority: e.target.value}))} className="bg-slate-800 border border-slate-600 text-slate-200 text-sm rounded-lg px-3 py-2">
                        {['Critical','High','Medium','Low'].map(p => <option key={p}>{p}</option>)}
                    </select>
                    <div className="flex gap-3">
                        <button type="submit" disabled={saving} className="bg-primary text-white px-4 py-2 rounded-lg text-sm font-medium disabled:opacity-50">{saving ? 'Saving...' : 'Create Case'}</button>
                        <button type="button" onClick={() => setShowForm(false)} className="bg-slate-700 text-slate-200 px-4 py-2 rounded-lg text-sm">Cancel</button>
                    </div>
                </form>
            )}
            {loading ? <div className="flex justify-center p-10"><div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div></div> :
            <div className="flex-1 overflow-y-auto space-y-3">
                {cases.length === 0 && <div className="text-center py-16"><i className="fa-solid fa-folder-open text-4xl text-slate-600 mb-3"></i><p className="text-slate-500">No cases yet. Create one to start tracking an investigation.</p></div>}
                {cases.map(c => (
                    <div key={c.id} className="glass-panel rounded-xl border border-slate-700/50 p-5 flex items-center justify-between">
                        <div>
                            <div className="flex items-center gap-2 mb-1">
                                <span className={`text-xs px-2 py-0.5 rounded ${SEV_BADGE[c.priority] || 'bg-slate-700 text-slate-300'}`}>{c.priority}</span>
                                <h3 className="text-white font-semibold">{c.title}</h3>
                            </div>
                            <p className="text-slate-400 text-sm">{c.description}</p>
                        </div>
                        <div className="ml-4 text-xs text-slate-500">{new Date(c.created_at).toLocaleDateString()}</div>
                    </div>
                ))}
            </div>}
        </div>
    );
};

// ==========================================
// Search / Investigation Page
// ==========================================
const SearchPage = () => {
    const [query, setQuery] = React.useState('');
    const [results, setResults] = React.useState(null);
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);

    const doSearch = async (e) => {
        e.preventDefault();
        if (!query.trim()) return;
        setLoading(true); setError(null); setResults(null);
        try { const r = await api.search(query); setResults(r); }
        catch (err) { setError(err.message); }
        setLoading(false);
    };

    return (
        <div className="p-6 h-full flex flex-col">
            <h2 className="text-2xl font-bold text-white mb-6"><i className="fa-solid fa-magnifying-glass text-primary mr-2"></i>Threat Hunt Search</h2>
            <form onSubmit={doSearch} className="flex gap-3 mb-6">
                <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search IPs, threats, incidents, logs..." className="flex-1 bg-slate-800 border border-slate-600 rounded-lg px-4 py-3 text-slate-200 text-sm focus:border-primary focus:outline-none" />
                <button type="submit" disabled={loading} className="bg-primary hover:bg-primary/80 text-white px-6 py-3 rounded-lg font-medium text-sm disabled:opacity-50 transition-colors">
                    {loading ? <i className="fa-solid fa-spinner animate-spin"></i> : 'Search'}
                </button>
            </form>
            {error && <div className="bg-red-900/20 border border-red-700/50 text-red-400 rounded-lg p-4 text-sm">{error}</div>}
            {results && (
                <div className="flex-1 overflow-y-auto space-y-6">
                    {results.alerts && results.alerts.length > 0 && (
                        <div>
                            <h3 className="text-slate-300 font-semibold mb-3 flex items-center gap-2"><i className="fa-solid fa-bell text-warning"></i> Alerts ({results.alerts.length})</h3>
                            <div className="space-y-2">
                                {results.alerts.map(a => (
                                    <div key={a.id} className="glass-panel rounded-lg border border-slate-700/50 p-4 flex items-center justify-between">
                                        <div><span className="text-white font-medium">{a.threat_type}</span><span className="ml-3 text-xs text-slate-400 font-mono">{a.source_ip}</span></div>
                                        <span className={`text-xs px-2 py-1 rounded ${SEV_BADGE[a.severity] || ''}`}>{a.severity}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                    {results.incidents && results.incidents.length > 0 && (
                        <div>
                            <h3 className="text-slate-300 font-semibold mb-3 flex items-center gap-2"><i className="fa-solid fa-shield-halved text-danger"></i> Incidents ({results.incidents.length})</h3>
                            <div className="space-y-2">
                                {results.incidents.map(i => (
                                    <div key={i.id} className="glass-panel rounded-lg border border-slate-700/50 p-4 flex items-center justify-between">
                                        <span className="text-white font-medium">{i.title}</span>
                                        <span className="text-danger font-bold text-sm">Risk: {i.risk_score ?? '—'}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                    {(!results.alerts?.length && !results.incidents?.length) && (
                        <div className="text-center py-16"><i className="fa-solid fa-ghost text-4xl text-slate-600 mb-3"></i><p className="text-slate-500">No results found for "{query}"</p></div>
                    )}
                </div>
            )}
            {!results && !loading && !error && (
                <div className="flex-1 flex flex-col items-center justify-center text-center">
                    <i className="fa-solid fa-radar text-6xl text-slate-700 mb-4"></i>
                    <p className="text-slate-500">Search across all alerts, incidents, and logs.<br/>Try an IP address, threat name, or keyword.</p>
                </div>
            )}
        </div>
    );
};

// ==========================================
// Main App Root
// ==========================================
const App = () => {
    const [currentPage, setCurrentPage] = React.useState('dashboard');
    
    const renderPage = () => {
        switch (currentPage) {
            case 'dashboard': return <Dashboard />;
            case 'alerts': return <AlertsPage />;
            case 'incidents': return <IncidentsPage />;
            case 'cases': return <CasesPage />;
            case 'search': return <SearchPage />;
            default: return <Dashboard />;
        }
    };

    return (
        <div className="flex h-screen bg-darker overflow-hidden text-slate-300">
            <Sidebar currentPage={currentPage} setPage={setCurrentPage} />
            <main className="flex-1 overflow-hidden relative">
                <div className="h-full w-full max-w-7xl mx-auto">{renderPage()}</div>
            </main>
        </div>
    );
};

try {
    const root = ReactDOM.createRoot(document.getElementById('root'));
    root.render(<App />);
} catch (error) {
    document.getElementById('root').innerHTML = `<div style="color:red; padding:20px; font-family:sans-serif;"><h1>Application Error</h1><pre>${error.message}</pre><pre>${error.stack}</pre></div>`;
    console.error("FATAL ERROR:", error);
}
