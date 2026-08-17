from fastapi import FastAPI

from app.routers.auth import router as auth_router
from app.routers.test import router as test_router
from app.routers.products import router as products_router
from app.routers.cart import router as cart_router
from app.routers.orders import router as orders_router

app = FastAPI(
    title="Smart E-Commerce API",
    version="1.0.0"
)


app.include_router(auth_router)
app.include_router(test_router)
app.include_router(products_router)
app.include_router(cart_router)
app.include_router(orders_router)

@app.get("/")
def root():
    return {
        "message": "Smart E-Commerce API is running"
    }