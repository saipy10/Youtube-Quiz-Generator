import re
from typing import List, Tuple, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.config.settings import settings
from app.youtube.videos import Video
from app.utils.logger import setup_logger, mask_secret

logger = setup_logger(__name__)


class YouTubeAPI:
    """Client for interacting with YouTube Data API v3."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.YOUTUBE_API_KEY
        if not self.api_key:
            logger.warning("YouTube API key is not configured!")
        else:
            logger.info(f"YouTubeAPI initialized with key {mask_secret(self.api_key)}")

        self._service = None

    @property
    def service(self):
        if self._service is None:
            if not self.api_key:
                raise ValueError("YouTube API key is missing. Please set YOUTUBE_API_KEY in .env")
            self._service = build("youtube", "v3", developerKey=self.api_key, cache_discovery=False)
        return self._service

    def clean_channel_input(self, channel_input: str) -> Tuple[str, str]:
        """
        Parses user channel input which could be:
        - Channel ID (UC...)
        - Handle (@ChannelName or https://youtube.com/@ChannelName)
        - Custom name / username
        Returns tuple: (query_type, cleaned_value)
        query_type can be 'id', 'handle', or 'username'
        """
        val = channel_input.strip()
        # Handle URLs like https://www.youtube.com/@handle or https://youtube.com/channel/UCxxx
        if "youtube.com" in val:
            if "/channel/" in val:
                val = val.split("/channel/")[-1].split("/")[0].split("?")[0]
            elif "/@" in val:
                val = "@" + val.split("/@")[-1].split("/")[0].split("?")[0]
            elif "/c/" in val or "/user/" in val:
                val = val.split("/")[-1].split("?")[0]

        if val.startswith("UC") and len(val) >= 20:
            return "id", val
        if val.startswith("@"):
            return "handle", val
        # If no @ prefix but looks like a handle, try handle first
        if re.match(r"^[a-zA-Z0-9_\-\.]+$", val) and not val.startswith("UC"):
            return "handle", f"@{val}"
        return "id", val

    def get_channel_details(self, channel_input: str) -> dict:
        """
        Retrieves channel metadata and uploads playlist ID.
        """
        query_type, cleaned_val = self.clean_channel_input(channel_input)
        logger.info(f"Resolving channel: type={query_type}, value={cleaned_val}")

        try:
            req = None
            if query_type == "id":
                req = self.service.channels().list(part="snippet,contentDetails", id=cleaned_val)
            elif query_type == "handle":
                req = self.service.channels().list(part="snippet,contentDetails", forHandle=cleaned_val)
            else:
                req = self.service.channels().list(part="snippet,contentDetails", forUsername=cleaned_val)

            res = req.execute()
            items = res.get("items", [])
            if not items and query_type == "handle":
                # Fallback: maybe username without @
                clean_name = cleaned_val.lstrip("@")
                res = self.service.channels().list(part="snippet,contentDetails", forUsername=clean_name).execute()
                items = res.get("items", [])

            if not items:
                raise ValueError(f"No YouTube channel found matching '{channel_input}'.")

            channel_item = items[0]
            channel_title = channel_item.get("snippet", {}).get("title", "")
            channel_id = channel_item.get("id", "")
            uploads_playlist_id = (
                channel_item.get("contentDetails", {})
                .get("relatedPlaylists", {})
                .get("uploads", "")
            )

            # Fallback for uploads playlist ID: UC -> UU
            if not uploads_playlist_id and channel_id.startswith("UC"):
                uploads_playlist_id = "UU" + channel_id[2:]

            return {
                "channel_id": channel_id,
                "title": channel_title,
                "uploads_playlist_id": uploads_playlist_id,
            }

        except HttpError as e:
            logger.error(f"YouTube API HttpError: {e}")
            raise RuntimeError(f"YouTube API error: {e.reason if hasattr(e, 'reason') else e}")
        except Exception as e:
            logger.error(f"Failed to get channel details: {e}")
            raise

    def get_latest_videos(self, channel_input: str, count: int = 10) -> List[Video]:
        """
        Retrieves the latest `count` videos uploaded by the specified channel.
        """
        logger.info(f"Fetching latest {count} videos for channel '{channel_input}'")
        channel_info = self.get_channel_details(channel_input)
        uploads_id = channel_info.get("uploads_playlist_id")

        if not uploads_id:
            raise ValueError(f"Could not find uploads playlist for channel '{channel_info.get('title')}'.")

        try:
            req = self.service.playlistItems().list(
                part="snippet",
                playlistId=uploads_id,
                maxResults=min(count, 50),
            )
            res = req.execute()
            items = res.get("items", [])

            videos: List[Video] = []
            for item in items:
                snippet = item.get("snippet", {})
                video_id = snippet.get("resourceId", {}).get("videoId")
                title = snippet.get("title", "").strip()

                # Skip deleted or private placeholders
                if not video_id or title in ("Private video", "Deleted video"):
                    continue

                published_at = snippet.get("publishedAt", "")
                thumbnails = snippet.get("thumbnails", {})
                thumbnail_url = (
                    thumbnails.get("high", {}).get("url")
                    or thumbnails.get("medium", {}).get("url")
                    or thumbnails.get("default", {}).get("url")
                    or ""
                )
                description = snippet.get("description", "")

                videos.append(
                    Video(
                        id=video_id,
                        title=title,
                        url=f"https://www.youtube.com/watch?v={video_id}",
                        published_at=published_at,
                        thumbnail_url=thumbnail_url,
                        description=description,
                    )
                )

                if len(videos) >= count:
                    break

            logger.info(f"Successfully retrieved {len(videos)} videos from channel '{channel_info.get('title')}'.")
            return videos

        except HttpError as e:
            logger.error(f"YouTube API error retrieving playlist items: {e}")
            raise RuntimeError(f"YouTube API error: {e.reason if hasattr(e, 'reason') else e}")
        except Exception as e:
            logger.error(f"Failed to retrieve latest videos: {e}")
            raise
