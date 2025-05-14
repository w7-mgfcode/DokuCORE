import logging
import time
from typing import Callable
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import json

logger = logging.getLogger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging request and response details.
    Also tracks request processing time.
    """
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate a unique request ID (simple implementation)
        request_id = str(int(time.time() * 1000))
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Start timer
        start_time = time.time()
        
        # Log request
        logger.info(f"Request {request_id}: {request.method} {request.url.path}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(f"Response {request_id}: Status {response.status_code}, Time {process_time:.3f}s")
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id
            
            return response
        except Exception as e:
            # Log exception
            logger.error(f"Request {request_id} failed: {str(e)}")
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Create error response
            error_response = Response(
                content=json.dumps({
                    "detail": str(e),
                    "request_id": request_id
                }),
                status_code=500,
                media_type="application/json"
            )
            
            # Add processing time header
            error_response.headers["X-Process-Time"] = str(process_time)
            error_response.headers["X-Request-ID"] = request_id
            
            return error_response


def setup_middleware(app: FastAPI):
    """
    Setup all middleware for the application.
    
    Args:
        app: FastAPI application instance.
    """
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, this should be restricted
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add request logging middleware
    app.add_middleware(RequestLoggingMiddleware)