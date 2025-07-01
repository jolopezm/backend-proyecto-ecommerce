import httpx
from fastapi import HTTPException
import json
from urllib.parse import urljoin 


class ChilexpressApiService:
    def __init__(self, config: dict):
        self.coberturas_base_url = config.get("COBERTURAS_BASE_URL")
        self.cotizaciones_base_url = config.get("COTIZACIONES_BASE_URL")
        self.envios_base_url = config.get("ENVIOS_BASE_URL")
        
        self.coberturas_api_key = config.get("COBERTURAS_API_KEY")
        self.cotizaciones_api_key = config.get("COTIZACIONES_API_KEY")
        self.envios_api_key = config.get("ENVIOS_API_KEY")

        if not self.coberturas_api_key:
            print("WARNING: COBERTURAS_API_KEY no configurada en ChilexpressApiService.")
        if not self.cotizaciones_api_key:
            print("WARNING: COTIZACIONES_API_KEY no configurada en ChilexpressApiService.")
        if not self.envios_api_key:
            print("WARNING: ENVIOS_API_KEY no configurada en ChilexpressApiService.")

        self.headers_coberturas = {
            "Ocp-Apim-Subscription-Key": self.coberturas_api_key,
            "Content-Type": "application/json"
        }
        self.headers_cotizaciones = {
            "Ocp-Apim-Subscription-Key": self.cotizaciones_api_key,
            "Content-Type": "application/json"
        }
        self.headers_envios = {
            "Ocp-Apim-Subscription-Key": self.envios_api_key,
            "Content-Type": "application/json"
        }

    async def _make_request(self, method: str, url: str, headers: dict, json_data: dict = None, params: dict = None):
        if not headers.get("Ocp-Apim-Subscription-Key"):
            raise HTTPException(
                status_code=500,
                detail="La configuración de la API Key de Chilexpress no está disponible para esta solicitud."
            )

        print(f"\n--- DEBUG: Petición a Chilexpress ---")
        print(f"URL: {method} {url}") # Esta 'url' debe ser la URL ABSOLUTA y completa
        print(f"Headers: {json.dumps(headers, indent=2)}")
        if json_data:
            print(f"JSON Data (Body): {json.dumps(json_data, indent=2)}")
        if params:
            print(f"Params (Query): {json.dumps(params, indent=2)}")
        print(f"-------------------------------------\n")

        try:
            async with httpx.AsyncClient() as client:
                if method == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=json_data)
                else:
                    raise ValueError(f"Método HTTP no soportado: {method}")
                
                response.raise_for_status() 
                return response.json()
        except httpx.HTTPStatusError as e:
            error_response_content = None
            try:
                if 'application/json' in e.response.headers.get('Content-Type', ''):
                    error_response_content = e.response.json()
                else:
                    error_response_content = e.response.text
            except json.JSONDecodeError:
                error_response_content = e.response.text

            print(f"Error HTTP de Chilexpress: {e.response.status_code} - {error_response_content} for URL: {url}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail={"message": "Error en la API de Chilexpress", "chilexpress_error": error_response_content}
            )
        except httpx.RequestError as e:
            print(f"Error de red al conectar con Chilexpress: {e} for URL: {url}")
            raise HTTPException(
                status_code=500,
                detail=f"Error de conexión con la API de Chilexpress: {str(e)}. Asegúrate que la URL sea correcta y accesible."
            )
        except Exception as e:
            print(f"Error inesperado al llamar a la API de Chilexpress: {e} for URL: {url}")
            raise HTTPException(
                status_code=500,
                detail=f"Error interno del servidor al procesar la solicitud: {str(e)}"
            )


    async def get_regions(self):
        full_url = f"{self.coberturas_base_url}/regions"
        return await self._make_request("GET", full_url, self.headers_coberturas)

    async def get_coverage_areas(self, region_code: str, type: int = 1):
        params = {"RegionCode": region_code, "type": type}
        full_url = f"{self.coberturas_base_url}/coverage-areas"
        return await self._make_request("GET", full_url, self.headers_coberturas, params=params)

    async def search_streets(self, county_name: str, street_name: str):
        json_data = {"countyName": county_name, "streetName": street_name}
        full_url = f"{self.coberturas_base_url}/streets/search"
        return await self._make_request("POST", full_url, self.headers_coberturas, json_data=json_data)

    async def get_street_numbers(self, street_id: int, street_number: int):
        full_url = f"{self.coberturas_base_url}/streets/{street_id}/numbers"
        return await self._make_request("GET", full_url, self.headers_coberturas, params={"streetNumber": street_number})

    async def georeference_address(self, address_data: dict):
        full_url = f"{self.coberturas_base_url}/addresses/georeference"
        return await self._make_request("POST", full_url, self.headers_coberturas, json_data=address_data)

    async def get_delivery_offices(self, region_code: str, county_name: str):
        params = {"Type": 0, "RegionCode": region_code, "CountyName": county_name}
        full_url = f"{self.coberturas_base_url}/offices"
        return await self._make_request("GET", full_url, self.headers_coberturas, params=params)

    async def quote_shipping(self, quote_body: dict):
        full_url = f"{self.cotizaciones_base_url}/rates/courier"
        return await self._make_request("POST", full_url, self.headers_cotizaciones, json_data=quote_body)

    async def create_shipping(self, shipping_body: dict):
        full_url = f"{self.envios_base_url}/transport-orders"
        return await self._make_request("POST", full_url, self.headers_envios, json_data=shipping_body)
    
    async def track_shipping(self, tracking_body: dict):
        tracking_body['rut'] = 96756430 
        full_url = urljoin(self.envios_base_url + '/', "tracking") 

        return await self._make_request("POST", full_url, self.headers_envios, json_data=tracking_body)