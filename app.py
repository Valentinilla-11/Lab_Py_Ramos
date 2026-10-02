from fastapi import FastAPI, HTTPException, status
from database import Product, Sale, CartProduct, Cart, db_session
from schema import (ProductCreate, ProductResponse, ProductListResponse, SingleProductResponse, SaleCreate, SaleResponse, SingleSaleResponse, 
                    CartCreate, CartResponse, SaleListResponse, SingleCartResponse, CartListResponse, SaleCartUpdate, CartProductAdd, CartUpdate)
from utils import calculate_cart_total

app = FastAPI()

@app.get("/") # Decorador
def root():
    return {"message": "API working"}

# ==========================================================
# Product
# ==========================================================

@app.post("/products", response_model=SingleProductResponse, status_code=status.HTTP_201_CREATED) # "response_model" es una palabra reservada de FastAPI. 
def create_product(product: ProductCreate):                                           # Toma el return y le pone el filtro que le pasas despues del "="
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
def get_products():
    try:
        products = Product.query.all()
        response = {"products": products}
        return response
    
    except Exception as e: # Si ocurre algún error durante la consulta a la base de datos o el armado de la respuesta, lo atrapa en la variable e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An error ocurred while trying to get product: {e}")


@app.get("/products/{product_id}", response_model=SingleProductResponse, status_code=status.HTTP_200_OK)
def get_product(product_id: int):
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
def update_product(product_id: int, product: ProductCreate):
    try:
        existing_product = Product.query.get(product_id)

        if not existing_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        # Sobrescribir directamente todos los campos recibidos
        existing_product.name = product.name
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
def delete_product(product_id):
    try:
        product = Product.query.get(product_id)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )

        # Impedir eliminar si ya está dentro de algún carrito
        in_cart = CartProduct.query.filter_by(product_id=product_id).first()
        if in_cart:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete product because it is currently inside a cart"
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

# ==========================================================
# Cart 
# ==========================================================

#! FALTAN MAS ENDPOINTS

@app.post("/carts/{cart_id}/products", response_model=SingleCartResponse, status_code=status.HTTP_200_OK)
def add_product_to_cart(cart_id: int, item_data: CartProductAdd):
    try:
        cart = Cart.query.get(cart_id)
        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

        product = Product.query.get(item_data.product_id)
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        # Si el producto ya está en el carrito, sumamos la cantidad
        existing_item = CartProduct.query.filter_by(cart_id=cart_id, product_id=item_data.product_id).first()
        if existing_item:
            existing_item.quantity += item_data.quantity
        else:
            new_item = CartProduct(
                cart_id=cart_id,
                product_id=item_data.product_id,
                quantity=item_data.quantity
            )
            db_session.add(new_item)

        db_session.commit()
        db_session.refresh(cart)
        return {"cart": cart}

    except HTTPException:
        raise
    except Exception as e:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while adding product to cart: {e}"
        )


@app.delete("/carts/{cart_id}/products/{product_id}", response_model=SingleCartResponse, status_code=status.HTTP_200_OK)
def remove_product_from_cart(cart_id: int, product_id: int):
    try:
        cart = Cart.query.get(cart_id)
        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

        item = CartProduct.query.filter_by(cart_id=cart_id, product_id=product_id).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found in this cart")

        db_session.delete(item)
        db_session.commit()
        db_session.refresh(cart)

        return {"cart": cart}

    except HTTPException:
        raise
    except Exception as e:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while removing product from cart: {e}"
        )


@app.post("/carts", response_model=SingleCartResponse, status_code=status.HTTP_201_CREATED)
def create_cart(cart_data: CartCreate):
    try:
        new_cart = Cart(
            creation_date=cart_data.creation_date,
            status=cart_data.status
        )
        db_session.add(new_cart)
        db_session.commit()
        db_session.refresh(new_cart)

        return {"cart": new_cart}
    
    except Exception as e:
        db_session.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while trying to create cart: {e}"
        )


@app.get("/carts", response_model=CartListResponse, status_code=status.HTTP_200_OK)
def get_carts():
    try:
        carts = Cart.query.all()
        return {"carts": carts}
    
    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while trying to get carts: {e}"
        )


@app.get("/carts/{cart_id}", response_model=SingleCartResponse, status_code=status.HTTP_200_OK)
def get_cart_by_id(cart_id: int):
    try:
        cart = Cart.query.get(cart_id)

        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found"
            ) 

        return {"cart": cart}

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while trying to get cart: {e}"
        )


@app.put("/carts/{cart_id}", response_model=SingleCartResponse, status_code=status.HTTP_200_OK)
def update_cart(cart_id: int, payload: CartUpdate):
    try:
        cart = Cart.query.get(cart_id)

        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found"
            )

        # Regla de negocio: Un carrito asociado a una venta no puede ser modificado
        if cart.sale is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A cart associated with a sale cannot be modified"
            )

        # Actualizamos solo los campos que fueron enviados en el body
        if payload.creation_date is not None:
            cart.creation_date = payload.creation_date

        if payload.status is not None:
            cart.status = payload.status

        db_session.commit()
        db_session.refresh(cart)

        return {"cart": cart}

    except HTTPException:
        raise

    except Exception as e:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the cart: {e}"
        )


