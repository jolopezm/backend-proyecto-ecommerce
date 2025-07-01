import datetime
from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.integration_type import IntegrationType
from transbank.common.options import WebpayOptions
from fastapi import HTTPException
from firebase_admin import firestore
from pydantic import BaseModel
from typing import List, Dict, Any
from services.chilexpress_api import ChilexpressApiService


class OrderItem(BaseModel):
    id: str
    name: str
    quantity: int
    price: float


class ShippingInfo(BaseModel):
    address: Dict[str, Any]
    option: Dict[str, Any]


class UserInfo(BaseModel):
    uid: str
    email: str
    name: str
    phoneNumber: str | None = None


class FinalizeOrderPayload(BaseModel):
    items: List[OrderItem]
    shipping_info: ShippingInfo
    user_info: UserInfo


commerce_code = '597055555532'
api_key = '579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C'
global_webpay_options = WebpayOptions(commerce_code, api_key, IntegrationType.TEST)
tbk_transaction = Transaction(global_webpay_options)


async def init_tbk_transaction(data: dict):
    buy_order = data['buy_order']
    session_id = data['session_id']
    amount = data['amount']
    return_url = data['return_url']

    try:
        resp = tbk_transaction.create(buy_order, session_id, amount, return_url)

        if isinstance(resp, dict):
            if 'error_message' in resp:
                raise HTTPException(status_code=400, detail=f"Error de Transbank: {resp.get('error_message')}")
            if 'url' in resp and 'token' in resp:
                return {"url": resp['url'], "token": resp['token']}
            else:
                raise HTTPException(status_code=500, detail=f"Respuesta inesperada de Transbank: {resp}")
        else:
            return {"url": resp.url, "token": resp.token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def commit_tbk_transaction(token: str):
    try:
        tbk_response = tbk_transaction.commit(token)
        is_dict = isinstance(tbk_response, dict)
        response_code = tbk_response['response_code'] if is_dict else tbk_response.response_code
        status = tbk_response['status'] if is_dict else tbk_response.status

        if response_code != 0:
            return {"response_code": response_code, "status": status, "message": "Pago rechazado."}
        else:
            if is_dict:
                return tbk_response
            else:
                return {
                    "vci": tbk_response.vci,
                    "amount": tbk_response.amount,
                    "status": tbk_response.status,
                    "buy_order": tbk_response.buy_order,
                    "session_id": tbk_response.session_id,
                    "card_detail": tbk_response.card_detail,
                    "accounting_date": tbk_response.accounting_date,
                    "transaction_date": str(tbk_response.transaction_date),
                    "authorization_code": tbk_response.authorization_code,
                    "payment_type_code": tbk_response.payment_type_code,
                    "response_code": tbk_response.response_code,
                    "installments_amount": tbk_response.installments_amount,
                    "installments_number": tbk_response.installments_number,
                    "balance": tbk_response.balance
                }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f'Error al procesar la confirmación de Transbank: {e}')



