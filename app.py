from fastapi import FastAPI, HTTPException, status
from database import Product, db_session
from schema import ProductCreate, ProductResponse

app = FastAPI()

@app.get("/")
def root():
    return {"message": "API working"}

@app.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate):

    new_product = Product(
        name=product.name,
        price=product.price
    )

    db_session.add(new_product)
    db_session.commit()
    db_session.refresh(new_product) # Hace que new_product se actualice con los datos que generó la base de datos, especialmente el id

    return new_product


@app.get("/products", status_code=status.HTTP_200_OK)
async def get_products():
    try:
        products = Product.query.all()
        response = {"products": products}
        return response
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An error ocurred while trying to get product: {e}")


@app.get("/products/{product_id}", status_code=status.HTTP_200_OK)
async def get_product(product_id):
    try:
        product = Product.query.get(product_id)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Product not found")

        response = {"product": product}
        return response

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_sERVER_ERROR, 
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

        db_session.delete(product)
        db_session.commit()

        return {"message": "Product deleted successfully"}

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error ocurred while trying to delete product: {e}"
        )


   



