"""
FastAPI REST API for Sales Advisor Service
Provides secure, rate-limited access to sales opportunity analysis
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import defaultdict

from fastapi import FastAPI, HTTPException, Security, Request, status
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from sales_advisor_engine import SalesAdvisorEngine
from models import (
    OpportunityRequest,
    OpportunityResponse,
    ErrorResponse,
    HealthResponse,
    ExtractedAttributes,
    SimilarDeal
)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Sales Advisor API",
    description="AI-powered sales opportunity analysis and recommendation service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - adjust origins as needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key authentication
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Rate limiting configuration
RATE_LIMIT_REQUESTS = 10  # requests per hour
RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds

# In-memory rate limiting store (use Redis in production for multi-instance deployments)
rate_limit_store: Dict[str, list] = defaultdict(list)

# Initialize Sales Advisor Engine (singleton)
engine: Optional[SalesAdvisorEngine] = None


def get_engine() -> SalesAdvisorEngine:
    """Get or initialize the Sales Advisor Engine"""
    global engine
    if engine is None:
        engine = SalesAdvisorEngine(log_level=logging.INFO)
    return engine


def get_valid_api_keys() -> set:
    """Get valid API keys from environment variables"""
    api_keys_str = os.getenv("API_KEYS", "")
    if not api_keys_str:
        raise ValueError("No API keys configured. Set API_KEYS environment variable.")
    return set(key.strip() for key in api_keys_str.split(",") if key.strip())


def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """Verify API key from request header"""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include X-API-Key header in your request.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    try:
        valid_keys = get_valid_api_keys()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key configuration error. Contact administrator."
        )
    
    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key provided.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return api_key


def check_rate_limit(api_key: str) -> None:
    """Check if API key has exceeded rate limit"""
    now = datetime.now()
    
    # Clean up old requests outside the time window
    rate_limit_store[api_key] = [
        req_time for req_time in rate_limit_store[api_key]
        if now - req_time < timedelta(seconds=RATE_LIMIT_WINDOW)
    ]
    
    # Check if limit exceeded
    if len(rate_limit_store[api_key]) >= RATE_LIMIT_REQUESTS:
        oldest_request = min(rate_limit_store[api_key])
        reset_time = oldest_request + timedelta(seconds=RATE_LIMIT_WINDOW)
        wait_seconds = int((reset_time - now).total_seconds())
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. You can analyze {RATE_LIMIT_REQUESTS} opportunities per hour. "
                   f"Please wait {wait_seconds} seconds before trying again.",
            headers={
                "X-RateLimit-Limit": str(RATE_LIMIT_REQUESTS),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(reset_time.timestamp())),
                "Retry-After": str(wait_seconds)
            }
        )
    
    # Record this request
    rate_limit_store[api_key].append(now)


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - redirect to docs"""
    return {
        "message": "Sales Advisor API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health_check": "/health"
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check endpoint"
)
async def health_check():
    """
    Check if the service and Azure dependencies are healthy.
    This endpoint does not require authentication.
    """
    try:
        # Try to initialize engine to check Azure connections
        test_engine = get_engine()

        return HealthResponse(
            status="healthy",
            version="1.0.0",
            azure_services={
                "openai": "connected",
                "cognitive_search": "connected"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "version": "1.0.0",
                "error": str(e),
                "azure_services": {
                    "openai": "error",
                    "cognitive_search": "error"
                }
            }
        )


