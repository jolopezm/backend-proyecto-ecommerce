from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class TransactionBase(BaseModel):
    token: str
    
class TransactionRequestBase(BaseModel):
    buy_order: str
    session_id: str
    amount: int
    return_url: str
    
class ConfirmTransactionRequest(BaseModel):
    token: str
    
class OrderItem(BaseModel):
    id: str
    name: str
    price: float
    quantity: int
    imageUrl: Optional[str] = None 
    
class ShippingAddress(BaseModel):
    alias: Optional[str] = None
    calle: Optional[str] = Field(None, alias="streetName")
    comuna: Optional[str] = Field(None, alias="countyName")
    comuna_cod: Optional[str] = Field(None, alias="countyCode") 
    id: Optional[str] = None
    nro: Optional[int] = Field(None, alias="number") 
    region: Optional[str] = None
    suplemento: Optional[str] = None
    userId: Optional[str] = None

    class Config:
        populate_by_name = True 

class ChilexpressDetail(BaseModel):
    additionalProductDescription: Optional[str] = None
    address: Optional[str] = None
    barcode: Optional[str] = None
    classificationData: Optional[str] = None
    companyName: Optional[str] = None
    createdDate: Optional[str] = None
    deliveryTypeCode: Optional[str] = None
    deliveryZoneId: Optional[int] = None
    destinationCoverageAreaName: Optional[str] = None
    distributionDescription: Optional[str] = None
    genericString1: Optional[str] = None
    genericString2: Optional[str] = None
    groupReference: Optional[str] = None
    labelData: Optional[str] = None 
    labelType: Optional[str] = None
    labelVersion: Optional[str] = None
    printedDate: Optional[str] = None
    productDescription: Optional[str] = None
    recipient: Optional[str] = None
    reference: Optional[str] = None
    serviceDescription: Optional[str] = None
    serviceDescriptionFull: Optional[str] = None
    statusCode: Optional[int] = None
    statusDescription: Optional[str] = None
    transportOrderNumber: Optional[int] = None

class ChilexpressHeader(BaseModel):
    certificateNumber: Optional[int] = None
    countOfGeneratedOrders: Optional[int] = None
    errors: Any = None
    statusCode: Optional[int] = None
    statusDescription: Optional[str] = None

class ChilexpressOptionService(BaseModel):
    required: Optional[bool] = None
    serviceDescription: Optional[str] = None
    serviceTypeCode: Optional[int] = None
    serviceValue: Optional[str] = None

class ChilexpressOption(BaseModel):
    additionalServices: Optional[List[ChilexpressOptionService]] = None
    conditions: Optional[str] = None
    deliveryType: Optional[int] = None
    didUseVolumetricWeight: Optional[bool] = None
    finalWeight: Optional[str] = None
    serviceDescription: Optional[str] = None
    serviceTypeCode: Optional[int] = None
    serviceValue: Optional[str] = None

class ChilexpressResponse(BaseModel):
    data: Optional[Dict[str, Any]] = None 
    header: Optional[ChilexpressHeader] = None 

class ShippingDetails(BaseModel):
    address: Optional[ShippingAddress] = None
    chilexpressResponse: Optional[ChilexpressResponse] = None 
    option: Optional[ChilexpressOption] = None


class TransbankDetails(BaseModel):
    transaction_date: Optional[str] = None 

class Order(BaseModel):
    id: str
    buy_order: Optional[str] = None 
    transaction_date: Optional[str] = None 
    status: Optional[str] = None 
    items: List[OrderItem] 
    totalAmount: float
    currency: Optional[str] = None 

    userId: Optional[str] = None
    userEmail: Optional[str] = None
    userName: Optional[str] = None
    userPhoneNumber: Optional[str] = None 
    
    createdAt: Optional[str] = None 
    updatedAt: Optional[str] = None 
    orderDate: Optional[str] = None 

    shipping: Optional[ShippingDetails] = None 
    notes: Optional[str] = None

