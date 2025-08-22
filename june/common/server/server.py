from starlette.applications import Starlette
from starlette.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from starlette.requests import Request
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.gzip import GZipMiddleware
from common.types import (
    A2ARequest,
    JSONRPCResponse,
    InvalidRequestError,
    JSONParseError,
    GetTaskRequest,
    CancelTaskRequest,
    SendTaskRequest,
    SetTaskPushNotificationRequest,
    GetTaskPushNotificationRequest,
    InternalError,
    AgentCard,
    TaskResubscriptionRequest,
    SendTaskStreamingRequest,
)
from pydantic import ValidationError
import json
from typing import AsyncIterable, Any
from common.server.task_manager import TaskManager
from common.utils.security import (
    rate_limiter,
    auth_middleware,
    security_validator,
    audit_logger,
    get_client_id,
    validate_request_size,
    sanitize_user_input,
    SecurityHeaders
)

import logging

logger = logging.getLogger(__name__)


class A2AServer:
    def __init__(
        self,
        host="0.0.0.0",
        port=5000,
        endpoint="/",
        agent_card: AgentCard = None,
        task_manager: TaskManager = None,
        enable_security: bool = True,
        allowed_origins: list = None,
        trusted_hosts: list = None,
    ):
        self.host = host
        self.port = port
        self.endpoint = endpoint
        self.task_manager = task_manager
        self.agent_card = agent_card
        self.enable_security = enable_security
        
        # Security configuration
        if allowed_origins is None:
            allowed_origins = ["http://localhost:3000", "http://localhost:12000"]
        if trusted_hosts is None:
            trusted_hosts = ["localhost", "127.0.0.1", "::1"]
        
        # Create Starlette app with security middleware
        self.app = Starlette()
        
        # Add security middleware
        if self.enable_security:
            self.app.add_middleware(
                Middleware(
                    TrustedHostMiddleware,
                    allowed_hosts=trusted_hosts
                )
            )
            
            self.app.add_middleware(
                Middleware(
                    CORSMiddleware,
                    allow_origins=allowed_origins,
                    allow_credentials=True,
                    allow_methods=["GET", "POST", "PUT", "DELETE"],
                    allow_headers=["*"],
                )
            )
            
            self.app.add_middleware(GZipMiddleware)
        
        # Add routes
        self.app.add_route(self.endpoint, self._process_request, methods=["POST"])
        self.app.add_route(
            "/.well-known/agent.json", self._get_agent_card, methods=["GET"]
        )
        
        # Add security headers middleware
        self.app.add_middleware(
            Middleware(
                SecurityHeadersMiddleware,
                security_headers=SecurityHeaders.get_security_headers()
            )
        )

    def start(self):
        if self.agent_card is None:
            raise ValueError("agent_card is not defined")

        if self.task_manager is None:
            raise ValueError("request_handler is not defined")

        import uvicorn

        uvicorn.run(self.app, host=self.host, port=self.port)

    def _get_agent_card(self, request: Request) -> JSONResponse:
        """Get agent card with security headers"""
        response = JSONResponse(self.agent_card.model_dump(exclude_none=True))
        
        # Add security headers
        if self.enable_security:
            for header, value in SecurityHeaders.get_security_headers().items():
                response.headers[header] = value
        
        return response

    async def _process_request(self, request: Request):
        """Process A2A request with security measures"""
        client_id = get_client_id(request)
        
        # Security checks
        if self.enable_security:
            # Rate limiting
            if not rate_limiter.is_allowed(client_id):
                audit_logger.log_security_event(
                    "RATE_LIMIT_EXCEEDED",
                    "anonymous",
                    {"client_id": client_id, "endpoint": str(request.url)},
                    "WARNING"
                )
                return JSONResponse(
                    {"error": "Rate limit exceeded. Please try again later."},
                    status_code=429
                )
            
            # Request size validation
            if not validate_request_size(request):
                audit_logger.log_security_event(
                    "REQUEST_SIZE_EXCEEDED",
                    "anonymous",
                    {"client_id": client_id, "endpoint": str(request.url)},
                    "WARNING"
                )
                return JSONResponse(
                    {"error": "Request too large"},
                    status_code=413
                )
        
        try:
            body = await request.json()
            
            # Input sanitization
            if self.enable_security:
                body = sanitize_user_input(body)
            
            json_rpc_request = A2ARequest.validate_python(body)

            # Log request for audit
            audit_logger.log_security_event(
                "A2A_REQUEST",
                "anonymous",
                {
                    "client_id": client_id,
                    "request_type": type(json_rpc_request).__name__,
                    "endpoint": str(request.url)
                },
                "INFO"
            )

            if isinstance(json_rpc_request, GetTaskRequest):
                result = await self.task_manager.on_get_task(json_rpc_request)
            elif isinstance(json_rpc_request, SendTaskRequest):
                result = await self.task_manager.on_send_task(json_rpc_request)
            elif isinstance(json_rpc_request, SendTaskStreamingRequest):
                result = await self.task_manager.on_send_task_subscribe(
                    json_rpc_request
                )
            elif isinstance(json_rpc_request, CancelTaskRequest):
                result = await self.task_manager.on_cancel_task(json_rpc_request)
            elif isinstance(json_rpc_request, SetTaskPushNotificationRequest):
                result = await self.task_manager.on_set_task_push_notification(json_rpc_request)
            elif isinstance(json_rpc_request, GetTaskPushNotificationRequest):
                result = await self.task_manager.on_get_task_push_notification(json_rpc_request)
            elif isinstance(json_rpc_request, TaskResubscriptionRequest):
                result = await self.task_manager.on_resubscribe_to_task(
                    json_rpc_request
                )
            else:
                logger.warning(f"Unexpected request type: {type(json_rpc_request)}")
                raise ValueError(f"Unexpected request type: {type(request)}")

            return self._create_response(result)

        except Exception as e:
            # Log security event for errors
            audit_logger.log_security_event(
                "A2A_ERROR",
                "anonymous",
                {
                    "client_id": client_id,
                    "error": str(e),
                    "endpoint": str(request.url)
                },
                "ERROR"
            )
            return self._handle_exception(e)

    def _handle_exception(self, e: Exception) -> JSONResponse:
        if isinstance(e, json.decoder.JSONDecodeError):
            json_rpc_error = JSONParseError()
        elif isinstance(e, ValidationError):
            json_rpc_error = InvalidRequestError(data=json.loads(e.json()))
        else:
            logger.error(f"Unhandled exception: {e}")
            json_rpc_error = InternalError()

        response = JSONResponse(json_rpc_error.model_dump(exclude_none=True), status_code=400)
        
        # Add security headers to error responses
        if self.enable_security:
            for header, value in SecurityHeaders.get_security_headers().items():
                response.headers[header] = value
        
        return response

    def _create_response(self, result: Any) -> JSONResponse | EventSourceResponse:
        if isinstance(result, AsyncIterable):

            async def event_generator(result) -> AsyncIterable[dict[str, str]]:
                async for item in result:
                    yield {"data": item.model_dump_json(exclude_none=True)}

            response = EventSourceResponse(event_generator(result))
            
            # Add security headers to SSE responses
            if self.enable_security:
                for header, value in SecurityHeaders.get_security_headers().items():
                    response.headers[header] = value
            
            return response
        elif isinstance(result, JSONRPCResponse):
            response = JSONResponse(result.model_dump(exclude_none=True))
            
            # Add security headers to JSON responses
            if self.enable_security:
                for header, value in SecurityHeaders.get_security_headers().items():
                    response.headers[header] = value
            
            return response
        else:
            logger.error(f"Unexpected result type: {type(result)}")
            raise ValueError(f"Unexpected result type: {type(result)}")


class SecurityHeadersMiddleware:
    """Middleware to add security headers to all responses"""
    
    def __init__(self, app, security_headers: dict):
        self.app = app
        self.security_headers = security_headers
    
    async def __call__(self, scope, receive, send):
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                # Add security headers to response headers
                if "headers" not in message:
                    message["headers"] = []
                
                for header, value in self.security_headers.items():
                    message["headers"].append(
                        (header.lower().encode(), value.encode())
                    )
            
            await send(message)
        
        await self.app(scope, receive, send_with_headers)
