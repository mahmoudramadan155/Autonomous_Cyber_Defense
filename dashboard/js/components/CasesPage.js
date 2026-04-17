const { useState, useEffect } from React;

const CasesPage = () => {
    const [cases, setCases] = useState([]);
    const [loading, setLoading] = useState(true);

    const loadCases = async () => {
        try {
            const data = await window.api.getCases();
            setCases(data);
            setLoading(false);
        } catch (err) {
            console.error("Failed to load cases", err);
            setLoading(false);
        }
    };

    useEffect(() => {
        loadCases();
    }, []);

    const getPriorityBadge = (prio) => {
        return `badge-${prio.toLowerCase()} px-2 py-0.5 rounded text-xs font-semibold border`;
    };

    return (
        <div className="p-6 h-full flex flex-col">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h2 className="text-2xl font-bold text-white">Case Management</h2>
                    <p className="text-slate-400 text-sm">Track analyst investigations and remediation efforts.</p>
                </div>
                <button className="px-4 py-2 bg-primary hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition-colors shadow-lg shadow-primary/20">
                    <i className="fa-solid fa-plus mr-2"></i> New Case
                </button>
            </div>

            <div className="flex-1 glass-panel rounded-xl border border-slate-700/50 overflow-hidden flex flex-col">
                <div className="overflow-x-auto flex-1">
                    <table className="w-full text-left text-sm text-slate-300">
                        <thead className="text-xs text-slate-400 uppercase bg-slate-800/80 sticky top-0 z-10">
                            <tr>
                                <th className="px-6 py-4 font-semibold">ID</th>
                                <th className="px-6 py-4 font-semibold">Title</th>
                                <th className="px-6 py-4 font-semibold">Status</th>
                                <th className="px-6 py-4 font-semibold">Priority</th>
                                <th className="px-6 py-4 font-semibold">Assignee</th>
                                <th className="px-6 py-4 font-semibold">Created</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-700/50">
                            {loading ? (
                                <tr><td colSpan="6" className="text-center py-10"><div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto"></div></td></tr>
                            ) : cases.length === 0 ? (
                                <tr><td colSpan="6" className="text-center py-10 text-slate-500">No open cases. Good job!</td></tr>
                            ) : (
                                cases.map(c => (
                                    <tr key={c.id} className="hover:bg-slate-800/50 transition-colors cursor-pointer">
                                        <td className="px-6 py-4 whitespace-nowrap text-slate-400 font-mono text-xs">CAS-{c.id.toString().padStart(4, '0')}</td>
                                        <td className="px-6 py-4 font-medium text-white">{c.title}</td>
                                        <td className="px-6 py-4">
                                            <span className="flex items-center gap-1.5 text-xs font-medium text-slate-300">
                                                <div className={`w-2 h-2 rounded-full ${c.status === 'Open' ? 'bg-primary' : c.status === 'Closed' ? 'bg-slate-500' : 'bg-warning'}`}></div>
                                                {c.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className={getPriorityBadge(c.priority)}>
                                                {c.priority}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-slate-400 text-xs">
                                            {c.assigned_to ? (
                                                <div className="flex items-center gap-2">
                                                    <div className="w-6 h-6 rounded-full bg-slate-700 flex items-center justify-center font-bold text-[10px] text-white">
                                                        {c.assigned_to.substring(0, 2).toUpperCase()}
                                                    </div>
                                                    {c.assigned_to}
                                                </div>
                                            ) : (
                                                <span className="italic text-slate-500">Unassigned</span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-xs text-slate-400">{new Date(c.created_at).toLocaleDateString()}</td>
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

window.CasesPage = CasesPage;
