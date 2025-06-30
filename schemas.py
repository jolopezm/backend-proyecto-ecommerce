from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any # Added Dict and Any for flexibility

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
    imageUrl: Optional[str] = None # Confirmed Optional as per typical product data
    
class ShippingAddress(BaseModel):
    alias: Optional[str] = None
    calle: Optional[str] = Field(None, alias="streetName") # <-- Alias aquí
    comuna: Optional[str] = Field(None, alias="countyName") # <-- Alias aquí
    comuna_cod: Optional[str] = Field(None, alias="countyCode") # <-- Alias aquí
    id: Optional[str] = None
    nro: Optional[int] = Field(None, alias="number") # <-- Alias aquí, y asegúrate que es int
    region: Optional[str] = None
    suplemento: Optional[str] = None
    userId: Optional[str] = None

    class Config:
        populate_by_name = True 

class ChilexpressDetail(BaseModel):
    # Simplified based on provided document for relevant fields
    additionalProductDescription: Optional[str] = None
    address: Optional[str] = None
    barcode: Optional[str] = None
    classificationData: Optional[str] = None
    companyName: Optional[str] = None
    createdDate: Optional[str] = None # Confirmed string in document
    deliveryTypeCode: Optional[str] = None
    deliveryZoneId: Optional[int] = None
    destinationCoverageAreaName: Optional[str] = None
    distributionDescription: Optional[str] = None
    genericString1: Optional[str] = None
    genericString2: Optional[str] = None
    groupReference: Optional[str] = None
    labelData: Optional[str] = None # Example: "<CXP_DATA>..." (large string)
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
    transportOrderNumber: Optional[int] = None # Confirmed number in document

class ChilexpressHeader(BaseModel):
    certificateNumber: Optional[int] = None
    countOfGeneratedOrders: Optional[int] = None
    errors: Any = None # Can be null or other structure
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
    data: Optional[Dict[str, Any]] = None # Chilexpress data can be complex and varied
    # From your document, 'detail' is an array inside 'data'
    # If you want to model it precisely:
    # data: Optional[Dict[str, List[ChilexpressDetail]]] = None
    # Assuming 'data' itself is a map that contains 'detail' and 'header' as per your document
    # For now, using Dict[str, Any] as a flexible container, and then drilling down.
    # A more precise model would be:
    # data: Optional[Dict[str, Any]] # Or a specific model like ChilexpressData
    header: Optional[ChilexpressHeader] = None # Added header
    # If data.detail is List[ChilexpressDetail] and data.header is ChilexpressHeader, consider:
    # data: Optional[Dict[str, Any]] # or a more structured model if you know all keys inside 'data'
    # For example:
    # class ChilexpressDataContent(BaseModel):
    #    detail: Optional[List[ChilexpressDetail]] = None
    #    header: Optional[ChilexpressHeader] = None
    # chilexpressResponse: Optional[ChilexpressDataContent] = None # in Shipping

class ShippingDetails(BaseModel):
    address: Optional[ShippingAddress] = None
    chilexpressResponse: Optional[ChilexpressResponse] = None # This is a top-level map in your document
    option: Optional[ChilexpressOption] = None # Added option based on document


class TransbankDetails(BaseModel):
    # Based on your document, transbank fields are directly in Order, not nested in a separate TransbankDetails map
    # But if your JS 'transbank' object has more fields, you might need this.
    # For now, I'll keep the TransbankDetails model as it was from previous context,
    # but the `transaction_date` itself is what was causing the issue.
    #response_code: Optional[int] = None # Not seen in your provided doc for transbank
    #amount: Optional[int] = None # Not seen in your provided doc for transbank
    transaction_date: Optional[str] = None # <-- CRITICAL: MUST BE Optional[str] here too
    # Add other Transbank fields that you might store (e.g., buy_order, amount if they are also nested)


class Order(BaseModel):
    id: str # Document ID
    buy_order: Optional[str] = None # <-- CRITICAL: Made Optional[str]
    transaction_date: Optional[str] = None # <-- CRITICAL: Made Optional[str] (from Transbank)
    status: Optional[str] = None # <-- CRITICAL: Made Optional[str]
    items: List[OrderItem] # Assuming items list will always be present (can be empty)
    totalAmount: float # Assuming totalAmount is always present as a float
    currency: Optional[str] = None # <-- CRITICAL: Made Optional[str]

    userId: Optional[str] = None
    userEmail: Optional[str] = None
    userName: Optional[str] = None
    userPhoneNumber: Optional[str] = None # Added based on your JS createOrder function
    
    createdAt: Optional[str] = None # <-- CRITICAL: Made Optional[str]
    updatedAt: Optional[str] = None # <-- CRITICAL: Made Optional[str]
    orderDate: Optional[str] = None # <--- CRITICAL: Made Optional[str]

    # Nested fields as per your document
    shipping: Optional[ShippingDetails] = None # Using the new ShippingDetails model
    # paymentDetails: Optional[PaymentDetails] = None # Not explicitly seen in your document's top level,
                                                  # but keeping if you use it elsewhere.
    # shippingCost: Optional[float] = None # This seems to be part of shipping.option.serviceValue / totalAmount
    notes: Optional[str] = None

