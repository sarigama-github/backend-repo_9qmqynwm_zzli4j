"""
Database Schemas for VideoGen AI

Each Pydantic model corresponds to a MongoDB collection (lowercased class name).
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal

# Core video generation request captured for history/analytics
class Videorequest(BaseModel):
    prompt: str = Field(..., description="Text prompt for video generation")
    duration: Literal[3, 5, 10, 20] = Field(5, description="Video duration in seconds")
    style: Literal["realistic", "cinematic", "anime", "horror", "cartoon", "digital art"] = Field("cinematic")
    aspect_ratio: str = Field("16:9", description="Aspect ratio like 16:9, 9:16, 1:1")
    variations: int = Field(1, ge=1, le=8, description="How many variations to generate")
    reference_image_ids: List[str] = Field(default_factory=list, description="IDs of uploaded reference images")
    image_to_video_ids: List[str] = Field(default_factory=list, description="IDs of uploaded images for image-to-video generation")

# Each video job represents a single variation render attempt
class Videojob(BaseModel):
    prompt: str
    status: Literal["queued", "processing", "completed", "failed"] = "queued"
    duration: Literal[3, 5, 10, 20] = 5
    style: Literal["realistic", "cinematic", "anime", "horror", "cartoon", "digital art"] = "cinematic"
    aspect_ratio: str = "16:9"
    reference_image_ids: List[str] = []
    image_to_video_ids: List[str] = []
    variation_index: int = 0
    video_url: Optional[str] = None
    error: Optional[str] = None
    saved: bool = False

# Store uploaded file metadata
class Upload(BaseModel):
    filename: str
    url: str
    type: Literal["reference", "image2video"]
    size: int = 0
    content_type: Optional[str] = None
