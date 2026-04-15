# app/core/config.py
try:
    from fastapi import FastAPI, APIRouter, HTTPException # type: ignore
    from pydantic import BaseModel # type: ignore
    FASTAPI_AVAILABLE = True
except ModuleNotFoundError:
    FASTAPI_AVAILABLE = False
    
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        def dict(self):
            return self.__dict__

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail
            super().__init__(f"{status_code}: {detail}")

    class APIRouter:
        def __init__(self, *args, **kwargs):
            pass
        def post(self, _path: str, **kwargs):
            def decorator(func):
                return func
            return decorator
        def get(self, _path: str, **kwargs):
            def decorator(func):
                return func
            return decorator

    class FastAPI:
        def __init__(self, title: str = "App", **kwargs):
            self.title = title

        def post(self, _path: str, **kwargs):
            def decorator(func):
                return func
            return decorator

        def get(self, _path: str, **kwargs):
            def decorator(func):
                return func
            return decorator
            
        def include_router(self, router, prefix="", tags=None):
            pass
