"""
Pydantic models for FastAPI request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class OpportunityRequest(BaseModel):
    """Request model for opportunity analysis"""
    opportunity_description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Detailed description of the sales opportunity",
        example="We're pursuing a $50,000 deal with a healthcare company in the Northeast region for our GTX Plus Pro product. The sales rep is John Smith."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "opportunity_description": "We're pursuing a $50,000 deal with a healthcare company in the Northeast region for our GTX Plus Pro product. The sales rep is John Smith."
            }
        }


class ExtractedAttributes(BaseModel):
    """Extracted attributes from the opportunity description"""
    product: Optional[str] = Field(None, description="Product name mentioned in the opportunity")
    sector: Optional[str] = Field(None, description="Industry sector of the customer")
    region: Optional[str] = Field(None, description="Geographic region")
    current_rep: Optional[str] = Field(None, description="Sales representative name")
    sales_price: Optional[float] = Field(None, description="Deal price if mentioned")
    expected_revenue: Optional[float] = Field(None, description="Expected revenue if mentioned")


class SimilarDeal(BaseModel):
    """Similar deal from historical data"""
    opportunity_id: str = Field(..., description="Unique identifier for the opportunity")
    product: Optional[str] = Field(None, description="Product name")
    account_sector: Optional[str] = Field(None, description="Customer sector")
    account_region: Optional[str] = Field(None, description="Geographic region")
    sales_rep: Optional[str] = Field(None, description="Sales representative")
    deal_stage: Optional[str] = Field(None, description="Deal outcome: won or lost")
    sales_price: Optional[float] = Field(None, description="Deal price")
    revenue_from_deal: Optional[float] = Field(None, description="Revenue generated")
    sales_cycle_duration: Optional[int] = Field(None, description="Sales cycle length in days")
    deal_value_ratio: Optional[float] = Field(None, description="Deal value ratio metric")
    notes: Optional[str] = Field(None, description="Notes about the deal")


class OpportunityResponse(BaseModel):
    """Response model for successful opportunity analysis"""
    success: bool = Field(True, description="Indicates successful analysis")
    recommendation: str = Field(..., description="AI-generated sales recommendation")
    extracted_attributes: ExtractedAttributes = Field(..., description="Attributes extracted from the description")
    similar_won_deals: List[SimilarDeal] = Field(..., description="Similar successful deals from history")
    similar_lost_deals: List[SimilarDeal] = Field(..., description="Similar failed deals from history")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "recommendation": "Based on analysis of similar deals...",
                "extracted_attributes": {
                    "product": "GTX Plus Pro",
                    "sector": "Healthcare",
                    "region": "Northeast",
                    "current_rep": "John Smith",
                    "sales_price": 50000.0,
                    "expected_revenue": None
                },
                "similar_won_deals": [],
                "similar_lost_deals": []
            }
        }


class ErrorResponse(BaseModel):
    """Response model for errors"""
    success: bool = Field(False, description="Indicates failed analysis")
    error_message: str = Field(..., description="Description of the error")
    error_type: str = Field(..., description="Type of error: validation, authentication, rate_limit, or server")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error_message": "Invalid API key provided",
                "error_type": "authentication"
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Service status: healthy or unhealthy")
    version: str = Field(..., description="API version")
    azure_services: Dict[str, str] = Field(..., description="Status of Azure services")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "azure_services": {
                    "openai": "connected",
                    "cognitive_search": "connected"
                }
            }
        }

