"""
Dynamic royalty‑free music search module.

Supports Jamendo API for live search results. Falls back to a
local curated catalogue when an API key is missing or the remote call fails.

Environment variables expected (set at runtime or in a .env file):

    JAMENDO_CLIENT_ID   – required for Jamendo search

Example:
    >>> from music_api import search_music
    >>> tracks = search_music(q="lofi", provider="jamendo")

All public functions:
    search_music(...)      – unified search wrapper
    download_music(...)    – download a selected track
    get_category_names()   – categories from curated list (fallback only)
    get_track_count_by_category()
"""

from __future__ import annotations

import os
import json
import random
import logging
from typing import Dict, List, Literal, Tuple, Any

import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(handler)

# Set Jamendo API credentials
JAMENDO_CLIENT_ID = "aa4f5a9d"
JAMENDO_CLIENT_SECRET = "9b2368a20504b7429e01226578eac3d7"

# Set as environment variables for backwards compatibility
os.environ["JAMENDO_CLIENT_ID"] = JAMENDO_CLIENT_ID
os.environ["JAMENDO_CLIENT_SECRET"] = JAMENDO_CLIENT_SECRET

Provider = Literal["jamendo", "curated"]

###############################################################################
# 1. Curated fallback catalogue
###############################################################################

CURATED_MUSIC: List[Dict[str, Any]] = [
    {
        "id": "ambient1",
        "title": "Ambiance Paisible",
        "artist": "Free Music",
        "duration": 180,
        "category": "Ambiance",
        "mood": "Relaxant",
        "url": "https://cdn.freesound.org/previews/635/635732_10985201-lq.mp3",
        "provider": "curated",
    },
    {
        "id": "electronic1",
        "title": "Groove Électronique",
        "artist": "Digital Beat",
        "duration": 185,
        "category": "Électronique",
        "mood": "Moderne",
        "url": "https://cdn.freesound.org/previews/635/635544_7037-lq.mp3",
        "provider": "curated",
    },
    {
        "id": "relaxing1",
        "title": "Jazz Lounge",
        "artist": "Jazz Masters",
        "duration": 230,
        "category": "Jazz",
        "mood": "Détendu",
        "url": "https://cdn.freesound.org/previews/447/447910_5121236-lq.mp3",
        "provider": "curated",
    },
    {
        "id": "relaxing2",
        "title": "Piano Contemplatif",
        "artist": "Melody Makers",
        "duration": 210,
        "category": "Classique",
        "mood": "Tranquille",
        "url": "https://cdn.freesound.org/previews/629/629110_14015496-lq.mp3",
        "provider": "curated",
    }
]

###############################################################################
# 2. Public API helpers
###############################################################################

def _jamendo_headers() -> Dict[str, str]:
    return {"Accept": "application/json"}


def _jamendo_params(query: str, page: int, per_page: int, category: str = None) -> Dict[str, str]:
    params = {
        "client_id": JAMENDO_CLIENT_ID,
        "format": "json",
        "limit": str(per_page),
        "offset": str((page - 1) * per_page),
        "audioformat": "mp31",  # smaller preview mp3
    }
    
    # Add search query if provided
    if query:
        params["namesearch"] = query
    
    # Add genre filter if category is provided
    if category and category.lower() != "tous" and category.lower() != "all":
        params["tags"] = category.lower()
    
    return params


def _search_jamendo(query: str, page: int, per_page: int, category: str = None) -> Tuple[int, List[Dict[str, Any]]]:
    # No need to check for credentials since we hardcoded them
    logger.info(f"Searching Jamendo API with query: {query}, category: {category}")
    
    url = "https://api.jamendo.com/v3.0/tracks"
    params = _jamendo_params(query, page, per_page, category)
    logger.debug("Jamendo request params: %s", params)
    
    try:
        resp = requests.get(url, headers=_jamendo_headers(), params=params, timeout=15)
        
        if resp.status_code != 200:
            logger.error("Jamendo API error %s: %s", resp.status_code, resp.text[:200])
            return 0, []
        
        data = resp.json()
        tracks_json = data.get("results", [])
        total = int(data.get("headers", {}).get("results_count", len(tracks_json)))
        
        logger.info("Jamendo returned %s tracks (page %s)", len(tracks_json), page)
        
        tracks = [
            {
                "id": f"jamendo_{t['id']}",  # Prefix with provider to avoid collisions
                "title": t["name"],
                "artist": t["artist_name"],
                "duration": int(t["duration"]),
                "category": t.get("genre", "Unknown"),
                "mood": t.get("mood", ""),
                "url": t["audio"] or t["audiodownload"],
                "provider": "jamendo",
                "license": t.get("license_ccurl", ""),
            }
            for t in tracks_json
        ]
        
        # Add duration_str to each track
        for track in tracks:
            track["duration_str"] = format_duration(track["duration"])
            
        return total, tracks
    except Exception as e:
        logger.error(f"Error in Jamendo search: {str(e)}", exc_info=True)
        return 0, []

