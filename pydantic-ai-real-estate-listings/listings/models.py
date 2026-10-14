from typing import Optional

from pydantic import BaseModel, Field


class PropertyListing(BaseModel):
    """A listing record. Everything except the address is optional: notes rarely state it all."""

    address: str = Field(description="Street address, with city/state if the note gives them")
    price_usd: Optional[int] = Field(None, description="Asking price in whole US dollars")
    bedrooms: Optional[int] = Field(None, description="Number of bedrooms")
    bathrooms: Optional[float] = Field(None, description="Number of bathrooms; a half bath is 0.5")
    square_feet: Optional[int] = Field(None, description="Interior living area in square feet")
    year_built: Optional[int] = Field(None, description="Year the home was built")
    agent_name: Optional[str] = Field(None, description="Listing agent's name")
    agent_phone: Optional[str] = Field(None, description="Listing agent's phone number")
    agent_email: Optional[str] = Field(None, description="Listing agent's email address")
