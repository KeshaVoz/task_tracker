import logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.exceptions.base import AppServiceException


logger = logging.getLogger("app.exceptions")


async def fastapi_validation_exception_handler(request: Request, exc: RequestValidationError | ValidationError):
    raw_errors = exc.errors()
    if not raw_errors:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"message": "Validation error"}
        )
    
    first_error = raw_errors[0]
    
    if isinstance(first_error, dict):
        error_msg = first_error.get("msg", "Validation error")
        loc_data = first_error.get("loc", [])
    else:
        error_msg = getattr(first_error, "msg", "Validation error")
        loc_data = getattr(first_error, "loc", [])
        
    error_msg = str(error_msg).replace("Value error, ", "")
    field = "->".join([str(x) for x in loc_data if str(x) != "body"])
    
    user_id = getattr(request.state, "user_id", "Anonymous")
    
    logger.warning(
        "Validation failed | User: %s | Route: %s %s | Field: [%s] | Error: %s",
        user_id, request.method, request.url.path, field, error_msg
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"message": error_msg}
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if isinstance(exc.detail, dict) and "message" in exc.detail:
        message = exc.detail["message"]
    else:
        message = str(exc.detail)
        
    user_id = getattr(request.state, "user_id", "Anonymous")
    
    if exc.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
        logger.warning(
            "Security/Auth exception | User: %s | Route: %s %s | Status: %s | Msg: %s",
            user_id, request.method, request.url.path, exc.status_code, message
        )
    else:
        logger.info(
            "HTTP exception | User: %s | Route: %s %s | Status: %s | Msg: %s",
            user_id, request.method, request.url.path, exc.status_code, message
        )
    
    return JSONResponse(
        status_code=exc.status_code, 
        content={"message": message}
    )


async def app_service_exception_handler(request: Request, exc: AppServiceException):
    user_id = getattr(request.state, "user_id", "Anonymous")
    
    logger.warning(
        "Business logic exception | User: %s | Route: %s %s | Status: %s | Msg: %s",
        user_id, request.method, request.url.path, exc.status_code, exc.message
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.message}
    )


async def global_unhandled_exception_handler(request: Request, exc: Exception):
    user_id = getattr(request.state, "user_id", "Anonymous")
    
    logger.error(
        "CRITICAL UNHANDLED EXCEPTION | User: %s | Route: %s %s",
        user_id, request.method, request.url.path,
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "Internal server error. Our team is already on it!"}
    )


def register_auth_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, fastapi_validation_exception_handler)
    app.add_exception_handler(ValidationError, fastapi_validation_exception_handler) 
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(AppServiceException, app_service_exception_handler)
    app.add_exception_handler(Exception, global_unhandled_exception_handler)
