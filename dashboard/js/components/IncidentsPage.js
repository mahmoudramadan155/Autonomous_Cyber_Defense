const { useState, useEffect } from React;

const IncidentsPage = () => {
    const [incidents, setIncidents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedIncident, setSelectedIncident] = useState(null);
    const [report, setReport] = useState(null);
    const [actionLoading, setActionLoading] = useState(false);

    const loadIncidents = async () => {
        try {
            const data = await window.api.getIncidents();
            setIncidents(data);
            setLoading(false);
        } catch (err) {
            console.error("Failed to load incidents", err);
            setLoading(false);
        }
    };

    useEffect(() => {
        loadIncidents();
        const interval = setInterval(loadIncidents, 15000);
        return () => clearInterval(interval);
    }, []);

    const viewDetails = async (incident) => {
        setSelectedIncident(incident);
        setReport(null);
        try {
            const data = await window.api.getIncidentReport(incident.id);
            setReport(data);
        } catch (err) {
            console.error("Failed to load report", err);
        }
    };

    const handleBlockIP = async (ip) => {
        if (!ip) return;
        setActionLoading(true);
        try {
            await window.api.blockIP(ip, `Manual block from Incident ${selectedIncident.id}`);
            alert(`Successfully blocked IP: ${ip}`);
            loadIncidents();
        } catch (err) {
            alert(`Failed to block IP: ${err.message}`);
        }
        setActionLoading(false);
    };

    const handleStatusChange = async (status) => {
        setActionLoading(true);
        try {
            await window.api.updateIncidentStatus(selectedIncident.id, status);
            const updated = { ...selectedIncident, status };
            setSelectedIncident(updated);
            setIncidents(incidents.map(i => i.id === updated.id ? updated : i));
        } catch (err) {
            alert(`Failed to update status: ${err.message}`);
        }
        setActionLoading(false);
    };

    if (selectedIncident) {
        return (
            <div className="p-6 h-full flex flex-col overflow-y-auto">
                <button 
                    onClick={() => setSelectedIncident(null)}
                    className="self-start mb-4 text-slate-400 hover:text-white flex items-center gap-2 transition-colors"
                >
                    <i className="fa-solid fa-arrow-left"></i> Back to Incidents
                </button>

                <div className="glass-panel p-8 rounded-xl border border-slate-700/50 mb-6 relative overflow-hidden">
                    {/* Background glow based on risk */}
                    <div className={`absolute -top-24 -right-24 w-64 h-64 rounded-full blur-3xl opacity-20 pointer-events-none 
                        ${selectedIncident.risk_level === 'Critical' ? 'bg-danger' : 
                          selectedIncident.risk_level === 'High' ? 'bg-warning' : 'bg-primary'}`}>
                    </div>

                    <div className="flex justify-between items-start mb-6 relative z-10">
                        <div>
                            <div className="flex items-center gap-3 mb-2">
                                <span className={`px-2.5 py-1 rounded-md text-xs font-bold border badge-${selectedIncident.risk_level.toLowerCase()}`}>
                                    Risk Score: {selectedIncident.risk_score} ({selectedIncident.risk_level})
                                </span>
                                <span className="px-2.5 py-1 rounded-md text-xs font-bold border bg-slate-800 text-slate-300 border-slate-600">
                                    Status: {selectedIncident.status}
                                </span>
                            </div>
                            <h2 className="text-3xl font-bold text-white mb-2">{selectedIncident.title}</h2>
                            <p className="text-slate-400 font-mono text-sm">Incident ID: INC-{selectedIncident.id.toString().padStart(5, '0')} | {new Date(selectedIncident.timestamp).toLocaleString()}</p>
                        </div>
                        
                        <div className="flex gap-2">
                            {selectedIncident.status !== 'Resolved' && (
                                <button 
                                    onClick={() => handleStatusChange('Resolved')}
                                    disabled={actionLoading}
                                    className="px-4 py-2 bg-success/20 hover:bg-success/30 text-success border border-success/30 rounded-lg text-sm font-medium transition-colors"
                                >
                                    <i className="fa-solid fa-check mr-2"></i> Mark Resolved
                                </button>
                            )}
                        </div>
                    </div>

                    {report ? (
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-8">
                            <div className="lg:col-span-2 space-y-6">
                                <div>
                                    <h3 className="text-lg font-semibold text-white border-b border-slate-700 pb-2 mb-3">Analysis & Root Cause</h3>
                                    <p className="text-slate-300 leading-relaxed">{report.root_cause || "Analysis pending."}</p>
                                </div>
                                
                                <div>
                                    <h3 className="text-lg font-semibold text-white border-b border-slate-700 pb-2 mb-3">Timeline</h3>
                                    <div className="space-y-4 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-700 before:to-transparent">
                                        {report.timeline.map((event, idx) => (
                                            <div key={idx} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                                                <div className="flex items-center justify-center w-10 h-10 rounded-full border-4 border-slate-900 bg-slate-800 text-slate-400 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
                                                    <i className={`fa-solid text-xs ${event.type === 'alert' ? 'fa-bell text-warning' : 'fa-shield text-primary'}`}></i>
                                                </div>
                                                <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] glass-panel p-4 rounded border border-slate-700/50 shadow">
                                                    <div className="flex justify-between items-center mb-1">
                                                        <span className="font-bold text-slate-200 text-sm">{event.detail}</span>
                                                        <time className="font-mono text-xs text-slate-500">{new Date(event.timestamp).toLocaleTimeString()}</time>
                                                    </div>
                                                    {event.source_ip && <div className="text-xs text-indigo-400 font-mono">Src: {event.source_ip}</div>}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            <div className="space-y-6">
                                <div className="bg-slate-900/50 p-5 rounded-xl border border-slate-800">
                                    <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Threat Intel</h3>
                                    
                                    <div className="mb-4">
                                        <p className="text-xs text-slate-500 mb-1">Attack Vectors</p>
                                        <div className="flex flex-wrap gap-2">
                                            {report.mitre_tactics.length > 0 ? report.mitre_tactics.map(t => (
                                                <span key={t} className="px-2 py-1 bg-slate-800 border border-slate-700 rounded text-xs text-slate-300">{t}</span>
                                            )) : <span className="text-sm text-slate-600">None detected</span>}
                                        </div>
                                    </div>
                                    
                                    <div>
                                        <p className="text-xs text-slate-500 mb-1">Source Infrastructure</p>
                                        <ul className="space-y-2">
                                            {report.source_ips.map(ip => (
                                                <li key={ip} className="flex justify-between items-center text-sm font-mono text-indigo-300">
                                                    {ip}
                                                    <button 
                                                        onClick={() => handleBlockIP(ip)}
                                                        disabled={actionLoading}
                                                        className="px-2 py-1 bg-danger/20 hover:bg-danger/40 text-danger rounded border border-danger/30 text-xs transition-colors"
                                                    >
                                                        Block IP
                                                    </button>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                </div>

                                <div className="bg-slate-900/50 p-5 rounded-xl border border-slate-800">
                                    <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Playbook Recommendations</h3>
                                    <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-line">
                                        {report.recommendations || "1. Isolate affected hosts.\n2. Block offending IPs.\n3. Review access logs."}
                                    </p>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="py-12 flex justify-center"><div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div></div>
                    )}
                </div>
            </div>
        );
    }

    return (
        <div className="p-6 h-full flex flex-col">
            <div className="mb-6">
                <h2 className="text-2xl font-bold text-white">Incident Response</h2>
                <p className="text-slate-400 text-sm">Correlated threat events requiring investigation.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {loading ? (
                    <div className="col-span-full py-12 flex justify-center"><div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div></div>
                ) : incidents.length === 0 ? (
                    <div className="col-span-full text-center py-12 text-slate-500 glass-panel rounded-xl">No active incidents found.</div>
                ) : (
                    incidents.map(incident => (
                        <div key={incident.id} className="glass-panel p-6 rounded-xl border border-slate-700/50 flex flex-col hover:border-slate-600 transition-colors group cursor-pointer" onClick={() => viewDetails(incident)}>
                            <div className="flex justify-between items-start mb-4">
                                <span className={`px-2 py-1 rounded text-xs font-bold border badge-${incident.risk_level.toLowerCase()}`}>
                                    Risk: {incident.risk_score}
                                </span>
                                <span className="text-xs font-mono text-slate-500">{new Date(incident.timestamp).toLocaleTimeString()}</span>
                            </div>
                            
                            <h3 className="text-lg font-bold text-slate-100 mb-2 group-hover:text-primary transition-colors">{incident.title}</h3>
                            <p className="text-sm text-slate-400 line-clamp-2 mb-4 flex-1">{incident.description}</p>
                            
                            <div className="mt-auto pt-4 border-t border-slate-700/50 flex justify-between items-center">
                                <div className="flex -space-x-2">
                                    <div className="w-8 h-8 rounded-full bg-slate-800 border-2 border-slate-700 flex items-center justify-center text-xs font-bold text-slate-400" title="Alerts Count">
                                        {incident.alerts?.length || 0}
                                    </div>
                                </div>
                                <div className="text-xs font-medium text-slate-400 flex items-center gap-1">
                                    <div className={`w-2 h-2 rounded-full ${incident.status === 'Open' ? 'bg-warning' : incident.status === 'Resolved' ? 'bg-success' : 'bg-primary'}`}></div>
                                    {incident.status}
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

window.IncidentsPage = IncidentsPage;