@app.post(
    "/api/v1/analyze",
    response_model=OpportunityResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Server error"}
    },
    tags=["Analysis"],
    summary="Analyze sales opportunity"
)
async def analyze_opportunity(
    request: OpportunityRequest,
    api_key: str = Security(verify_api_key)
):
    """
    Analyze a sales opportunity and get AI-powered recommendations.

    **Authentication**: Requires valid API key in X-API-Key header

    **Rate Limit**: 10 requests per hour per API key

    **Request Body**:
    - `opportunity_description`: Detailed description of your sales opportunity (10-5000 characters)

    **Response**:
    - `success`: Whether analysis succeeded
    - `recommendation`: AI-generated sales strategy recommendation
    - `extracted_attributes`: Key attributes extracted from your description
    - `win_probability_improvements`: Top 3 recommendations to improve win rate
    - `similar_won_deals`: Historical successful deals similar to yours
    - `similar_lost_deals`: Historical failed deals to learn from
    - `statistics`: Relevant statistical insights

    **Example**:
    ```json
    {
      "opportunity_description": "We're pursuing a $50,000 deal with a healthcare company in the Northeast region for our GTX Plus Pro product. The sales rep is John Smith."
    }
    ```
    """
    # Log incoming request body (split into lines to avoid truncation)
    import json as json_lib
    request_body = request.model_dump()
    logging.info("=" * 80)
    logging.info("*** USER REQUEST RECEIVED ***")
    logging.info("=" * 80)

    # Convert to JSON and log line by line to avoid truncation
    request_json = json_lib.dumps(request_body, indent=2, ensure_ascii=False)
    for line in request_json.split('\n'):
        logging.info(line)

    logging.info("=" * 80)
    logging.info("*** END OF USER REQUEST ***")
    logging.info("=" * 80)

    # Check rate limit
    check_rate_limit(api_key)

    try:
        # Get the engine
        sales_engine = get_engine()

        # Analyze the opportunity
        result = sales_engine.analyze_opportunity(request.opportunity_description)

        # Check if analysis failed
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error_message"]
            )

        # Transform the result to match our response model
        response = transform_engine_result(result)

        # Log outgoing response body (split into lines to avoid truncation)
        response_body = response.model_dump()
        logging.info("=" * 80)
        logging.info("*** SENDING RESPONSE BACK TO CALLER ***")
        logging.info("=" * 80)

        # Log recommendation separately first (since it's large)
        recommendation_text = response_body.get("recommendation", "")
        logging.info("")
        logging.info("RECOMMENDATION (Complete):")
        logging.info("-" * 80)
        # Log recommendation line by line
        for line in recommendation_text.split('\n'):
            logging.info(line)
        logging.info("-" * 80)
        logging.info("")

        # Log the rest of the response (without recommendation to avoid duplication)
        response_summary = {
            "success": response_body.get("success"),
            "extracted_attributes": response_body.get("extracted_attributes"),
            "similar_won_deals_count": len(response_body.get("similar_won_deals", [])),
            "similar_lost_deals_count": len(response_body.get("similar_lost_deals", [])),
            "recommendation_length": len(recommendation_text)
        }

        logging.info("RESPONSE SUMMARY:")
        logging.info("-" * 80)
        # Convert to JSON and log line by line to avoid truncation
        summary_json = json_lib.dumps(response_summary, indent=2, ensure_ascii=False)
        for line in summary_json.split('\n'):
            logging.info(line)
        logging.info("-" * 80)

        logging.info("=" * 80)
        logging.info("*** END OF USER RESPONSE ***")
        logging.info("=" * 80)

        return response

    except HTTPException as http_exc:
        # Log HTTP exception response (split into lines to avoid truncation)
        error_response = {
            "status_code": http_exc.status_code,
            "detail": http_exc.detail
        }
        logging.info("=" * 80)
        logging.info("📤 OUTGOING API ERROR RESPONSE (HTTP Exception)")
        logging.info("=" * 80)
        logging.info("ERROR RESPONSE BODY (Complete):")

        # Convert to JSON and log line by line to avoid truncation
        error_json = json_lib.dumps(error_response, indent=2, ensure_ascii=False)
        for line in error_json.split('\n'):
            logging.info(line)

        logging.info("=" * 80)
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error
        logging.error(f"Error analyzing opportunity: {str(e)}", exc_info=True)

        # Log exception response (split into lines to avoid truncation)
        exception_response = {
            "status_code": 500,
            "detail": f"An error occurred during analysis: {str(e)}",
            "error_type": type(e).__name__
        }
        logging.info("=" * 80)
        logging.info("📤 OUTGOING API ERROR RESPONSE (Exception)")
        logging.info("=" * 80)
        logging.info("ERROR RESPONSE BODY (Complete):")

        # Convert to JSON and log line by line to avoid truncation
        exception_json = json_lib.dumps(exception_response, indent=2, ensure_ascii=False)
        for line in exception_json.split('\n'):
            logging.info(line)

        logging.info("=" * 80)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during analysis: {str(e)}"
        )