###############################################################################
# 3. Public API – search / download / helpers
###############################################################################

def search_music(
    q: str = "",
    category: str | None = None,
    provider: Provider = "jamendo",
    page: int = 1,
    per_page: int = 10,
) -> Dict[str, Any]:
    """Search for music tracks.

    Args:
        q: Search query (free‑text).
        category: Optional category filter (applies to both jamendo and curated).
        provider: "jamendo" or "curated".
        page: 1‑based page index.
        per_page: Results per page (max 50 for Jamendo).

    Returns:
        dict with keys: total, page, per_page, tracks (list[dict]).
    """

    logger.info(
        "search_music(provider=%s, q=%r, category=%r, page=%s, per_page=%s)",
        provider,
        q,
        category,
        page,
        per_page,
    )

    # Always try Jamendo first
    if provider == "jamendo":
        total, tracks = _search_jamendo(q, page, per_page, category)
        # If Jamendo returns no results, fall back to curated
        if len(tracks) == 0 and q:
            logger.info("No Jamendo results, falling back to curated collection")
            total, tracks = _search_curated(category, q, page, per_page)
    else:
        total, tracks = _search_curated(category, q, page, per_page)

    # Add duration_str to each track for display in UI
    for track in tracks:
        if "duration_str" not in track:
            track["duration_str"] = format_duration(track["duration"])

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "tracks": tracks,
    }


def _search_curated(
    category: str | None, q: str, page: int, per_page: int
) -> Tuple[int, List[Dict[str, Any]]]:
    filtered = CURATED_MUSIC
    if category and category.lower() != "all":
        filtered = [t for t in filtered if t["category"].lower() == category.lower()]
    if q:
        q_low = q.lower()
        filtered = [
            t
            for t in filtered
            if q_low in t["title"].lower()
            or q_low in t["artist"].lower()
            or q_low in t["mood"].lower()
        ]
    total = len(filtered)
    start = (page - 1) * per_page
    end = start + per_page
    return total, filtered[start:end]


def download_music(track_id: str, download_path: str) -> bool:
    """Download a track to *download_path*.

    Works for any provider; for Jamendo we always get a direct MP3
    URL from search result, so we just fetch it.
    """
    try:
        # Check if this is a Jamendo track
        if track_id.startswith("jamendo_"):
            # Handle Jamendo tracks - we need to extract the ID and use the API
            jamendo_id = track_id.replace("jamendo_", "")
            logger.info(f"Downloading Jamendo track {jamendo_id}")
            
            # Since we already have tracks in session state with URLs, we can reuse them
            # This is a workaround since we don't have the full track info here
            url = None
            
            # Try to find the track in session data or make a new API call
            if not url:
                # We need to get the download URL from the API 
                search_url = f"https://api.jamendo.com/v3.0/tracks/?client_id={JAMENDO_CLIENT_ID}&format=json&id={jamendo_id}"
                resp = requests.get(search_url, timeout=15)
                
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get('results') and len(data['results']) > 0:
                        url = data['results'][0].get('audio') or data['results'][0].get('audiodownload')
                
            if url:
                logger.info(f"Downloading from Jamendo URL: {url}")
                return _download_file(url, download_path)
            else:
                logger.error(f"Could not find download URL for Jamendo track: {jamendo_id}")
                return False
        
        # Handle curated tracks
        track = next((t for t in CURATED_MUSIC if t["id"] == track_id), None)
        if track:
            url = track["url"]
            logger.info(f"Downloading curated track: {url}")
            return _download_file(url, download_path)
        
        logger.error(f"Track {track_id} not found in any collection")
        return False
    
    except Exception as e:
        logger.error(f"Error downloading track {track_id}: {str(e)}", exc_info=True)
        return False

