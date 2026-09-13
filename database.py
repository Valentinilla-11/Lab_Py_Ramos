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
    total_price = Column(Float, nullable=False)

    product = relationship("Product", back_populates="sales")

# Creá las tablas que estén definidas en Base si todavía no existen
Base.metadata.create_all(engine, Base.metadata.tables.values(), checkfirst=True)
