"""Swagger/OpenAPI documentation configuration for Ani API."""

from flasgger import Swagger


def init_swagger(app):
    """Initialize Swagger documentation.
    
    Args:
        app: Flask application instance.
    """
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/docs",
    }

    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Ani AI Assistant API",
            "description": "A smart, context-aware AI chatbot API for showcasing developer projects and handling inquiries.",
            "contact": {
                "name": "Cid Kageno",
                "url": "https://github.com/cid-kageno-dev",
                "email": "cidkageno105@gmail.com",
            },
            "version": "1.0.0",
        },
        "basePath": "/",
        "schemes": ["http", "https"],
        "securityDefinitions": {
            "api_key": {
                "type": "apiKey",
                "name": "X-API-Key",
                "in": "header",
            }
        },
    }

    swagger = Swagger(
        app,
        config=swagger_config,
        template=swagger_template,
    )

    return swagger


# API Documentation for each endpoint

HEALTH_SPEC = {
    "tags": ["System"],
    "summary": "Health check endpoint",
    "description": "Check if the API is running and ready to handle requests.",
    "responses": {
        "200": {
            "description": "API is healthy",
            "schema": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "example": "ok",
                        "description": "Health status",
                    },
                    "version": {
                        "type": "string",
                        "example": "1.0.0",
                        "description": "API version",
                    },
                    "ai_ready": {
                        "type": "boolean",
                        "example": True,
                        "description": "Is AI service ready",
                    },
                    "db_ready": {
                        "type": "boolean",
                        "example": True,
                        "description": "Is database ready",
                    },
                },
            },
        }
    },
}

CHAT_SPEC = {
    "tags": ["Chat"],
    "summary": "Send a message to Ani",
    "description": "Send a message and receive an AI-generated response from Ani.",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "example": "Tell me about your creator",
                        "description": "User message to Ani",
                    }
                },
                "required": ["message"],
            },
        }
    ],
    "responses": {
        "200": {
            "description": "Successful response from Ani",
            "schema": {
                "type": "object",
                "properties": {
                    "user_query": {"type": "string", "example": "Tell me about your creator"},
                    "ai_response": {"type": "string", "example": "I'm Ani, created by Cid Kageno..."},
                    "source": {"type": "string", "example": "AI Response"},
                    "timestamp": {"type": "string", "example": "2026-05-17T12:34:56Z"},
                },
            },
        },
        "400": {
            "description": "Invalid request (missing or empty message)",
            "schema": {
                "type": "object",
                "properties": {
                    "error": {"type": "string"},
                },
            },
        },
        "500": {
            "description": "Server error or AI service unavailable",
        },
    },
}

GITHUB_SPEC = {
    "tags": ["GitHub"],
    "summary": "Get GitHub user information",
    "description": "Fetch real-time GitHub profile data and repositories for the configured user.",
    "responses": {
        "200": {
            "description": "Successfully retrieved GitHub data",
            "schema": {
                "type": "object",
                "properties": {
                    "username": {"type": "string", "example": "cid-kageno-dev"},
                    "bio": {"type": "string", "example": "Developer & AI Enthusiast"},
                    "repositories": {"type": "integer", "example": 12},
                    "followers": {"type": "integer", "example": 45},
                    "public_repos": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "url": {"type": "string"},
                                "stars": {"type": "integer"},
                            },
                        },
                    },
                    "cached": {"type": "boolean"},
                    "cache_expires_in": {"type": "integer", "description": "Seconds until cache expires"},
                },
            },
        },
        "404": {"description": "GitHub user not found"},
        "500": {"description": "Server error"},
    },
}

CACHE_STATUS_SPEC = {
    "tags": ["Cache"],
    "summary": "Get cache status",
    "description": "Check the current status of all cached data.",
    "responses": {
        "200": {
            "description": "Cache status retrieved",
            "schema": {
                "type": "object",
                "properties": {
                    "github": {
                        "type": "object",
                        "properties": {
                            "cached": {"type": "boolean"},
                            "expires_in": {"type": "integer"},
                        },
                    },
                },
            },
        }
    },
}

CACHE_CLEAR_SPEC = {
    "tags": ["Cache"],
    "summary": "Clear cache",
    "description": "Clear all cached data or specific cache entries.",
    "responses": {
        "200": {
            "description": "Cache cleared successfully",
            "schema": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "example": "Cache cleared"},
                },
            },
        }
    },
}

HISTORY_SPEC = {
    "tags": ["History"],
    "summary": "Get chat history",
    "description": "Retrieve past chat interactions (requires database configuration).",
    "parameters": [
        {
            "name": "limit",
            "in": "query",
            "type": "integer",
            "default": 10,
            "description": "Maximum number of records to return",
        },
        {
            "name": "offset",
            "in": "query",
            "type": "integer",
            "default": 0,
            "description": "Number of records to skip",
        },
    ],
    "responses": {
        "200": {
            "description": "Chat history retrieved",
            "schema": {
                "type": "object",
                "properties": {
                    "total": {"type": "integer"},
                    "limit": {"type": "integer"},
                    "offset": {"type": "integer"},
                    "interactions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "user_query": {"type": "string"},
                                "ai_response": {"type": "string"},
                                "created_at": {"type": "string"},
                            },
                        },
                    },
                },
            },
        },
        "503": {"description": "Database not configured"},
    },
}