###############################################################################
# 4. Utility helpers (download, duration, stats)
###############################################################################


def _download_file(url: str, download_path: str) -> bool:
    try:
        os.makedirs(os.path.dirname(download_path), exist_ok=True)
        resp = requests.get(url, stream=True, timeout=30)
        if resp.status_code != 200:
            logger.warning("HTTP %s while downloading %s", resp.status_code, url)
            return False
        with open(download_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        logger.info("Saved %s", download_path)
        return True
    except Exception as exc:
        logger.error("Failed to download %s: %s", url, exc, exc_info=True)
        return False


def format_duration(seconds: int) -> str:
    mins, secs = divmod(seconds, 60)
    return f"{mins}:{secs:02d}"


def fetch_jamendo_categories() -> List[str]:
    """Fetch music genres from Jamendo API.
    
    Returns a list of genre names directly from the Jamendo API.
    """
    try:
        url = "https://api.jamendo.com/v3.0/tracks/"
        params = {
            "client_id": JAMENDO_CLIENT_ID,
            "format": "json",
            "limit": "100",  # Get a good number of tracks to extract genres
            "boost": "popularity",  # Get popular tracks for more relevant genres
            "include": "musicinfo",  # Include genre information
        }
        
        logger.info("Fetching genres from Jamendo API")
        resp = requests.get(url, headers=_jamendo_headers(), params=params, timeout=15)
        
        if resp.status_code != 200:
            logger.error("Jamendo API error %s while fetching genres", resp.status_code)
            return []
        
        data = resp.json()
        tracks = data.get("results", [])
        
        # Extract unique genres from the tracks
        genres = set()
        for track in tracks:
            if "genre" in track and track["genre"]:
                # Some tracks have multiple genres separated by spaces
                track_genres = track["genre"].split()
                for genre in track_genres:
                    if genre and len(genre) > 2:  # Filter out very short genre names
                        genres.add(genre.capitalize())
        
        # Sort alphabetically
        genre_list = sorted(list(genres))
        logger.info("Found %d genres from Jamendo API: %s", len(genre_list), genre_list)
        return genre_list
        
    except Exception as e:
        logger.error("Error fetching Jamendo genres: %s", str(e), exc_info=True)
        return []

def get_category_names() -> List[str]:
    """Get a combined list of music categories.
    
    Returns categories from the Jamendo API and the curated list, sorted alphabetically.
    """
    # Get categories from the Jamendo API
    jamendo_cats = fetch_jamendo_categories()
    
    # Get categories from curated music
    curated_cats = {t["category"] for t in CURATED_MUSIC}
    
    # Common categories to include as fallback if API fails
    common_cats = {"Pop", "Rock", "Electronic", "Classical", "Jazz", "Hip Hop", "Ambient", "Folk", "Blues", "Country"}
    
    # Combine all categories and sort
    # If we got categories from Jamendo, prioritize those, otherwise use fallbacks
    if jamendo_cats:
        all_cats = sorted(set(jamendo_cats) | curated_cats)
    else:
        all_cats = sorted(curated_cats | common_cats)
    
    logger.info("Available categories: %s", all_cats)
    return all_cats


def get_track_count_by_category() -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for t in CURATED_MUSIC:
        counts[t["category"]] = counts.get(t["category"], 0) + 1
    return counts


def get_duration_ranges() -> List[Dict[str, Any]]:
    """Get predefined duration ranges for filtering.
    
    Returns a list of dictionaries with min_seconds, max_seconds, and label.
    """
    return [
        {"min_seconds": 0, "max_seconds": 120, "label": "Court (< 2 min)"},
        {"min_seconds": 120, "max_seconds": 240, "label": "Moyen (2-4 min)"},
        {"min_seconds": 240, "max_seconds": 99999, "label": "Long (> 4 min)"}
    ] 