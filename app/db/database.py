from sqlmodel import create_engine, SQLModel, Session


# Chaîne de connexion Azure SQL
from urllib.parse import quote_plus

DATABASE_URL = (
    "mssql+pyodbc://CloudSAe6b1e60b:" +
    quote_plus("KaRa1035*") +
    "@calcul-enr.database.windows.net:1433/data_calculatrice"
    "?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no"
)

engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    return Session(engine)
