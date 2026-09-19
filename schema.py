from pydantic import BaseModel
from typing import List, Optional
from datetime import date, time

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


class SaleCreate(BaseModel):
    date: date
    time: time
    quantity: int
    product_id: int

    class Config:
        from_attributes = True

class SaleResponse(BaseModel):
    id: int
    date: date
    time: time
    quantity: int
    product: ProductResponse
    total_price: float

    class Config:
        from_attributes = True

class SingleSaleResponse(BaseModel):
    sale: SaleResponse

class SaleListResponse(BaseModel):
    sales: List[SaleResponse]



