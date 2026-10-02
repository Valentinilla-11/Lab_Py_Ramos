from pydantic import BaseModel
from typing import List, Optional
from datetime import date, time

# ==========================================================
# Product
# ==========================================================

class ProductCreate(BaseModel):
    name: str
    price: float

    class Config:
        from_attributes = True # Esto creo que es opcional ya que recibe directamente un JSON 

class ProductResponse(BaseModel):
    id: int
    name: str
    price: float

    class Config:
        from_attributes = True # Permite que Pydantic lea los datos directamente desde objetos de SQLAlchemy (usando objeto.nombre) y no solo desde diccionarios o JSON

class ProductListResponse(BaseModel):
    products: List[ProductResponse] # Cada elemento dentro de la lista debe cumplir y ordenarse según el molde ProductResponse

class SingleProductResponse(BaseModel):
    product: ProductResponse # Indica que dentro de "product" viene un objeto con forma de ProductResponse

# ==========================================================
# Cart / CartProduct
# ==========================================================

class CartCreate(BaseModel):
    creation_date: date
    status: str = "abierto"  # Por defecto el estado inicial es "abierto"

    class Config:
        from_attributes = True

# POST /carritos/{id}/productos
class CartProductAdd(BaseModel):
    product_id: int
    quantity: int


class CartUpdate(BaseModel):
    creation_date: Optional[date] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True

# Representación de un producto DENTRO de la lista del carrito en la respuesta JSON de CartResponse 
class CartProductResponse(BaseModel):
    id: int
    product: ProductResponse  # Mapea la relación 'product' en CartProduct
    quantity: int

    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    id: int
    creation_date: date
    status: str
    products: List[CartProductResponse] = []  # Mapea 'products' en tu clase Cart

    class Config:
        from_attributes = True

class SingleCartResponse(BaseModel):
    cart: CartResponse

class CartListResponse(BaseModel):
    carts: List[CartResponse]

# ==========================================================
# Sale
# ==========================================================

class SaleCreate(BaseModel):
    date: date
    time: time
    cart_id: int

    class Config:
        from_attributes = True

# Para el endpoint POST /ventas/{id}/carrito 
class SaleCartUpdate(BaseModel):
    cart_id: int

class SaleResponse(BaseModel):
    id: int
    date: date
    time: time
    total_price: float  # Lee directo el valor float persistido en la BD
    cart: Optional[CartResponse] = None  # Mapea la relación 'cart' de la clase Sale

    class Config:
        from_attributes = True

class SingleSaleResponse(BaseModel):
    sale: SaleResponse

class SaleListResponse(BaseModel):
    sales: List[SaleResponse]