def transform_engine_result(result: dict) -> OpportunityResponse:
    """
    Transform SalesAdvisorEngine result to API response model.

    Handles missing metrics gracefully - if product/sector/region not found,
    the engine returns top alternatives instead of crashing.
    """
    try:
        # Extract attributes - use .get() to handle missing keys gracefully
        extracted_attrs_data = result.get("extracted_attributes", {})
        extracted_attrs = ExtractedAttributes(
            product=extracted_attrs_data.get("product"),
            sector=extracted_attrs_data.get("sector"),
            region=extracted_attrs_data.get("region"),
            current_rep=extracted_attrs_data.get("current_rep"),
            sales_price=extracted_attrs_data.get("sales_price"),
            expected_revenue=extracted_attrs_data.get("expected_revenue")
        )

        # Similar won deals - handle missing data gracefully
        similar_won = []
        for deal in result.get("won_matches", []):
            try:
                similar_won.append(
                    SimilarDeal(
                        opportunity_id=deal.get("opportunity_id", ""),
                        product=deal.get("product"),
                        account_sector=deal.get("account_sector"),
                        account_region=deal.get("account_region"),
                        sales_rep=deal.get("sales_rep"),
                        deal_stage=deal.get("deal_stage"),
                        sales_price=deal.get("sales_price"),
                        revenue_from_deal=deal.get("revenue_from_deal"),
                        sales_cycle_duration=deal.get("sales_cycle_duration"),
                        deal_value_ratio=deal.get("deal_value_ratio"),
                        notes=deal.get("Notes", "")[:400] if deal.get("Notes") else None
                    )
                )
            except Exception as e:
                logging.warning(f"Skipping invalid won deal: {e}")
                continue

        # Similar lost deals - handle missing data gracefully
        similar_lost = []
        for deal in result.get("lost_matches", []):
            try:
                similar_lost.append(
                    SimilarDeal(
                        opportunity_id=deal.get("opportunity_id", ""),
                        product=deal.get("product"),
                        account_sector=deal.get("account_sector"),
                        account_region=deal.get("account_region"),
                        sales_rep=deal.get("sales_rep"),
                        deal_stage=deal.get("deal_stage"),
                        sales_price=deal.get("sales_price"),
                        revenue_from_deal=deal.get("revenue_from_deal"),
                        sales_cycle_duration=deal.get("sales_cycle_duration"),
                        deal_value_ratio=deal.get("deal_value_ratio"),
                        notes=deal.get("Notes", "")[:400] if deal.get("Notes") else None
                    )
                )
            except Exception as e:
                logging.warning(f"Skipping invalid lost deal: {e}")
                continue

        return OpportunityResponse(
            success=True,
            recommendation=result.get("recommendation", "No recommendation available"),
            extracted_attributes=extracted_attrs,
            similar_won_deals=similar_won,
            similar_lost_deals=similar_lost
        )

    except Exception as e:
        logging.error(f"Error transforming engine result: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to transform engine result: {str(e)}")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logging.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error_message": "An unexpected error occurred. Please try again later.",
            "error_type": "server"
        }
    )


if __name__ == "__main__":
    import uvicorn

    # For local testing
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

