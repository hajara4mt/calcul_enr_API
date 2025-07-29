from fastapi import FastAPI
from app.routes import input_routes 
from app.routes import output_routes  
from app.routes import projets_utilisateur  
from app.routes import maj_routes  
from app.routes import list_projets
from app.routes import suppression_projet
from app.routes import suppression_utilisateur


app = FastAPI()

# on prend les routes qu'on a défini dans notre dossier routes
app.include_router(input_routes.router)
app.include_router(output_routes.router)  

app.include_router(projets_utilisateur.router)
app.include_router(maj_routes.router)
app.include_router(list_projets.router)
app.include_router(suppression_projet.router)
app.include_router(suppression_utilisateur.router)



# Endpoint 
@app.get("/")
def root():
    return {"message": "API FastAPI en ligne "}


