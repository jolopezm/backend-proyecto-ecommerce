from fastapi import APIRouter, HTTPException
from firebase_admin import firestore

db_client: firestore.Client = None

def router(db: firestore.Client):
    global db_client
    db_client = db
    router = APIRouter()

    @router.get("/products")
    async def get_products_endpoint():
        try:
            products_ref = db_client.collection('products')
            docs = products_ref.order_by('name').get()

            products_list = []
            for doc in docs:
                product_data = doc.to_dict()
                product_data['id'] = doc.id 
                products_list.append(product_data)
            return products_list
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno del servidor al obtener productos: {str(e)}")

    @router.get("/products/{product_id}")
    async def get_product_endpoint(product_id: str):
        try:
            doc_ref = db_client.collection('productos').document(product_id)
            doc = doc_ref.get()

            if not doc.exists:
                raise HTTPException(status_code=404, detail="Producto no encontrado")

            product_data = doc.to_dict()
            product_data['id'] = doc.id
            return product_data
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error interno del servidor al obtener producto: {str(e)}")

    return router
