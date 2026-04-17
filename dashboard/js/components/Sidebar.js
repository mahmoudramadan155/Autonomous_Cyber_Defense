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
                        <button
                            key={item.id}
                            onClick={() => setPage(item.id)}
                            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                                isActive 
                                ? 'bg-primary/10 text-primary border border-primary/20 shadow-inner' 
                                : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                            }`}
                        >
                            <i className={`fa-solid ${item.icon} w-5 text-center ${isActive ? 'text-primary' : ''}`}></i>
                            <span className="font-medium">{item.label}</span>
                            {isActive && (
                                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></div>
                            )}
                        </button>
                    );
                })}
            </nav>

            <div className="p-6 border-t border-slate-700/50">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-xs font-bold border border-slate-600">
                        OP
                    </div>
                    <div>
                        <p className="text-sm font-medium text-slate-200">System Operator</p>
                        <p className="text-xs text-success flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-success"></span> Online
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

window.Sidebar = Sidebar;
