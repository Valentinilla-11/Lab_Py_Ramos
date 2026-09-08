from fastapi import FastAPI, HTTPException, status
from database import Product, db_session
from schema import ProductCreate, ProductResponse, ProductListResponse, SingleProductResponse

app = FastAPI()

@app.get("/") # Decorador
def root():
    return {"message": "API working"}


@app.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED) # "response_model" es una palabra reservada de FastAPI. 
async def create_product(product: ProductCreate):                                           # Toma el return y le pone el filtro que le pasas despues del "="
    try:
        # Verifica si hay un producto con el mismo nombre
        existing = Product.query.filter_by(name=product.name).first() 
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A product with this name already exists"
            )

        new_product = Product(name=product.name, price=product.price)
        db_session.add(new_product)
        db_session.commit()
        db_session.refresh(new_product) # Hace que new_product se actualice con los datos que generó la base de datos, especialmente el id

        return new_product

    except HTTPException:
        raise  

    except Exception as e:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while trying to create product: {e}"
        )


@app.get("/products", response_model=ProductListResponse, status_code=status.HTTP_200_OK)
async def get_products():
    try:
        products = Product.query.all()
        response = {"products": products}
        return response
    
    except Exception as e: # Si ocurre algún error durante la consulta a la base de datos o el armado de la respuesta, lo atrapa en la variable e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An error ocurred while trying to get product: {e}")


@app.get("/products/{product_id}", response_model=SingleProductResponse, status_code=status.HTTP_200_OK)
async def get_product(product_id):
    try:
        product = Product.query.get(product_id)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Product not found")

        response = {"product": product} # Como tenemos un diccionario ademas de devolver el product, hay que usar otro response, el "SingleProductResponse"
        return response

    except HTTPException: # Si se lanzó la HTTPException del 404 (producto no encontrado) dentro del try, la deja pasar 
        raise             # Python evalúa los bloques except en orden, de arriba a abajo, de lo más específico (HTTPException) a lo más general (Exception) 
                          # Si esto no estuviera, se sobreescribiria en el siguiente except a HTTP_500

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An error ocurred while trying to get product: {e}")


@app.put("/products/{product_id}", response_model=ProductResponse, status_code=status.HTTP_200_OK)
async def update_product(product_id: int, product: ProductCreate):
    try:
        existing_product = Product.query.get(product_id)

        if not existing_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        existing_product.name = product.name
        existing_product.price = product.price

        db_session.commit()
        db_session.refresh(existing_product)

        return existing_product

    except HTTPException:
        raise

    except Exception as e:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error ocurred while trying to update product: {e}"
        )


@app.delete("/products/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product(product_id):
    try:
        product = Product.query.get(product_id)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        # Convertimos el objeto SQLAlchemy a Pydantic ANTES de borrarlo
        deleted_product_data = ProductResponse.model_validate(product)

        db_session.delete(product)
        db_session.commit()

        return {
            "message": "Product deleted successfully",
            "product": deleted_product_data
        }

    except HTTPException:
        raise

    except Exception as e:
        db_session.rollback()  # Cancela cualquier operación pendiente en la sesión de la base de datos para dejarla en un estado limpio y seguro tras el fallo

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error ocurred while trying to delete product: {e}"
        )


   



