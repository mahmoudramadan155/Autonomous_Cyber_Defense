// API Service for interacting with FastAPI backend
// Uses relative paths so Nginx can proxy /api/ → http://api:8000 internally
// Access dashboard at http://localhost:3000 — all API calls go through the same port.
const API_BASE_URL = '/api/v1';

const api = {
    // Helper for fetch
    async fetch(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };
        const res = await fetch(url, { ...defaultOptions, ...options });
        if (!res.ok) {
            const error = await res.json().catch(() => ({}));
            throw new Error(error.detail || `HTTP error ${res.status}`);
        }
        return res.status === 204 ? null : await res.json();
    },

    // Dashboard
    async getDashboardStats() {
        return this.fetch('/dashboard/');
    },

    // Alerts
    async getAlerts(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.fetch(`/alerts/?${query}`);
    },

    // Incidents
    async getIncidents(params = {}) {
        const query = new URLSearchParams(params).toString();
        return this.fetch(`/incidents/?${query}`);
    },
    
    async getIncidentReport(id) {
        return this.fetch(`/incidents/${id}/report`);
    },
    
    async updateIncidentStatus(id, status) {
        return this.fetch(`/incidents/${id}/status?status=${encodeURIComponent(status)}`, {
            method: 'PATCH',
        });
    },

    // Response Actions
    async executeResponse(data) {
        return this.fetch('/response/execute', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    // Blocked IPs
    async getBlockedIPs() {
        return this.fetch('/blocked-ips/');
    },
    
    async blockIP(ip, reason) {
        return this.fetch('/blocked-ips/', {
            method: 'POST',
            body: JSON.stringify({ ip_address: ip, reason }),
        });
    },
    
    async unblockIP(ip) {
        return this.fetch(`/blocked-ips/${encodeURIComponent(ip)}`, {
            method: 'DELETE',
        });
    },

    // Cases
    async getCases() {
        return this.fetch('/cases/');
    },
    
    async createCase(data) {
        return this.fetch('/cases/', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    // Search
    async search(query, kind = null) {
        const params = new URLSearchParams({ q: query });
        if (kind) params.append('kind', kind);
        return this.fetch(`/search/?${params.toString()}`);
    },

    // WebSocket Hook (custom hook helper)
    useWebSocket(onMessage) {
        const [status, setStatus] = React.useState('connecting');
        const wsRef = React.useRef(null);

        React.useEffect(() => {
            const connect = () => {
                wsRef.current = new WebSocket(`ws://${window.location.host}/api/v1/ws/alerts`);
                
                wsRef.current.onopen = () => setStatus('connected');
                
                wsRef.current.onclose = () => {
                    setStatus('disconnected');
                    // Reconnect logic
                    setTimeout(connect, 3000);
                };
                
                wsRef.current.onerror = () => setStatus('error');
                
                wsRef.current.onmessage = (e) => {
                    const data = JSON.parse(e.data);
                    if (data.type !== 'heartbeat') {
                        onMessage(data);
                    }
                };
            };
            
            connect();
            
            return () => {
                if (wsRef.current) wsRef.current.close();
            };
        }, [onMessage]);

        return status;
    }
};

window.api = api;
