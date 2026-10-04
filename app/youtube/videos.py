import random
from typing import List, Optional
from pydantic import BaseModel, Field


class Video(BaseModel):
    """
    Representation of a YouTube video.
    """
    id: str = Field(..., description="YouTube video ID")
    title: str = Field(..., description="Title of the video")
    url: str = Field(..., description="Direct link to watch video")
    published_at: str = Field(default="", description="ISO publication timestamp")
    thumbnail_url: str = Field(default="", description="Thumbnail image URL")
    description: str = Field(default="", description="Snippet description")

    def display_label(self) -> str:
        """Formatted display string for dropdowns."""
        return f"{self.title} ({self.id})"


def select_random_video(videos: List[Video]) -> Optional[Video]:
    """Randomly selects one video from a list of videos."""
    if not videos:
        return None
    return random.choice(videos)
