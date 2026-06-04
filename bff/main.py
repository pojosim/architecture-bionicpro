import os
import secrets
import base64
import hashlib
import time
import redis
import requests
from flask import Flask, request, redirect, jsonify, session
from flask_session import Session
from functools import wraps
from urllib.parse import urlencode
from flask_cors import CORS

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))

CORS(app,
     supports_credentials=True,
     origins=["http://localhost:3000"],
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "OPTIONS"])

app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379/0'))
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False   # True в prod
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

Session(app)

KEYCLOAK_INTERNAL_URL = os.environ.get('KEYCLOAK_INTERNAL_URL', 'http://keycloak:8080')
KEYCLOAK_EXTERNAL_URL = os.environ.get('KEYCLOAK_EXTERNAL_URL', 'http://localhost:8080')
REALM = os.environ.get('KEYCLOAK_REALM', 'reports-realm')
CLIENT_ID = os.environ.get('KEYCLOAK_CLIENT_ID', 'reports-frontend')
CLIENT_SECRET = os.environ.get('KEYCLOAK_CLIENT_SECRET', 'oNwoLQdvJAvRcL89SydqCWCe5ry1jMgq')
REDIRECT_URI = os.environ.get('REDIRECT_URI', 'http://localhost:8081/auth/callback')
BACKEND_API_URL = os.environ.get('BACKEND_API_URL', 'http://reports-api:8000')

def generate_pkce_pair():
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode('utf-8').rstrip('=')
    return code_verifier, code_challenge

@app.route('/auth/login')
def login():
    verifier, challenge = generate_pkce_pair()
    session['code_verifier'] = verifier
    auth_endpoint = f"{KEYCLOAK_EXTERNAL_URL}/realms/{REALM}/protocol/openid-connect/auth"
    params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'code_challenge': challenge,
        'code_challenge_method': 'S256',
        'scope': 'openid profile email',
        'prompt': 'login'
    }
    auth_url = f"{auth_endpoint}?{urlencode(params)}"
    return redirect(auth_url)

@app.route('/auth/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'missing code'}), 400
    verifier = session.pop('code_verifier', None)
    if not verifier:
        return jsonify({'error': 'missing verifier'}), 400

    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code_verifier': verifier
    }
    resp = requests.post(f"{KEYCLOAK_INTERNAL_URL}/realms/{REALM}/protocol/openid-connect/token", data=data)
    if resp.status_code != 200:
        return jsonify({'error': 'token exchange failed'}), 500
    tokens = resp.json()
    session['access_token'] = tokens['access_token']
    session['refresh_token'] = tokens['refresh_token']
    session['expires_at'] = time.time() + tokens.get('expires_in', 300)
    return redirect('http://localhost:3000')

@app.route('/auth/status')
def status():
    return jsonify({'authenticated': 'access_token' in session}), (200 if 'access_token' in session else 401)

@app.route('/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return '', 204

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'access_token' not in session:
            return jsonify({'error': 'unauthorized'}), 401

        if time.time() >= session.get('expires_at', 0):
            refresh = session.get('refresh_token')
            if not refresh:
                return jsonify({'error': 'session expired'}), 401
            resp = requests.post(f"{KEYCLOAK_INTERNAL_URL}/realms/{REALM}/protocol/openid-connect/token", data={
                'grant_type': 'refresh_token',
                'refresh_token': refresh,
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET
            })
            if resp.status_code != 200:
                session.clear()
                return jsonify({'error': 'refresh failed'}), 401
            tokens = resp.json()
            session['access_token'] = tokens['access_token']
            session['refresh_token'] = tokens.get('refresh_token', refresh)
            session['expires_at'] = time.time() + tokens.get('expires_in', 300)
        return f(*args, **kwargs)
    return decorated

@app.route('/api/reports', methods=['GET'])
@require_auth
def get_report():
    access_token = session.get('access_token')
    if not access_token:
        return jsonify({'error': 'unauthorized'}), 401

    print(f"DEBUG: Token: {access_token}...")
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    try:
        resp = requests.get(f"{BACKEND_API_URL}/reports", headers=headers)
        print(f"DEBUG: Reports API responded with status {resp.status_code}")
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Report service unavailable: {str(e)}'}), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=True)