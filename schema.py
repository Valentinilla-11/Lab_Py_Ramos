from pydantic import BaseModel

class ProductCreate(BaseModel):
    name: str
    price: float

    class Config:
        from_attributes = True # Si te doy una Persona, podés mirar sus propiedades (nombre, edad, ciudad) y llenar la ficha.

class ProductResponse(BaseModel):
    id: int
    name: str
    price: float

    class Config:
        from_attributes = True