@app.delete("/carts/{cart_id}", status_code=status.HTTP_200_OK)
def delete_cart(cart_id: int):
    try:
        cart = Cart.query.get(cart_id)
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Cart not found")

        if cart.sale:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete a cart that is associated with a sale")

        deleted_cart_data = CartResponse.model_validate(cart)

        db_session.delete(cart)
        db_session.commit()

        return {
            "message": "Cart deleted successfully",
            "cart": deleted_cart_data
        }

    except HTTPException:
        raise

    except Exception as e:
        db_session.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while trying to delete cart: {e}"
        )

# ==========================================================
# Sale
# ==========================================================

@app.post("/sales", response_model=SingleSaleResponse, status_code=status.HTTP_201_CREATED)
def create_sale(sale_data: SaleCreate):
    try:
        cart = Cart.query.get(sale_data.cart_id)

        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

        # Regla de negocio: Solo se permite asociar a una venta un carrito cerrado
        if cart.status != "cerrado":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign an open cart to a sale. Close the cart first."
            )

        # Verificar que el carrito no esté asignado a otra venta (Relación 1 a 1)
        existing_sale = Sale.query.filter_by(cart_id=sale_data.cart_id).first()

        if existing_sale:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This cart is already assigned to another sale"
            )

        # Calculamos el total con los precios actuales antes de guardar la venta
        total = calculate_cart_total(cart)

        sale = Sale(
            date=sale_data.date,
            time=sale_data.time,
            cart_id=sale_data.cart_id,
            total_price=total  # Guardamos el total en la base de datos
        )

        db_session.add(sale)
        db_session.commit()
        db_session.refresh(sale)

        return {"sale": sale}

    except HTTPException:
        raise
    except Exception as e:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while trying to create sale: {e}"
        )


@app.get("/sales", response_model=SaleListResponse, status_code=status.HTTP_200_OK)
def get_sales():
    try:

        sales = Sale.query.all()
        response = {"sales": sales}
        return response;
    
    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while trying to get sales: {e}"
        )

   
@app.get("/sale/{sale_id}", response_model=SingleSaleResponse, status_code=status.HTTP_200_OK)
def get_sale(sale_id: int):
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


@app.post("/sales/{sale_id}/cart", response_model=SingleSaleResponse, status_code=status.HTTP_200_OK)
def update_sale_cart(sale_id: int, payload: SaleCartUpdate): 
    try:
        sale = Sale.query.get(sale_id)

        if not sale:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sale not found")

        cart = Cart.query.get(payload.cart_id)

        if not cart:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

        # Regla de negocio: Solo se permite asociar a una venta un carrito cuyo estado sea "cerrado"
        if cart.status != "cerrado":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only closed carts can be assigned to a sale"
            )

        # Verificar que el carrito no esté asociado a otra venta diferente
        existing_sale = Sale.query.filter_by(cart_id=payload.cart_id).first()

        # Si ya está asociado a esta misma venta (existing_sale.id == sale_id), no genera error.
        if existing_sale and existing_sale.id != sale_id: 
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This cart is already associated with another sale"
            )

        # Actualizamos la relación del carrito
        sale.cart_id = payload.cart_id
        
        # Recalculamos y congelamos el nuevo total de la venta en la BD
        sale.total_price = calculate_cart_total(cart)

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
            detail=f"An error occurred while updating sale's cart: {e}"
        )


@app.put("/sales/{sale_id}", response_model=SingleSaleResponse, status_code=status.HTTP_200_OK)
def update_sale(sale_id: int, sale_data: SaleCreate):
    try: 
        existing_sale = Sale.query.get(sale_id)

        if not existing_sale:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sale not found"
            )

        # Verificar que el carrito enviado exista
        cart = Cart.query.get(sale_data.cart_id)
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found"
            )

        # Regla de negocio: El carrito debe estar en estado "cerrado"
        if cart.status != "cerrado":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only closed carts can be assigned to a sale"
            )

        # Verificar que el carrito no esté asignado a otra venta distinta
        other_sale_with_cart = Sale.query.filter_by(cart_id=sale_data.cart_id).first()

        if other_sale_with_cart and other_sale_with_cart.id != sale_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This cart is already associated with another sale"
            )

        # Actualizar los campos básicos
        existing_sale.date = sale_data.date
        existing_sale.time = sale_data.time

        # Si cambió el carrito (o por consistencia al actualizar), recalculamos el total
        existing_sale.cart_id = sale_data.cart_id
        existing_sale.total_price = calculate_cart_total(cart)

        db_session.commit()
        db_session.refresh(existing_sale)

        return {"sale": existing_sale}

    except HTTPException:
        raise

    except Exception as e:
        db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while trying to update sale: {e}"
        )


@app.delete("/sales/{sale_id}", status_code=status.HTTP_200_OK)
def delete_sale(sale_id: int):
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


