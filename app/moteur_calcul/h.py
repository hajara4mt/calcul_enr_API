import pyodbc

conn = pyodbc.connect(
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=calcul-enr.database.windows.net;"
    "DATABASE=data_calculatrice;"
    "UID=CloudSAe6b1e60b;"
    "PWD=KaRa1035*;"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
)
cursor = conn.cursor()
cursor.execute("SELECT GETDATE()")
print(cursor.fetchone())
