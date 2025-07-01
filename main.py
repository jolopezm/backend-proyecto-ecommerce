import os
import json
from fastapi import FastAPI, HTTPException
import httpx
from firebase_admin import credentials, initialize_app, firestore
import firebase_admin
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from routers import users, products, chilexpress
from init_transaction import init_tbk_transaction, commit_tbk_transaction
from typing import List, Dict, Any

load_dotenv()

app = FastAPI()

origins = [
    'http://localhost:5173',
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVICE_ACCOUNT_KEY_PATH = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "../../mi-app-carrito/config/serviceAccountKey.json")

def _load_api_key_from_json_file(file_path: str) -> str | None:
    if not os.path.exists(file_path):
        print(f"Advertencia: Archivo de clave API no encontrado en la ruta '{file_path}'. La clave API no estará disponible.")
        return None
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, dict) and "apiKey" in data:
                return data["apiKey"]
            elif isinstance(data, str): 
                return data
            else:
                print(f"Advertencia: El archivo '{file_path}' no contiene un JSON con la estructura esperada (ej. {{'apiKey': 'clave'}} o una cadena directamente).")
                return None
    except json.JSONDecodeError:
        try:
            with open(file_path, 'r') as f:
                return f.read().strip()
        except Exception as e:
            print(f"Error al leer el archivo '{file_path}' como texto plano: {e}")
            return None
    except Exception as e:
        print(f"Error inesperado al cargar la clave API de '{file_path}': {e}")
        return None

COBERTURAS_KEY_PATH = os.getenv("CHILEXPRESS_COBERTURAS_API_KEY_PATH", "../../mi-app-carrito/config/chilexpress_coberturas_api_key.json")
COTIZACIONES_KEY_PATH = os.getenv("CHILEXPRESS_COTIZACIONES_API_KEY_PATH", "../../mi-app-carrito/config/chilexpress_cotizaciones_api_key.json")
ENVIOS_KEY_PATH = os.getenv("CHILEXPRESS_ENVIOS_API_KEY_PATH", "../../mi-app-carrito/config/chilexpress_envios_api_key.json")

CHILEXPRESS_COBERTURAS_API_KEY = _load_api_key_from_json_file(COBERTURAS_KEY_PATH)
CHILEXPRESS_COTIZACIONES_API_KEY = _load_api_key_from_json_file(COTIZACIONES_KEY_PATH)
CHILEXPRESS_ENVIOS_API_KEY = _load_api_key_from_json_file(ENVIOS_KEY_PATH)

CHILEXPRESS_CONFIG = {
    "COBERTURAS_BASE_URL": 'http://testservices.wschilexpress.com/georeference/api/v1',
    "COTIZACIONES_BASE_URL": 'http://testservices.wschilexpress.com/rating/api/v1',
    "ENVIOS_BASE_URL": 'http://testservices.wschilexpress.com/transport-orders/api/v1',
    "COBERTURAS_API_KEY": CHILEXPRESS_COBERTURAS_API_KEY, # <-- AQUI SE PASA LA CLAVE REAL
    "COTIZACIONES_API_KEY": CHILEXPRESS_COTIZACIONES_API_KEY, # <-- AQUI SE PASA LA CLAVE REAL
    "ENVIOS_API_KEY": CHILEXPRESS_ENVIOS_API_KEY, # <-- AQUI SE PASA LA CLAVE REAL
}

print("Configuración de Chilexpress:")
for key, value in CHILEXPRESS_CONFIG.items():
    if value:
        if "API_KEY" in key and value:
            print(f"{key}: {value[:3]}{'*' * (len(value) - 7)}{value[-4:]}")
        else:
            print(f"{key}: {value}")
    else:
        print(f"{key}: No configurado")


if not os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
    raise FileNotFoundError(
        f"ERROR: El archivo de clave de servicio de Firebase NO se encontró en: {SERVICE_ACCOUNT_KEY_PATH}\n"
        "Asegúrate de descargarlo de la consola de Firebase y colocarlo en la ruta correcta."
    )
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
        initialize_app(cred)
    print("Firebase Admin SDK inicializado.")
except ValueError as e:
    print(f"Advertencia al inicializar Firebase: {e}. Si ya está inicializado, puedes ignorar esto.")
except Exception as e:
    raise Exception(f"Fallo al inicializar Firebase Admin SDK: {e}")

db = firestore.client()

@app.post("/api/init-tx")
async def init_tx(data: dict):
    return await init_tbk_transaction(data)

from init_transaction import FinalizeOrderPayload
from services.chilexpress_api import ChilexpressApiService
from typing import Dict

@app.post("/api/confirm-transaction/{token_str}")
async def confirm_transaction(token_str: str):
    try:
        resp = await commit_tbk_transaction(token_str)
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error al confirmar la transaccion: {e}')

app.include_router(users.router(db=db), prefix="")
app.include_router(products.router(db=db), prefix="")
app.include_router(chilexpress.router(chilexpress_config=CHILEXPRESS_CONFIG, db=db), prefix="") 

@app.get("/")
async def read_root():
    return {"message": "Hello, FastAPI!"}
