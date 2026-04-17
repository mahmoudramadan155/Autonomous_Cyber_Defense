const { useState, useEffect } from React;

const AlertsPage = () => {
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);

    // Initial load
    useEffect(() => {
        window.api.getAlerts({ limit: 50 }).then(data => {
            setAlerts(data);
            setLoading(false);
        });
    }, []);

    // WebSocket real-time updates
    const wsStatus = window.api.useWebSocket((newAlert) => {
        // Handle new alert from WebSocket
        setAlerts(prev => [newAlert, ...prev].slice(0, 100)); // Keep last 100
    });

    const getSeverityBadge = (sev) => {
        return `badge-${sev.toLowerCase()} px-2.5 py-1 rounded-md text-xs font-semibold border`;
    };

    return (
        <div className="p-6 h-full flex flex-col">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h2 className="text-2xl font-bold text-white">Alert Triage Queue</h2>
                    <p className="text-slate-400 text-sm">Real-time stream of threat detection signals.</p>
                </div>
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2 text-sm bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700">
                        <div className={`w-2 h-2 rounded-full ${wsStatus === 'connected' ? 'bg-success animate-pulse' : 'bg-danger'}`}></div>
                        <span className="text-slate-300 font-medium">Live Stream: {wsStatus}</span>
                    </div>
                </div>
            </div>

            <div className="flex-1 glass-panel rounded-xl border border-slate-700/50 overflow-hidden flex flex-col">
                <div className="overflow-x-auto flex-1">
                    <table className="w-full text-left text-sm text-slate-300">
                        <thead className="text-xs text-slate-400 uppercase bg-slate-800/80 sticky top-0 z-10 shadow-md">
                            <tr>
                                <th className="px-6 py-4 font-semibold">Timestamp</th>
                                <th className="px-6 py-4 font-semibold">Threat Type</th>
                                <th className="px-6 py-4 font-semibold">Severity</th>
                                <th className="px-6 py-4 font-semibold">Source IP</th>
                                <th className="px-6 py-4 font-semibold">MITRE ATT&CK</th>
                                <th className="px-6 py-4 font-semibold text-right">Confidence</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700/50">
                            {loading ? (
                                <tr><td colSpan="6" className="text-center py-10"><div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto"></div></td></tr>
                            ) : alerts.length === 0 ? (
                                <tr><td colSpan="6" className="text-center py-10 text-slate-500">No alerts found.</td></tr>
                            ) : (
                                alerts.map(alert => (
                                    <tr key={alert.id || alert.timestamp} className="hover:bg-slate-800/50 transition-colors group">
                                        <td className="px-6 py-4 whitespace-nowrap text-slate-400 font-mono text-xs">
                                            {new Date(alert.timestamp).toLocaleString()}
                                        </td>
                                        <td className="px-6 py-4 font-medium text-white flex items-center gap-2">
                                            {alert.threat_type === 'SQL Injection' && <i className="fa-solid fa-database text-primary"></i>}
                                            {alert.threat_type === 'Brute Force' && <i className="fa-solid fa-key text-warning"></i>}
                                            {alert.threat_type === 'DDoS' && <i className="fa-solid fa-network-wired text-danger"></i>}
                                            {alert.threat_type}
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={getSeverityBadge(alert.severity)}>
                                                {alert.severity}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 font-mono text-xs text-indigo-300">{alert.source_ip}</td>
                                        <td className="px-6 py-4 text-xs text-slate-400">
                                            {alert.mitre_tactic ? (
                                                <div className="flex gap-1 flex-wrap">
                                                    <span className="bg-slate-800 px-1.5 py-0.5 rounded border border-slate-700">{alert.mitre_tactic}</span>
                                                    {alert.mitre_technique && <span className="bg-slate-800 px-1.5 py-0.5 rounded border border-slate-700">{alert.mitre_technique}</span>}
                                                </div>
                                            ) : (
                                                <span className="opacity-50">-</span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="flex items-center justify-end gap-2">
                                                <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                                    <div 
                                                        className="h-full bg-primary" 
                                                        style={{ width: `${(alert.confidence || 0) * 100}%` }}
                                                    ></div>
                                                </div>
                                                <span className="text-xs font-mono w-8">{((alert.confidence || 0) * 100).toFixed(0)}%</span>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

window.AlertsPage = AlertsPage;
