const { useState, useEffect } from React;
const { 
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, 
    PieChart, Pie, Cell, LineChart, Line 
} = window.Recharts;

const StatCard = ({ title, value, icon, color }) => (
    <div className="glass-panel p-6 rounded-xl flex items-center justify-between transition-transform hover:-translate-y-1 duration-300">
        <div>
            <p className="text-slate-400 text-sm font-medium mb-1">{title}</p>
            <h3 className="text-3xl font-bold text-white tracking-tight">{value !== null ? value.toLocaleString() : '...'}</h3>
        </div>
        <div className={`w-12 h-12 rounded-full flex items-center justify-center bg-${color}/10 border border-${color}/20`}>
            <i className={`fa-solid ${icon} text-xl text-${color}`}></i>
        </div>
    </div>
);

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
const SEV_COLORS = { 'Critical': '#ef4444', 'High': '#f59e0b', 'Medium': '#10b981', 'Low': '#3b82f6' };

const Dashboard = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    const loadStats = async () => {
        try {
            const data = await window.api.getDashboardStats();
            setStats(data);
            setLoading(false);
        } catch (err) {
            console.error("Failed to load dashboard stats", err);
        }
    };

    useEffect(() => {
        loadStats();
        const interval = setInterval(loadStats, 10000); // Poll every 10s
        return () => clearInterval(interval);
    }, []);

    if (loading) return <div className="flex h-full items-center justify-center"><div className="w-10 h-10 border-4 border-primary border-t-transparent rounded-full animate-spin"></div></div>;

    const { summary, alert_severity_breakdown, threat_type_breakdown, recent_alerts, recent_incidents } = stats;

    // Formatting for charts
    const threatData = Object.keys(threat_type_breakdown).map(k => ({ name: k, count: threat_type_breakdown[k] }));
    const sevData = Object.keys(alert_severity_breakdown).map(k => ({ name: k, value: alert_severity_breakdown[k] }));

    return (
        <div className="p-6 space-y-6 h-full overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
                <div>
                    <h2 className="text-2xl font-bold text-white">SOC Overview</h2>
                    <p className="text-slate-400 text-sm">Real-time threat intelligence and system status.</p>
                </div>
                <button onClick={loadStats} className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-sm flex items-center gap-2 border border-slate-700 transition-colors">
                    <i className="fa-solid fa-rotate-right"></i> Refresh
                </button>
            </div>

            {/* Top Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard title="Total Logs (24h)" value={summary.total_logs} icon="fa-database" color="primary" />
                <StatCard title="Alerts Fired" value={summary.total_alerts} icon="fa-bell" color="warning" />
                <StatCard title="Active Incidents" value={summary.total_incidents} icon="fa-shield-halved" color="danger" />
                <StatCard title="Blocked IPs" value={summary.total_blocked_ips} icon="fa-ban" color="success" />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Charts */}
                <div className="lg:col-span-2 glass-panel p-6 rounded-xl border border-slate-700/50">
                    <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
                        <i className="fa-solid fa-chart-column text-primary"></i> Top Threat Types
                    </h3>
                    <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={threatData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                                <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
                                <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
                                <RechartsTooltip 
                                    contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px', color: '#f8fafc' }}
                                    itemStyle={{ color: '#3b82f6' }}
                                    cursor={{ fill: 'rgba(51, 65, 85, 0.4)' }}
                                />
                                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="glass-panel p-6 rounded-xl border border-slate-700/50">
                    <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
                        <i className="fa-solid fa-chart-pie text-warning"></i> Alert Severity
                    </h3>
                    <div className="h-64 flex items-center justify-center">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie 
                                    data={sevData} 
                                    cx="50%" cy="50%" 
                                    innerRadius={60} outerRadius={80} 
                                    paddingAngle={5} 
                                    dataKey="value"
                                >
                                    {sevData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={SEV_COLORS[entry.name] || COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <RechartsTooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }} />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="flex justify-center gap-4 text-xs font-medium text-slate-400">
                        {sevData.map(d => (
                            <div key={d.name} className="flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: SEV_COLORS[d.name] }}></span>
                                {d.name}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Recent Incidents Table */}
                <div className="lg:col-span-3 glass-panel p-6 rounded-xl border border-slate-700/50">
                    <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
                        <i className="fa-solid fa-fire text-danger"></i> Recent High-Risk Incidents
                    </h3>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm text-slate-300">
                            <thead className="text-xs text-slate-400 uppercase bg-slate-800/50">
                                <tr>
                                    <th className="px-4 py-3 rounded-tl-lg">Incident</th>
                                    <th className="px-4 py-3">Risk Score</th>
                                    <th className="px-4 py-3">Status</th>
                                    <th className="px-4 py-3">Source IPs</th>
                                    <th className="px-4 py-3 rounded-tr-lg">Time</th>
                                </tr>
                            </thead>
                            <tbody>
                                {recent_incidents.slice(0, 5).map(inc => (
                                    <tr key={inc.id} className="border-b border-slate-700/50 hover:bg-slate-800/30">
                                        <td className="px-4 py-3 font-medium text-white">{inc.title}</td>
                                        <td className="px-4 py-3">
                                            <span className={`px-2 py-1 rounded text-xs font-bold badge-${inc.risk_level.toLowerCase()}`}>
                                                {inc.risk_score} - {inc.risk_level}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3">
                                            <span className="flex items-center gap-1">
                                                <div className={`w-1.5 h-1.5 rounded-full ${inc.status === 'Open' ? 'bg-warning' : inc.status === 'Resolved' ? 'bg-success' : 'bg-primary'}`}></div>
                                                {inc.status}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 font-mono text-xs">{inc.source_ips.join(', ') || 'N/A'}</td>
                                        <td className="px-4 py-3 text-slate-400">{new Date(inc.timestamp).toLocaleString()}</td>
                                    </tr>
                                ))}
                                {recent_incidents.length === 0 && (
                                    <tr>
                                        <td colSpan="5" className="px-4 py-8 text-center text-slate-500">No recent incidents detected.</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
};

window.Dashboard = Dashboard;
