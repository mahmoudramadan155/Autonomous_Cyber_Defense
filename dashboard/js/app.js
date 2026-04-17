const { useState, useEffect } = React;

const App = () => {
    const [currentPage, setCurrentPage] = useState('dashboard');
    const [connected, setConnected] = useState(true);

    // Simple connection check
    useEffect(() => {
        const checkConn = async () => {
            try {
                await window.api.getDashboardStats();
                setConnected(true);
            } catch (err) {
                setConnected(false);
            }
        };
        checkConn();
        const interval = setInterval(checkConn, 15000);
        return () => clearInterval(interval);
    }, []);

    const renderPage = () => {
        switch (currentPage) {
            case 'dashboard':
                return <window.Dashboard />;
            case 'alerts':
                return <window.AlertsPage />;
            case 'incidents':
                return <window.IncidentsPage />;
            case 'cases':
                return <window.CasesPage />;
            case 'search':
                return <window.SearchPage />;
            default:
                return <window.Dashboard />;
        }
    };

    return (
        <div className="flex h-screen bg-darker overflow-hidden text-slate-300 relative">
            {/* Ambient Background Glow */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-4xl h-64 bg-primary/10 blur-[120px] rounded-full pointer-events-none"></div>

            {!connected && (
                <div className="absolute top-0 left-0 w-full bg-danger text-white text-center py-1 text-xs font-bold z-50">
                    <i className="fa-solid fa-triangle-exclamation mr-2"></i> Connection to backend lost. Retrying...
                </div>
            )}

            <window.Sidebar currentPage={currentPage} setPage={setCurrentPage} />
            
            <main className="flex-1 relative z-10 overflow-hidden">
                <div className="h-full w-full max-w-7xl mx-auto">
                    {renderPage()}
                </div>
            </main>
        </div>
    );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
