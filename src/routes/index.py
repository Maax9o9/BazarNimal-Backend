"""Montaje de todas las rutas bajo /api/v1 (orden: auth, adopciones, tienda, publicaciones)."""

from fastapi import APIRouter

from src.features.adoptions.admin.routes.adoptions_admin_routes import routers as adoptions_admin_routers
from src.features.adoptions.user.routes.adoptions_user_routes import routers as adoptions_user_routers
from src.features.auth.routes.auth_routes import router as auth_router
from src.features.posts.admin.routes.posts_admin_routes import router as posts_admin_router
from src.features.posts.user.routes.posts_user_routes import router as posts_user_router
from src.features.products.admin.routes.products_admin_routes import router as products_admin_router
from src.features.products.user.routes.products_user_routes import router as products_user_router

API_PREFIX = "/api/v1"


def build_api_router() -> APIRouter:
    api = APIRouter(prefix=API_PREFIX)
    routers = [
        auth_router,
        *adoptions_user_routers,
        *adoptions_admin_routers,
        products_user_router,
        products_admin_router,
        posts_user_router,
        posts_admin_router,
    ]
    for router in routers:
        api.include_router(router)
    return api
