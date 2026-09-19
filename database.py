from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Time, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session, relationship

# La base de datos va a ser SQLite y el archivo se va a llamar database.db
DATABASE_URL = "sqlite:///./database.db"

# El objeto que permite que SQLAlchemy se comunique con SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Crea un gestor de sesiones único y aislado por cada hilo/petición (Thread-Local)
# para interactuar con la base de datos de forma segura sin conflictos de acceso.
db_session = scoped_session(
    sessionmaker(bind=engine)
)

# Base nos va a servir para que SQLAlchemy sepa cuáles de nuestras clases representan tablas de la base de datos
Base = declarative_base()

# "Agregale a Base una propiedad llamada query que utilice db_session para hacer consultas" y como las clases heredan de base tambien heredan query
Base.query = db_session.query_property()

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)

    sales = relationship("Sale", back_populates="product") # Primer argumento es el nombre de la clase de python 
                                                          # "back_populates" es el nombre del atributo que declare en la otra clase
                                                          # si es una relacion de uno a muchos, en el lado de muchos el nombre va en plural ("sales")

class Sale(Base):
    __tablename__= "sales"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    quantity = Column(Integer, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False) # Clave Foránea


    @property # Es un decorador que hace que una función se pueda usar como si fuera una variable o atributo simple 
              # "mi_total = venta.total_price" y NO "mi_total = venta.total_price()" asi Pydantic puede leerlo para armar el JSON al responder

    def total_price(self) -> float: # Define la función que se ejecutará en segundo plano cuando alguien consulte sale.total_price
        if self.product and self.product.price: # Comprueba que la relación con el producto exista y que este tenga un precio cargado
            return self.product.price * self.quantity
        return 0.0 #Si la validación del if falla, la propiedad retorna 0.0 como valor por defecto.

    # Cuando ejecutas venta1.total_price, self representa a venta1 (mira la cantidad de esa venta y el precio de su producto)
    # self le dice a Python: "usá la cantidad y el producto de esta venta en concreto, no de otra"

    product = relationship("Product", back_populates="sales")

# Creá las tablas que estén definidas en Base si todavía no existen
Base.metadata.create_all(engine, Base.metadata.tables.values(), checkfirst=True)
