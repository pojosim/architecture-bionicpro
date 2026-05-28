import React from 'react';
import { ReactKeycloakProvider } from '@react-keycloak/web';
import Keycloak, { KeycloakConfig } from 'keycloak-js';
import ReportPage from './components/ReportPage';

const keycloakConfig: KeycloakConfig = {
    url: process.env.REACT_APP_KEYCLOAK_URL || 'http://localhost:8080',
    realm: process.env.REACT_APP_KEYCLOAK_REALM || 'reports-realm',
    clientId: process.env.REACT_APP_KEYCLOAK_CLIENT_ID || 'reports-frontend',
};

const keycloak = new Keycloak(keycloakConfig);

const initOptions = {
    onLoad: 'check-sso',
    pkceMethod: 'S256',
    silentCheckSsoRedirectUri: window.location.origin + '/silent-check-sso.html',
    checkLoginIframe: true,
    checkLoginIframeInterval: 30,
};

const App: React.FC = () => {
    return (
        <ReactKeycloakProvider
            authClient={keycloak}
            initOptions={initOptions}
        >
            <ReportPage />
        </ReactKeycloakProvider>
    );
};

export default App;