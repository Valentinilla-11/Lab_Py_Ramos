from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

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
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)


# Creá las tablas que estén definidas en Base si todavía no existen
Base.metadata.create_all(bind=engine)

