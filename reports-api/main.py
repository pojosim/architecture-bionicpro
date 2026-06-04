import os
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from clickhouse_driver import Client
from jwt import PyJWKClient

app = FastAPI(title="Reports API")

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "clickhouse")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", 9000))
CLICKHOUSE_DB = os.getenv("CLICKHOUSE_DB", "reports_db")
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "clickhouse_user")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "clickhouse_password")
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "reports-realm")

clickhouse_client = Client(
    host=CLICKHOUSE_HOST,
    port=CLICKHOUSE_PORT,
    user=CLICKHOUSE_USER,
    password=CLICKHOUSE_PASSWORD,
    database=CLICKHOUSE_DB,
)

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    print(f"DEBUG: Received token: {token}")
    try:
        jwks_client = PyJWKClient(f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/certs")
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(token, signing_key.key, algorithms=["RS256"], audience="reports-frontend")
        return payload
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports")
async def get_report(user: dict = Depends(get_current_user)):
    print("DEBUG: Full payload:", user)
    sensor_user_id = user.get("sensor_user_id")
    if sensor_user_id is None:
        raise HTTPException(status_code=400, detail="Missing sensor_user_id")
    try:
        user_id_int = int(sensor_user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid sensor_user_id format")

    query = """
            SELECT
                date,
                total_signals,
                avg_amplitude,
                avg_frequency,
                avg_duration,
                customer_name,
                customer_email,
                customer_country
            FROM daily_user_metrics
            WHERE user_id = %(user_id)s
            ORDER BY date DESC
                LIMIT 30 \
            """
    try:
        rows = clickhouse_client.execute(query, {"user_id": user_id_int})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    result = []
    for row in rows:
        result.append({
            "date": row[0].isoformat(),
            "total_signals": row[1],
            "avg_amplitude": float(row[2]) if row[2] is not None else None,
            "avg_frequency": row[3],
            "avg_duration": row[4],
            "customer": {
                "name": row[5],
                "email": row[6],
                "country": row[7]
            }
        })
    return {
        "user_id": user_id_int,
        "report": result,
        "data_up_to": (datetime.now() - timedelta(hours=1)).isoformat()
    }