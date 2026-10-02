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

    # Relación hacia la tabla intermedia
    cart_products = relationship("CartProduct", back_populates="product")    # Primer argumento es el nombre de la clase de python 
                                                                             # "back_populates" es el nombre del atributo que declare en la otra clase
                                                                       

class CartProduct(Base): # Tabla intermedia que representa a "carrito_producto". Mapea la relacion N:M y almacena la cantidad

    __tablename__ = "cart_products"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)            # La gestiona la Base de Datos (SQL)
    cart_id = Column(Integer, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False) # ondelete="CASCADE" -> Si se elimina el registro padre, se borran automáticamente todos los registros hijos asociados a él
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)

    # Relaciones de navegación
    cart = relationship("Cart", back_populates="products")
    product = relationship("Product", back_populates="cart_products")


class Cart(Base):
    __tablename__ = "carts"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    creation_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default="abierto") # 'abierto' o 'cerrado'

    # Un carrito contiene muchos productos con sus cantidades                                   # La gestiona Python (SQLAlchemy)
    products = relationship("CartProduct", back_populates="cart", cascade="all, delete-orphan") # cascade(...) -> todas las acciones como eliminar carrito se propagan a sus items
                                                                                                # sin esto al eliminar un carrito, el producto sigue en cartProduct pero con cart_id = NULL
    # Relación 1 a 1 con la venta (uselist=False indica que es objeto único, no lista)
    sale = relationship("Sale", back_populates="cart", uselist=False) #Por defecto, SQLAlchemy asume relaciones de uno-a-muchos (1:N), por eso hay que aclarar cuando no es (1:1)


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    # Campo para almacenar el precio histórico congelado al momento de crear/asignar
    total_price = Column(Float, nullable=False, default=0.0)
    
    # Clave foránea única hacia la tabla carts (Relación 1 a 1)
    cart_id = Column(Integer, ForeignKey("carts.id"), unique=True, nullable=False)

    # Relación inversa hacia el carrito
    cart = relationship("Cart", back_populates="sale")

# Creá las tablas que estén definidas en Base si todavía no existen
Base.metadata.create_all(engine, Base.metadata.tables.values(), checkfirst=True)
