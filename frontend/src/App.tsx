import { useEffect, useState } from 'react';
import ReportPage from './components/ReportPage';
import LoginPage from './components/LoginPage';

const BFF_URL = 'http://localhost:8081';

function App() {
    const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);

    useEffect(() => {
        fetch(`${BFF_URL}/auth/status`, { credentials: 'include' })
            .then(res => {
                if (res.ok) {
                    setIsAuthenticated(true);
                } else {
                    setIsAuthenticated(false);
                }
            })
            .catch(() => setIsAuthenticated(false));
    }, []);

    if (isAuthenticated === null) {
        return <div className="flex items-center justify-center min-h-screen">Загрузка...</div>;
    }

    return isAuthenticated ? <ReportPage /> : <LoginPage />;
}

export default App;