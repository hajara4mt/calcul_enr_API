from sqlmodel import create_engine, SQLModel, Session
import logging
# Chaîne de connexion Azure SQL
from urllib.parse import quote_plus

logging.basicConfig(level=logging.INFO)  # affiche warnings et erreurs
logger = logging.getLogger("sqlalchemy.engine")


DATABASE_URL = (
    "mssql+pyodbc://CloudSAe6b1e60b:" +
    quote_plus("KaRa1035*") +
    "@calcul-enr.database.windows.net:1433/data_calculatrice"
    "?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no"
)

engine = create_engine(DATABASE_URL,
                        echo=False ,
                        pool_pre_ping=True,     # Vérifie les connexions avant usage
    pool_recycle=1800,
     pool_size=10   )

def get_session():
    return Session(engine)
