from fastapi import APIRouter, HTTPException, Query, Depends, Body
from services.chilexpress_api import ChilexpressApiService
from typing import Dict, Any, List
from schemas import ShippingAddress
from firebase_admin import firestore
from init_transaction import FinalizeOrderPayload, OrderItem, ShippingInfo, UserInfo
import datetime

chilexpress_service: ChilexpressApiService = None

def router(chilexpress_config: Dict, db: firestore.Client): 
    global chilexpress_service
    if chilexpress_service is None:
        chilexpress_service = ChilexpressApiService(chilexpress_config)

    router = APIRouter()

    @router.get("/regiones")
    async def get_regiones_endpoint():
        return await chilexpress_service.get_regions()

    @router.get("/comunas/{region_id}")
    async def get_comunas_endpoint(region_id: str):
        return await chilexpress_service.get_coverage_areas(region_code=region_id, type=1)

    @router.post("/chilexpress/streets/search")
    async def search_chilexpress_streets_endpoint(search_body: Dict):
        county_name = search_body.get("countyName")
        street_name = search_body.get("streetName", "")
        if not county_name:
            raise HTTPException(status_code=400, detail="countyName es requerido para buscar calles.")
        return await chilexpress_service.search_streets(county_name=county_name, street_name=street_name)

    @router.get("/chilexpress/numeraciones/{street_id}/{nro}")
    async def get_chilexpress_numeraciones_endpoint(street_id: int, nro: int):
        return await chilexpress_service.get_street_numbers(street_id=street_id, street_number=nro)

    @router.post("/chilexpress/georeferencia")
    async def georeference_chilexpress_endpoint(address: ShippingAddress):
        address_dict = address.dict(by_alias=True, exclude_unset=True)
        
        return await chilexpress_service.georeference_address(address_data=address_dict)

    @router.get("/chilexpress/oficinas-de-entrega/{region_id}/{commune_name}")
    async def get_oficinas_de_entrega_endpoint(region_id: str, commune_name: str):
        return await chilexpress_service.get_delivery_offices(region_code=region_id, county_name=commune_name)

    @router.post("/chilexpress/cotizar-envio")
    async def cotizar_envio_endpoint(cotizacion_body: Dict):
        return await chilexpress_service.quote_shipping(quote_body=cotizacion_body)

    @router.post("/chilexpress/crear-envio")
    async def crear_envio_endpoint(envio_body: Dict):
        return await chilexpress_service.create_shipping(shipping_body=envio_body)

    @router.post("/chilexpress/tracking")
    async def consulta_envio_endpoint(consult_body: Dict):
        return await chilexpress_service.track_shipping(tracking_body=consult_body)

    @router.post("/chilexpress/process-order-and-shipping")
    async def process_order_and_shipping_endpoint(
        payload: FinalizeOrderPayload,
        transbank_response: Dict[str, Any],
        db: firestore.Client = Depends(lambda: db) 
    ):
        try:
            shipping_address = payload.shipping_info.address
            shipping_option = payload.shipping_info.option
            user_info = payload.user_info
            buy_order_id = transbank_response['buy_order']
            total_value = sum(item.price * item.quantity for item in payload.items)

            shipment_body = {
                "header": {
                    "customerCardNumber": "18578680",
                    "countyOfOriginCoverageCode": "STGO",
                    "labelType": 1,
                    "marketplaceRut": "96756430",
                    "sellerRut": "DEFAULT"
                },
                "details": [{
                    "addresses": [
                        {
                            "addressId": 0,
                            "countyCoverageCode": shipping_address.get("comuna_cod"),
                            "streetName": shipping_address.get("calle"),
                            "streetNumber": shipping_address.get("nro"),
                            "supplement": shipping_address.get("suplemento", ""),
                            "addressType": "DEST",
                            "deliveryOnCommercialOffice": False,
                            "commercialOfficeId": None,
                            "observation": "DEFAULT"
                        },
                        {
                            "addressId": 0,
                            "countyCoverageCode": "STGO",
                            "streetName": "SAN ALFONSO",
                            "streetNumber": 100,
                            "supplement": "Oficina 101",
                            "addressType": "DEV",
                            "deliveryOnCommercialOffice": False,
                            "commercialOfficeId": None,
                            "observation": "DEFAULT"
                        }
                    ],
                    "contacts": [
                        {
                            "name": "Tu Tienda E-commerce", # Nombre fijo para el remitente
                            "phoneNumber": "223824861", # Teléfono del ejemplo
                            "mail": "cestevez@chilexpress.cl", # Email del ejemplo
                            "contactType": "R"
                        },
                        {
                            "name": user_info.name,
                            "phoneNumber": user_info.phoneNumber if user_info.phoneNumber else "999999999",
                            "mail": user_info.email,
                            "contactType": "D"
                        }
                    ],
                    "packages": [{
                        "weight": "1", # Valor del ejemplo
                        "height": "1", # Valor del ejemplo
                        "width": "1", # Valor del ejemplo
                        "length": "1", # Valor del ejemplo
                        "serviceDeliveryCode": str(shipping_option.get("serviceTypeCode")),
                        "productCode": str(shipping_option.get("productCode", 3)),
                        "deliveryReference": f"ORDEN-{buy_order_id}",
                        "groupReference": "GRUPO", # Valor del ejemplo
                        "declaredValue": str(round(total_value)),
                        "declaredContent": "5", # Valor del ejemplo
                        "receivableAmountInDelivery": 0
                    }]
                }]
            }

            chilexpress_response = await chilexpress_service.create_shipping(shipment_body)
            print(f"DEBUG: Raw Chilexpress create_shipping response: {chilexpress_response}")

            transport_order_number = None
            reference_number = None

            if chilexpress_response and "data" in chilexpress_response:
                if "detail" in chilexpress_response["data"] and isinstance(chilexpress_response["data"]["detail"], list) and len(chilexpress_response["data"]["detail"]) > 0:
                    first_detail = chilexpress_response["data"]["detail"][0]
                    transport_order_number = first_detail.get("transportOrderNumber")
                    reference_number = first_detail.get("reference")
                
                if "data" not in chilexpress_response:
                    chilexpress_response["data"] = {}
                if "detail" not in chilexpress_response["data"]:
                    chilexpress_response["data"]["detail"] = [{}]

                if chilexpress_response["data"]["detail"] and len(chilexpress_response["data"]["detail"]) > 0:
                    chilexpress_response["data"]["detail"][0]["transportOrderNumber"] = transport_order_number
                    chilexpress_response["data"]["detail"][0]["reference"] = reference_number
            
            print(f"DEBUG: Extracted transport_order_number: {transport_order_number}, reference_number: {reference_number}")
            print(f"DEBUG: chilexpress_response after setting values: {chilexpress_response}")


            order_ref = db.collection('orders').document()
            transaction = db.transaction()

            @firestore.transactional
            def full_process(trans):
                product_updates = {}
                for item in payload.items:
                    product_ref = db.collection('products').document(item.id)
                    snapshot = product_ref.get(transaction=trans)
                    if not snapshot.exists: raise ValueError(f"Producto {item.id} no encontrado.")
                    current_stock = snapshot.to_dict().get('stock', 0)
                    if current_stock < item.quantity: raise ValueError(f"Stock insuficiente para {item.name}.")
                    product_updates[item.id] = current_stock - item.quantity

                for product_id, new_stock in product_updates.items():
                    trans.update(db.collection('products').document(product_id), {'stock': new_stock})


                card_detail = transbank_response['card_detail']
                final_order_data = {
                    "userId": user_info.uid,
                    "userEmail": user_info.email,
                    "userName": user_info.name,
                    "userPhoneNumber": user_info.phoneNumber,
                    "items": [item.dict() for item in payload.items],
                    "totalAmount": total_value,
                    "status": "paid_and_shipping_created",
                    "createdAt": firestore.SERVER_TIMESTAMP,
                    "shipping_info": payload.shipping_info.dict(),
                    "shipping": {
                        "chilexpressResponse": chilexpress_response
                    },
                    "transbank_details": {
                        "buy_order": buy_order_id,
                        "card_number": card_detail.get('card_number'),
                        "transaction_date": str(transbank_response['transaction_date']),
                    }
                }
                trans.set(order_ref, final_order_data)
                return final_order_data


            final_order = full_process(transaction)

            serializable_order = final_order.copy()
            serializable_order["createdAt"] = datetime.datetime.now(datetime.timezone.utc).isoformat()


            return {
                "success": True,
                "order_id": order_ref.id,
                "tracking_number": str(transport_order_number) if transport_order_number else None,
                "order_details": serializable_order
            }


        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f'Error al procesar la orden y envío: {e}')

    return router

