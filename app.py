from fastapi import FastAPI, HTTPException, status
from database import Product, Sale, db_session
from schema import ProductCreate, ProductResponse, ProductListResponse, SingleProductResponse, SaleCreate, SaleResponse, SingleSaleResponse, SaleListResponse, SaleUpdate, ProductUpdate

app = FastAPI()

@app.get("/") # Decorador
async def root():
    return {"message": "API working"}


@app.post("/products", response_model=SingleProductResponse, status_code=status.HTTP_201_CREATED) # "response_model" es una palabra reservada de FastAPI. 
async def create_product(product: ProductCreate):                                           # Toma el return y le pone el filtro que le pasas despues del "="
    try:
        # Verifica si hay un producto con el mismo nombre
        existing = Product.query.filter_by(name=product.name).first() 
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A product with this name already exists"
            )

        new_product = Product(
            name=product.name, 
            price=product.price
        )

        db_session.add(new_product)
        db_session.commit()
        db_session.refresh(new_product) # Hace que new_product se actualice con los datos que generó la base de datos, especialmente el id

        response = {"product": new_product} 
        return response

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

@app.put("/products/{product_id}", response_model=SingleProductResponse, status_code=status.HTTP_200_OK)
async def update_product(product_id: int, product: ProductUpdate):
    try:
        existing_product = Product.query.get(product_id)

        if not existing_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        # Solo actualizar los campos que no vienen nulos
        if product.name is not None:
            existing_product.name = product.name

        if product.price is not None:
            existing_product.price = product.price

        db_session.commit()
        db_session.refresh(existing_product)

        response = {"product": existing_product}
        return response

    except HTTPException:
        raise

    except Exception as e:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while trying to update product: {e}"
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


@app.post("/sales", response_model=SingleSaleResponse, status_code=status.HTTP_201_CREATED)
async def create_sale(sale_data: SaleCreate):
    try:
        product = Product.query.get(sale_data.product_id)

        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product does not exist")

        sale = Sale(
            date=sale_data.date,
            time=sale_data.time,
            quantity=sale_data.quantity,
            product_id=sale_data.product_id,
            total_price=(product.price * sale_data.quantity)
        )

        db_session.add(sale)
        db_session.commit()
        db_session.refresh(sale)

        response = {"sale": sale}
        return response

    except HTTPException:
        raise

    except Exception as e:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An error occurred while trying to create sale: {e}")    


@app.get("/sales", response_model=SaleListResponse, status_code=status.HTTP_200_OK)
async def get_sales():
    try:

        sales = Sale.query.all()
        response = {"sales": sales}
        return response;

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error ocurred while trying to get sale: {e}")

        
@app.get("/sale/{sale_id}", response_model=SingleSaleResponse, status_code=status.HTTP_200_OK)
async def get_sale(sale_id):
    try:

        sale = Sale.query.get(sale_id)

        if not sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sale not found")

        response = {"sale": sale}

        return response

    except HTTPException:
         raise

    except Exception as e:
         raise HTTPException(
             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
             detail=f"An error ocurred while trying to get sale: {e}")


@app.put("/sales/{sale_id}", response_model=SingleSaleResponse, status_code=status.HTTP_200_OK)
async def update_sale(sale_id: int, sale: SaleUpdate):
    try: 
        existing_sale = Sale.query.get(sale_id)

        if not existing_sale: # Buscar la venta existente
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sale not found"
            )

        if sale.product_id is not None: # Si se envió un nuevo product_id, verificar que el producto exista
            product = Product.query.get(sale.product_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )
            existing_sale.product_id = product.id 

        if sale.quantity is not None: # Si se envió una nueva cantidad, actualizarla
            existing_sale.quantity = sale.quantity

        current_product = Product.query.get(existing_sale.product_id) # Recalcular el total_price 
        existing_sale.total_price = (current_product.price * existing_sale.quantity)

        db_session.commit()
        db_session.refresh(existing_sale)

        response = {"sale": existing_sale}
        return response

    except HTTPException:
        raise

    except Exception as e:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while trying to update sale: {e}")
        

@app.delete("/sales/{sale_id}", status_code=status.HTTP_200_OK)
async def delete_sale(sale_id):
    try: 
        sale = Sale.query.get(sale_id)

        if not sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sale not found"
            )

        deleted_sale_data = SaleResponse.model_validate(sale)

        db_session.delete(sale)
        db_session.commit()

        return {
            "message": "Sale deleted successfully",
            "sale": deleted_sale_data
        }

    except HTTPException:
        raise

    except Exception as e:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error ocurred while trying to delete sale: {e}"
        )


