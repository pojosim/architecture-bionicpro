const BFF_URL = process.env.REACT_APP_BFF_URL || 'http://localhost:8081';

const LoginPage = () => {
    const handleLogin = () => {
        window.location.href = `${BFF_URL}/auth/login`;
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-100">
            <div className="bg-white p-8 rounded-lg shadow-md text-center">
                <h1 className="text-3xl font-bold mb-4 text-gray-800">BionicPRO</h1>
                <p className="text-gray-600 mb-6">For reports please login</p>
                <button
                    onClick={handleLogin}
                    className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg transition duration-200"
                >
                    Login via Keycloak
                </button>
            </div>
        </div>
    );
};

export default LoginPage;