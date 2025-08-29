from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.db.database import engine
from app.db.models import Base
from app.api.product import router as product_router
from app.api.tracking import router as tracking_router

# Create database tables automatically when app starts
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Product API", description="API for managing products", version="1.0.0")

@app.get("/")
def read_root():
    return {"message": "Welcome to Product API"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include API routes
app.include_router(product_router)
app.include_router(tracking_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
