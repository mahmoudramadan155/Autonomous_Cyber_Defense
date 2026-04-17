const { useState } from React;

const SearchPage = () => {
    const [query, setQuery] = useState('');
    const [kind, setKind] = useState('');
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!query.trim()) return;
        
        setLoading(true);
        try {
            const data = await window.api.search(query, kind || null);
            setResults(data.results);
        } catch (err) {
            console.error("Search failed", err);
            alert("Search failed: " + err.message);
        }
        setLoading(false);
    };

    return (
        <div className="p-6 h-full flex flex-col overflow-hidden">
            <div className="mb-8">
                <h2 className="text-2xl font-bold text-white mb-2">Threat Hunt & Investigation</h2>
                <p className="text-slate-400 text-sm mb-6">Search across alerts, incidents, and raw logs using Lucene-like syntax.</p>
                
                <form onSubmit={handleSearch} className="flex gap-4">
                    <div className="flex-1 relative">
                        <i className="fa-solid fa-search absolute left-4 top-1/2 -translate-y-1/2 text-slate-400"></i>
                        <input 
                            type="text" 
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Search IPs, threat types, logs... (e.g. 192.168.1.10)"
                            className="w-full bg-slate-800/80 border border-slate-600 text-white rounded-lg pl-10 pr-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all shadow-inner"
                        />
                    </div>
                    <select 
                        value={kind}
                        onChange={(e) => setKind(e.target.value)}
                        className="bg-slate-800/80 border border-slate-600 text-slate-200 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary"
                    >
                        <option value="">All Sources</option>
                        <option value="incidents">Incidents</option>
                        <option value="alerts">Alerts</option>
                        <option value="logs">Raw Logs</option>
                    </select>
                    <button type="submit" className="px-6 py-3 bg-primary hover:bg-blue-600 text-white rounded-lg font-medium transition-colors shadow-lg shadow-primary/20">
                        {loading ? <i className="fa-solid fa-spinner fa-spin"></i> : 'Search'}
                    </button>
                </form>
            </div>

            <div className="flex-1 overflow-y-auto pr-2 space-y-6">
                {!results && !loading && (
                    <div className="h-64 flex flex-col items-center justify-center text-slate-500 glass-panel rounded-xl border border-slate-700/50">
                        <i className="fa-solid fa-magnifying-glass text-4xl mb-4 opacity-50"></i>
                        <p>Enter a query to begin hunting.</p>
                    </div>
                )}

                {loading && (
                    <div className="py-12 flex justify-center"><div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div></div>
                )}

                {results && (
                    <>
                        {/* Incidents Results */}
                        {results.incidents && results.incidents.length > 0 && (
                            <div>
                                <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                                    <i className="fa-solid fa-shield-halved text-danger"></i> Incidents ({results.incidents.length})
                                </h3>
                                <div className="space-y-3">
                                    {results.incidents.map(inc => (
                                        <div key={inc.id} className="glass-panel p-4 rounded-lg border border-slate-700/50 hover:border-slate-500 transition-colors">
                                            <div className="flex justify-between items-start">
                                                <div>
                                                    <h4 className="text-white font-medium mb-1">{inc.title}</h4>
                                                    <p className="text-xs text-slate-400 font-mono">INC-{inc.id} | {new Date(inc.timestamp).toLocaleString()}</p>
                                                </div>
                                                <span className={`badge-${inc.risk_level.toLowerCase()} px-2 py-0.5 rounded text-xs font-bold border`}>
                                                    Risk: {inc.risk_score}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Alerts Results */}
                        {results.alerts && results.alerts.length > 0 && (
                            <div>
                                <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2 mt-6">
                                    <i className="fa-solid fa-bell text-warning"></i> Alerts ({results.alerts.length})
                                </h3>
                                <div className="glass-panel rounded-lg border border-slate-700/50 overflow-hidden">
                                    <table className="w-full text-left text-sm text-slate-300">
                                        <thead className="bg-slate-800/80 text-xs text-slate-400">
                                            <tr>
                                                <th className="px-4 py-2">Threat</th>
                                                <th className="px-4 py-2">Severity</th>
                                                <th className="px-4 py-2">Source IP</th>
                                                <th className="px-4 py-2">Time</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-slate-700/50">
                                            {results.alerts.map(a => (
                                                <tr key={a.id} className="hover:bg-slate-800/50">
                                                    <td className="px-4 py-2 font-medium text-slate-200">{a.threat_type}</td>
                                                    <td className="px-4 py-2 text-xs"><span className={`badge-${a.severity.toLowerCase()} px-1.5 py-0.5 rounded border`}>{a.severity}</span></td>
                                                    <td className="px-4 py-2 font-mono text-xs text-indigo-300">{a.source_ip}</td>
                                                    <td className="px-4 py-2 text-xs text-slate-400">{new Date(a.timestamp).toLocaleString()}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}

                        {/* Logs Results */}
                        {results.logs && results.logs.length > 0 && (
                            <div>
                                <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2 mt-6">
                                    <i className="fa-solid fa-database text-primary"></i> Raw Logs ({results.logs.length})
                                </h3>
                                <div className="space-y-2 font-mono text-xs">
                                    {results.logs.map(log => (
                                        <div key={log.id} className="bg-slate-900 border border-slate-800 p-3 rounded text-slate-400 flex gap-4 hover:border-slate-600 transition-colors">
                                            <span className="text-slate-500 shrink-0">{new Date(log.timestamp).toISOString()}</span>
                                            <span className="text-primary shrink-0 w-24">{log.source_ip}</span>
                                            <span className="text-success shrink-0 w-12">{log.method}</span>
                                            <span className="text-slate-300 truncate">{log.path}</span>
                                            <span className={log.status_code >= 400 ? 'text-danger' : 'text-slate-500'}>{log.status_code}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {results && Object.keys(results).every(k => results[k].length === 0) && (
                            <div className="text-center py-10 text-slate-500 glass-panel rounded-xl">
                                No results found for "{query}".
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
};

window.SearchPage = SearchPage;
