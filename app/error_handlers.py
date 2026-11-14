
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


logger = logging.getLogger(__name__)


def error_response(
    status_code: int,
    code: str,
    message: str,
):
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
            },
        },
    )


def register_exception_handlers(app: FastAPI):

    # Erros HTTP gerados pelas rotas
    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ):
        error_codes = {
            400: "BAD_REQUEST",
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            409: "CONFLICT",
            413: "PAYLOAD_TOO_LARGE",
            422: "VALIDATION_ERROR",
            500: "INTERNAL_SERVER_ERROR",
        }

        code = error_codes.get(
            exc.status_code,
            "HTTP_ERROR",
        )

        message = (
            exc.detail
            if isinstance(exc.detail, str)
            else "The request could not be processed"
        )

        return error_response(
            exc.status_code,
            code,
            message,
        )

    # Erros de validação dos parâmetros e dados recebidos
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        logger.warning(
            "Request validation failed: %s",
            exc.errors(),
        )

        return error_response(
            422,
            "VALIDATION_ERROR",
            "The request contains invalid or missing data",
        )

    # Erros de integridade do banco de dados
    @app.exception_handler(IntegrityError)
    async def integrity_exception_handler(
        request: Request,
        exc: IntegrityError,
    ):
        logger.exception(
            "Database integrity constraint violated"
        )

        return error_response(
            409,
            "DATA_INTEGRITY_ERROR",
            "The operation conflicts with existing data",
        )

    # Outros erros relacionados ao banco de dados
    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(
        request: Request,
        exc: SQLAlchemyError,
    ):
        logger.exception("Database operation failed")

        return error_response(
            500,
            "DATABASE_ERROR",
            "A database operation could not be completed",
        )

    # Qualquer erro inesperado
    @app.exception_handler(Exception)
    async def unexpected_exception_handler(
        request: Request,
        exc: Exception,
    ):
        logger.exception("Unexpected application error")

        return error_response(
            500,
            "INTERNAL_SERVER_ERROR",
            "An unexpected error occurred",
        )