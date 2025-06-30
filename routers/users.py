from fastapi import APIRouter, HTTPException, Query, Body
from firebase_admin import firestore
from datetime import datetime
from typing import Optional, List, Dict, Any
# Assuming your Order schema is defined here and it now includes orderDate
from schemas import Order 
# Import the specific Firestore Timestamp type for robust checking
try:
    from google.cloud.firestore_v1.base_client import DatetimeWithNanoseconds
except ImportError:
    # Fallback if the specific type is not found, will rely on hasattr(field_value, 'isoformat') or datetime check
    DatetimeWithNanoseconds = type(None) # Set to a dummy type if not available

db_client: firestore.Client = None

def router(db: firestore.Client):
    global db_client
    db_client = db
    router = APIRouter()

    @router.get("/users")
    async def get_users_endpoint():
        """
        Retrieves a list of all users from the 'users' collection, ordered by userName.
        """
        try:
            user_ref = db_client.collection('users')
            docs = user_ref.order_by('userName').get()

            user_list = []
            for doc in docs:
                user_data = doc.to_dict()
                user_data['id'] = doc.id
                user_list.append(user_data)
            return user_list
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno del servidor al obtener usuarios: {str(e)}")

    @router.get("/user/{user_id}")
    async def get_user_endpoint(user_id: str):
        """
        Retrieves a single user by their userId from the 'users' collection.
        """
        try:
            doc_ref = db_client.collection('users')
            query = doc_ref.where('userId', '==', user_id)
            docs_stream = query.stream()

            found_user = None
            for d in docs_stream:
                found_user = d
                break
            
            if not found_user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")

            user_data = found_user.to_dict()
            user_data['id'] = found_user.id
            return user_data
        except HTTPException as http_exc:
            raise http_exc
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno del servidor al obtener usuario: {str(e)}")
        
    @router.get("/addresses/{user_id}")
    async def get_addresses_by_user_id_endpoint(user_id: str):
        """
        Retrieves all addresses associated with a given user ID from the 'addresses' collection.
        """
        try:
            addresses_ref = db_client.collection('addresses')
            query_stream = addresses_ref.where('userId', '==', user_id).stream()
            
            addresses_list = []
            for doc in query_stream:
                address_data = doc.to_dict()
                address_data['id'] = doc.id
                addresses_list.append(address_data)
            
            return addresses_list 
        except Exception as e:
            print(f"Error al obtener direcciones para el usuario {user_id} desde Firestore: {e}")
            raise HTTPException(status_code=500, detail=f"Error interno del servidor al obtener Direcciones: {str(e)}")

    @router.get("/orders", response_model=List[Order])
    async def get_user_orders_endpoint(user_id: Optional[str] = Query(None, description="Filtra órdenes por ID de usuario")):
        """
        Retrieves orders, optionally filtered by user ID, and converts Firestore Timestamps to ISO 8601 strings.
        """
        orders_ref = db_client.collection('orders')
        query_ref = orders_ref.order_by("createdAt", direction=firestore.Query.DESCENDING)

        if user_id:
            query_ref = query_ref.where("userId", "==", user_id)

        try:
            docs = query_ref.stream()
            orders_list = []
            for doc in docs:
                order_data = doc.to_dict()
                order_data['id'] = doc.id
                
                # Helper function to convert to ISO 8601 if it's a Firestore Timestamp or Python datetime object
                def to_isoformat_if_timestamp(field_value: Any) -> Optional[str]:
                    print(f"DEBUG: to_isoformat_if_timestamp received value: '{field_value}' (Type: {type(field_value)})")
                    if field_value is None:
                        return None # Explicitly return None if value is None
                    
                    # Handle Firestore Timestamp type (DatetimeWithNanoseconds) specifically
                    if isinstance(field_value, DatetimeWithNanoseconds):
                        try:
                            # DatetimeWithNanoseconds objects have .isoformat() directly
                            return field_value.isoformat() 
                        except Exception as e:
                            print(f"Advertencia: No se pudo convertir DatetimeWithNanoseconds '{field_value}' a ISO format: {e}")
                            return None # Return None if conversion fails
                    
                    # Handle generic Python datetime objects
                    elif isinstance(field_value, datetime):
                        try:
                            return field_value.isoformat()
                        except Exception as e:
                            print(f"Advertencia: No se pudo convertir Python datetime '{field_value}' a ISO format: {e}")
                            return None # Return None if conversion fails
                    
                    # If it's already a string, return it as is
                    elif isinstance(field_value, str):
                        return field_value
                    
                    # Fallback for any other unexpected type: return None.
                    print(f"Advertencia: Tipo de dato inesperado para fecha: {type(field_value)}. Valor: '{field_value}'. Retornando None.")
                    return None


                # --- CRITICAL FIX: Apply conversion to TOP-LEVEL 'transaction_date' ---
                order_data['transaction_date'] = to_isoformat_if_timestamp(order_data.get('transaction_date'))
                print(f"DEBUG: Top-level transaction_date. Raw: '{order_data.get('transaction_date')}' (Type: {type(order_data.get('transaction_date'))}). Converted: '{order_data['transaction_date']}' (Type: {type(order_data['transaction_date'])})")


                # Apply the conversion to other relevant top-level date fields
                order_data['createdAt'] = to_isoformat_if_timestamp(order_data.get('createdAt'))
                order_data['updatedAt'] = to_isoformat_if_timestamp(order_data.get('updatedAt'))
                order_data['orderDate'] = to_isoformat_if_timestamp(order_data.get('orderDate'))

                # Handle potentially nested transbank.transaction_date (if it exists)
                # This handles cases where 'transbank' might be a separate map containing transaction_date
                # (though your provided document shows transaction_date at top-level)
                if 'transbank' in order_data and isinstance(order_data['transbank'], dict):
                    raw_nested_transaction_date = order_data['transbank'].get('transaction_date')
                    converted_nested_transaction_date = to_isoformat_if_timestamp(raw_nested_transaction_date)
                    order_data['transbank']['transaction_date'] = converted_nested_transaction_date
                    print(f"DEBUG: Nested transbank.transaction_date. Raw: '{raw_nested_transaction_date}' (Type: {type(raw_nested_transaction_date)}). Converted: '{converted_nested_transaction_date}' (Type: {type(converted_nested_transaction_date)})")
                else:
                    # Ensure 'transbank' and its 'transaction_date' are structured correctly
                    if 'transbank' not in order_data:
                        order_data['transbank'] = {} # Initialize if missing
                    order_data['transbank']['transaction_date'] = None # Explicitly set to None
                    print(f"DEBUG: 'transbank' key missing or not a dict for order {order_data.get('id')}. Setting nested transaction_date to None.")
                
                orders_list.append(order_data)

            return orders_list
        except Exception as e:
            print(f"Error al obtener órdenes desde Firestore: {e}")
            raise HTTPException(status_code=500, detail=f"Error interno del servidor al obtener las órdenes: {e}")

    @router.post("/create-test-order", status_code=201)
    async def create_test_order_endpoint(order_data: Order = Body(...)):
        """
        Creates a test order in Firestore.
        """
        orders_ref = db_client.collection('orders')
        
        # Convert string dates from Pydantic model back to datetime objects for Firestore storage
        def to_datetime_for_firestore(field_value: Optional[str]):
            if isinstance(field_value, str):
                try:
                    return datetime.fromisoformat(field_value)
                except ValueError:
                    print(f"Advertencia: String de fecha malformado '{field_value}'. Usando datetime.now().")
                    return datetime.now()
            return datetime.now() # Default if None or not a string

        # Create a dictionary from the Pydantic model for Firestore insertion
        order_dict = order_data.dict(exclude_unset=True)
        order_dict.pop('id', None) # Remove 'id' as it's generated by Firestore

        # Convert top-level date fields
        order_dict['createdAt'] = to_datetime_for_firestore(order_dict.get('createdAt'))
        order_dict['updatedAt'] = to_datetime_for_firestore(order_dict.get('updatedAt'))
        order_dict['transaction_date'] = to_datetime_for_firestore(order_dict.get('transaction_date')) # <--- TOP-LEVEL transaction_date conversion for saving


        # orderDate can be genuinely None if not provided
        if 'orderDate' in order_dict and isinstance(order_dict['orderDate'], str):
            try:
                order_dict['orderDate'] = datetime.fromisoformat(order_dict['orderDate'])
            except ValueError:
                print(f"Advertencia: String de orderDate malformado '{order_dict['orderDate']}'. Estableciendo a None.")
                order_dict['orderDate'] = None
        elif 'orderDate' in order_dict and order_dict['orderDate'] is None:
            pass # Keep it None
        else:
            order_dict['orderDate'] = None # Explicitly set to None if not provided or unexpected type


        # Handle nested transbank.transaction_date conversion for storage (if it exists)
        if 'transbank' in order_dict and isinstance(order_dict['transbank'], dict):
            if 'transaction_date' in order_dict['transbank'] and isinstance(order_dict['transbank']['transaction_date'], str):
                try:
                    order_dict['transbank']['transaction_date'] = datetime.fromisoformat(order_dict['transbank']['transaction_date'])
                except ValueError:
                    print(f"Advertencia: String de transbank.transaction_date malformado '{order_dict['transbank']['transaction_date']}'. Estableciendo a None.")
                    order_dict['transbank']['transaction_date'] = None
            elif 'transaction_date' in order_dict['transbank'] and order_dict['transbank']['transaction_date'] is None:
                pass # Keep it None
            else:
                order_dict['transbank']['transaction_date'] = None # If present but not str/None, set to None
        elif 'transbank' in order_dict and not isinstance(order_dict['transbank'], dict):
             order_dict['transbank'] = {'transaction_date': None} # Handle non-dict transbank
        else: # If 'transbank' itself is missing, set it up with transaction_date as None
            order_dict['transbank'] = {'transaction_date': None}


        try:
            doc_ref = await orders_ref.add(order_dict)
            return {"message": "Orden de prueba creada exitosamente", "order_id": doc_ref[1].id if isinstance(doc_ref, tuple) else doc_ref.id}
        except Exception as e:
            print(f"Error al crear la orden de prueba en Firestore: {e}")
            raise HTTPException(status_code=500, detail=f"Error interno del servidor al crear la orden de prueba: {e}")

    return router
