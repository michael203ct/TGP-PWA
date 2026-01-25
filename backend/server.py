from fastapi import FastAPI, APIRouter, HTTPException, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timedelta, timezone
import aiohttp
from collections import defaultdict
import time
import feedparser
import asyncio
import re
from html import unescape

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'gigpulse')]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the main app without a prefix
app = FastAPI(title="the gig pulse API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# YouTube API Router
youtube_router = APIRouter(prefix="/api/youtube", tags=["youtube"])

# RSS News Feed Router
news_router = APIRouter(prefix="/api/news", tags=["news"])

# ============ Rate Limiting ============

# In-memory rate limiter (for production, use Redis)
rate_limit_store: Dict[str, List[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 30  # max requests per window per IP

def get_client_ip(request: Request) -> str:
    """Get client IP from request, handling proxies"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def check_rate_limit(client_ip: str) -> bool:
    """Check if client is within rate limit. Returns True if allowed."""
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    
    # Clean old entries
    rate_limit_store[client_ip] = [
        t for t in rate_limit_store[client_ip] if t > window_start
    ]
    
    # Check limit
    if len(rate_limit_store[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        return False
    
    # Record this request
    rate_limit_store[client_ip].append(now)
    return True

async def rate_limit_check(request: Request):
    """Rate limit dependency for YouTube endpoints"""
    client_ip = get_client_ip(request)
    if not check_rate_limit(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later."
        )

# ============ Models ============

class ChannelSuggestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    url: str
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChannelSuggestionCreate(BaseModel):
    name: str
    url: str

class NewsSuggestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    url: str
    type: str  # "website" or "twitter"
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class NewsSuggestionCreate(BaseModel):
    name: str
    url: str
    type: str

class EmailSubscriber(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    list_type: str = "merch"  # merch, newsletter, etc.
    created_at: datetime = Field(default_factory=datetime.utcnow)

class EmailSubscriberCreate(BaseModel):
    email: str
    list_type: str = "merch"

class GearSuggestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str
    description: str
    link: Optional[str] = None
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GearSuggestionCreate(BaseModel):
    name: str
    category: str
    description: str
    link: Optional[str] = None

class AppSuggestion(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str
    description: str
    link: Optional[str] = None
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AppSuggestionCreate(BaseModel):
    name: str
    category: str
    description: str
    link: Optional[str] = None

class GearItem(BaseModel):
    id: str
    name: str
    category: str
    description: str
    image: str
    price: str
    affiliate_url: str
    hearts: int = 0
    clicks: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class VoteRequest(BaseModel):
    product_id: str
    device_id: str

class ClickRequest(BaseModel):
    product_id: str

# ============ Routes ============

@api_router.get("/")
async def root():
    return {"message": "Welcome to the gig pulse API", "tagline": "Educate. Elevate. Motivate."}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# ----- Channel Suggestions -----
@api_router.post("/suggestions/channel", response_model=ChannelSuggestion)
async def create_channel_suggestion(input: ChannelSuggestionCreate):
    # Basic spam check
    spam_keywords = ['casino', 'gambling', 'crypto', 'forex', 'bitcoin', 'adult']
    name_lower = input.name.lower()
    url_lower = input.url.lower()
    
    for keyword in spam_keywords:
        if keyword in name_lower or keyword in url_lower:
            raise HTTPException(status_code=400, detail="Invalid submission")
    
    # Validate YouTube URL
    if 'youtube.com' not in url_lower and 'youtu.be' not in url_lower:
        raise HTTPException(status_code=400, detail="Please provide a valid YouTube channel URL")
    
    suggestion = ChannelSuggestion(name=input.name, url=input.url)
    await db.channel_suggestions.insert_one(suggestion.dict())
    return suggestion

@api_router.get("/suggestions/channel", response_model=List[ChannelSuggestion])
async def get_channel_suggestions(status: Optional[str] = None):
    query = {}
    if status:
        query["status"] = status
    suggestions = await db.channel_suggestions.find(query).to_list(100)
    return [ChannelSuggestion(**s) for s in suggestions]

# ----- News Suggestions -----
@api_router.post("/suggestions/news", response_model=NewsSuggestion)
async def create_news_suggestion(input: NewsSuggestionCreate):
    # Basic spam check
    spam_keywords = ['casino', 'gambling', 'forex', 'adult', 'xxx']
    name_lower = input.name.lower()
    url_lower = input.url.lower()
    
    for keyword in spam_keywords:
        if keyword in name_lower or keyword in url_lower:
            raise HTTPException(status_code=400, detail="Invalid submission")
    
    suggestion = NewsSuggestion(name=input.name, url=input.url, type=input.type)
    await db.news_suggestions.insert_one(suggestion.dict())
    return suggestion

@api_router.get("/suggestions/news", response_model=List[NewsSuggestion])
async def get_news_suggestions(status: Optional[str] = None):
    query = {}
    if status:
        query["status"] = status
    suggestions = await db.news_suggestions.find(query).to_list(100)
    return [NewsSuggestion(**s) for s in suggestions]

# ----- Email Subscriptions -----
@api_router.post("/subscribe", response_model=EmailSubscriber)
async def subscribe_email(input: EmailSubscriberCreate):
    import re
    # Validate email format
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, input.email):
        raise HTTPException(status_code=400, detail="Please enter a valid email address")
    
    # Check if already subscribed to this list
    existing = await db.email_subscribers.find_one({
        "email": input.email.lower(),
        "list_type": input.list_type
    })
    if existing:
        raise HTTPException(status_code=400, detail="You're already on the list!")
    
    subscriber = EmailSubscriber(
        email=input.email.lower(),
        list_type=input.list_type
    )
    await db.email_subscribers.insert_one(subscriber.dict())
    return subscriber

@api_router.get("/subscribers")
async def get_subscribers(list_type: Optional[str] = None):
    """Admin endpoint to get subscribers"""
    query = {}
    if list_type:
        query["list_type"] = list_type
    subscribers = await db.email_subscribers.find(query, {"_id": 0}).to_list(1000)
    return {"count": len(subscribers), "subscribers": subscribers}

# ----- Gear Suggestions -----
@api_router.post("/suggestions/gear", response_model=GearSuggestion)
async def create_gear_suggestion(input: GearSuggestionCreate):
    # Basic spam check
    spam_keywords = ['casino', 'gambling', 'forex', 'adult', 'xxx', 'crypto']
    name_lower = input.name.lower()
    desc_lower = input.description.lower()
    
    for keyword in spam_keywords:
        if keyword in name_lower or keyword in desc_lower:
            raise HTTPException(status_code=400, detail="Invalid submission")
    
    # Check for duplicate names
    existing = await db.gear_suggestions.find_one({"name": {"$regex": f"^{input.name}$", "$options": "i"}})
    if existing:
        raise HTTPException(status_code=400, detail="A similar product has already been suggested")
    
    suggestion = GearSuggestion(
        name=input.name,
        category=input.category,
        description=input.description,
        link=input.link
    )
    await db.gear_suggestions.insert_one(suggestion.dict())
    return suggestion

@api_router.get("/suggestions/gear", response_model=List[GearSuggestion])
async def get_gear_suggestions(status: Optional[str] = None):
    query = {}
    if status:
        query["status"] = status
    suggestions = await db.gear_suggestions.find(query).to_list(100)
    return [GearSuggestion(**s) for s in suggestions]

# ----- App Suggestions -----
@api_router.post("/suggestions/app", response_model=AppSuggestion)
async def create_app_suggestion(input: AppSuggestionCreate):
    # Basic spam check
    spam_keywords = ['casino', 'gambling', 'forex', 'adult', 'xxx', 'crypto', 'bitcoin']
    name_lower = input.name.lower()
    desc_lower = input.description.lower()
    
    for keyword in spam_keywords:
        if keyword in name_lower or keyword in desc_lower:
            raise HTTPException(status_code=400, detail="Invalid submission")
    
    # Check for duplicate names
    existing = await db.app_suggestions.find_one({"name": {"$regex": f"^{input.name}$", "$options": "i"}})
    if existing:
        raise HTTPException(status_code=400, detail="This app has already been suggested")
    
    suggestion = AppSuggestion(
        name=input.name,
        category=input.category,
        description=input.description,
        link=input.link
    )
    await db.app_suggestions.insert_one(suggestion.dict())
    return suggestion

@api_router.get("/suggestions/app", response_model=List[AppSuggestion])
async def get_app_suggestions(status: Optional[str] = None):
    query = {}
    if status:
        query["status"] = status
    suggestions = await db.app_suggestions.find(query).to_list(100)
    return [AppSuggestion(**s) for s in suggestions]

@api_router.post("/suggestions/app/{suggestion_id}/approve")
async def approve_app_suggestion(suggestion_id: str):
    suggestion = await db.app_suggestions.find_one({"id": suggestion_id})
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    # Add to helpful_tools collection
    new_tool = {
        "id": str(uuid.uuid4()),
        "name": suggestion["name"],
        "description": suggestion.get("description", ""),
        "icon": "apps",
        "color": "#6B7280",
        "url": suggestion.get("link", ""),
        "features": []
    }
    await db.static_helpful_tools.insert_one(new_tool)
    
    # Update suggestion status
    await db.app_suggestions.update_one(
        {"id": suggestion_id},
        {"$set": {"status": "approved"}}
    )
    return {"success": True, "message": "App added to helpful tools"}

@api_router.delete("/suggestions/app/{suggestion_id}")
async def delete_app_suggestion(suggestion_id: str):
    result = await db.app_suggestions.delete_one({"id": suggestion_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return {"success": True}

@api_router.post("/suggestions/gear/{suggestion_id}/approve")
async def approve_gear_suggestion(suggestion_id: str):
    suggestion = await db.gear_suggestions.find_one({"id": suggestion_id})
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    # Add to gear_items collection
    new_item = {
        "id": str(uuid.uuid4()),
        "name": suggestion["name"],
        "description": suggestion.get("description", ""),
        "price": "$0.00",
        "imageUrl": "",
        "affiliateUrl": suggestion.get("link", ""),
        "categories": [suggestion.get("category", "other")],
        "likes": 0
    }
    await db.gear_items.insert_one(new_item)
    
    # Update suggestion status
    await db.gear_suggestions.update_one(
        {"id": suggestion_id},
        {"$set": {"status": "approved"}}
    )
    return {"success": True, "message": "Gear item added"}

@api_router.delete("/suggestions/gear/{suggestion_id}")
async def delete_gear_suggestion(suggestion_id: str):
    result = await db.gear_suggestions.delete_one({"id": suggestion_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return {"success": True}

@api_router.post("/suggestions/channel/{suggestion_id}/approve")
async def approve_channel_suggestion(suggestion_id: str):
    suggestion = await db.channel_suggestions.find_one({"id": suggestion_id})
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    # Update suggestion status
    await db.channel_suggestions.update_one(
        {"id": suggestion_id},
        {"$set": {"status": "approved"}}
    )
    return {"success": True, "message": "Channel suggestion approved - manual setup required"}

@api_router.delete("/suggestions/channel/{suggestion_id}")
async def delete_channel_suggestion(suggestion_id: str):
    result = await db.channel_suggestions.delete_one({"id": suggestion_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return {"success": True}

@api_router.post("/suggestions/news/{suggestion_id}/approve")
async def approve_news_suggestion(suggestion_id: str):
    suggestion = await db.news_suggestions.find_one({"id": suggestion_id})
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    # Update suggestion status
    await db.news_suggestions.update_one(
        {"id": suggestion_id},
        {"$set": {"status": "approved"}}
    )
    return {"success": True, "message": "News source approved - manual setup required"}

@api_router.delete("/suggestions/news/{suggestion_id}")
async def delete_news_suggestion(suggestion_id: str):
    result = await db.news_suggestions.delete_one({"id": suggestion_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    return {"success": True}

# ----- Gear Items & Voting -----
@api_router.get("/gear")
async def get_gear_items(category: Optional[str] = None):
    """Get gear items with optional category filter"""
    query = {}
    if category and category != "all":
        query["category"] = category.lower()
    
    items = await db.gear_items.find(query).sort("score", -1).to_list(50)
    
    # If no items in DB, return mock data structure indicator
    if not items:
        return {"items": [], "source": "database_empty"}
    
    return {"items": items, "source": "database"}

@api_router.post("/gear/vote")
async def vote_for_gear(request: VoteRequest):
    """Vote for a gear item (heart)"""
    # Check rate limiting - max 5 votes per device per day
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    vote_count = await db.votes.count_documents({
        "device_id": request.device_id,
        "created_at": {"$gte": today}
    })
    
    if vote_count >= 5:
        raise HTTPException(status_code=429, detail="Daily vote limit reached (5 votes per day)")
    
    # Check if already voted for this product
    existing_vote = await db.votes.find_one({
        "product_id": request.product_id,
        "device_id": request.device_id
    })
    
    if existing_vote:
        raise HTTPException(status_code=400, detail="Already voted for this product")
    
    # Record vote
    vote = {
        "id": str(uuid.uuid4()),
        "product_id": request.product_id,
        "device_id": request.device_id,
        "created_at": datetime.utcnow()
    }
    await db.votes.insert_one(vote)
    
    # Increment heart count
    await db.gear_items.update_one(
        {"id": request.product_id},
        {"$inc": {"hearts": 1}}
    )
    
    # Recalculate score
    await recalculate_score(request.product_id)
    
    return {"success": True, "message": "Vote recorded"}

@api_router.post("/gear/click")
async def track_gear_click(request: ClickRequest):
    """Track a click on a gear item (for Shop Now button)"""
    # Increment click count
    await db.gear_items.update_one(
        {"id": request.product_id},
        {"$inc": {"clicks": 1}}
    )
    
    # Recalculate score
    await recalculate_score(request.product_id)
    
    return {"success": True}

async def recalculate_score(product_id: str):
    """Recalculate product score: hearts + (clicks × 0.5) + recency boost"""
    item = await db.gear_items.find_one({"id": product_id})
    if not item:
        return
    
    hearts = item.get("hearts", 0)
    clicks = item.get("clicks", 0)
    created_at = item.get("created_at", datetime.utcnow())
    
    # Base score
    score = hearts + (clicks * 0.5)
    
    # Recency boost: extra points for items created in last 30 days
    days_old = (datetime.utcnow() - created_at).days
    if days_old < 30:
        recency_boost = (30 - days_old) * 0.5  # Up to 15 extra points
        score += recency_boost
    
    await db.gear_items.update_one(
        {"id": product_id},
        {"$set": {"score": score}}
    )

# ----- Affiliate URL Proxy -----
@api_router.get("/affiliate-link")
async def get_affiliate_link(url: str, tag: Optional[str] = None):
    """
    Proxy endpoint to append affiliate tag to Amazon URLs.
    In production, the tag would be stored securely.
    """
    # Default affiliate tag (placeholder - user will provide real one)
    affiliate_tag = tag or os.environ.get("AMAZON_AFFILIATE_TAG", "gigpulse-20")
    
    if "amazon.com" in url:
        # Append or replace affiliate tag
        if "?" in url:
            if "tag=" in url:
                # Replace existing tag
                import re
                url = re.sub(r'tag=[^&]+', f'tag={affiliate_tag}', url)
            else:
                url = f"{url}&tag={affiliate_tag}"
        else:
            url = f"{url}?tag={affiliate_tag}"
    
    return {"url": url}

# ============ YouTube API Proxy Routes ============

# Gig work related keywords for filtering mixed-content channels
GIG_KEYWORDS = [
    # Platforms
    'uber', 'lyft', 'doordash', 'grubhub', 'instacart', 'shipt', 'spark', 'amazon flex',
    'gopuff', 'postmates', 'caviar', 'waitr', 'favor', 'roadie', 'point pickup',
    # General terms
    'rideshare', 'ride share', 'gig work', 'gig economy', 'gig worker', 'delivery driver',
    'food delivery', 'grocery delivery', 'courier', 'driver earnings', 'driver tips',
    'driver pay', 'driver income', 'driver strategy', 'driver app', 'acceptance rate',
    'completion rate', 'dash', 'dashing', 'multi-app', 'multiapp', 'multi app',
    # Earnings related
    'earnings', 'pay', 'income', 'tips', 'bonus', 'incentive', 'quest', 'challenge',
    'surge', 'peak pay', 'boost', 'promotion', 'guarantee',
    # Strategy
    'strategy', 'tutorial', 'how to', 'guide', 'walkthrough', 'review',
    # News
    'deactivat', 'lawsuit', 'settlement', 'prop 22', 'ab5', 'ic', 'independent contractor'
]

def matches_gig_keywords(title: str, description: str) -> bool:
    """Check if video title or description contains gig-related keywords"""
    text = (title + " " + description).lower()
    return any(keyword in text for keyword in GIG_KEYWORDS)

async def get_video_statistics(video_ids: list) -> dict:
    """Helper function to fetch detailed statistics for videos"""
    try:
        api_key = os.environ.get("YOUTUBE_API_KEY", "")
        if not api_key:
            return {}
            
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "part": "statistics",
            "id": ",".join(video_ids),
            "key": api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()
                stats = {}
                for item in data.get("items", []):
                    stats[item["id"]] = item["statistics"]
                return stats
    except Exception:
        return {}

async def _get_channel_details_internal(channel_id: str, force_refresh: bool = False):
    """
    Internal function to fetch channel details (no rate limiting).
    """
    api_key = os.environ.get("YOUTUBE_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="YouTube API key not configured")
    
    # Check MongoDB cache first (2 hour cache)
    if not force_refresh:
        cached = await db.youtube_channel_cache.find_one({
            "channel_id": channel_id,
            "cached_at": {"$gt": datetime.now(timezone.utc) - timedelta(hours=2)}
        })
        
        if cached:
            return {
                "success": True,
                "data": cached["data"],
                "cached": True
            }
    
    # Make API request if not cached
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "snippet,statistics,contentDetails",
        "id": channel_id,
        "key": api_key
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            if response.status != 200:
                error_data = await response.json()
                raise HTTPException(
                    status_code=response.status,
                    detail=error_data.get("error", {}).get("message", "YouTube API request failed")
                )
            
            data = await response.json()
            
            if not data.get("items"):
                raise HTTPException(status_code=404, detail="Channel not found")
            
            channel_data = data["items"][0]
            
            # Extract relevant fields
            channel_info = {
                "channel_id": channel_id,
                "title": channel_data["snippet"]["title"],
                "description": channel_data["snippet"]["description"],
                "thumbnail": channel_data["snippet"]["thumbnails"]["default"]["url"],
                "thumbnail_medium": channel_data["snippet"]["thumbnails"].get("medium", {}).get("url", ""),
                "thumbnail_high": channel_data["snippet"]["thumbnails"].get("high", {}).get("url", ""),
                "subscriber_count": channel_data["statistics"].get("subscriberCount", "0"),
                "view_count": channel_data["statistics"].get("viewCount", "0"),
                "video_count": channel_data["statistics"].get("videoCount", "0"),
                "uploads_playlist_id": channel_data["contentDetails"]["relatedPlaylists"]["uploads"]
            }
            
            # Cache the result
            await db.youtube_channel_cache.update_one(
                {"channel_id": channel_id},
                {"$set": {
                    "channel_id": channel_id,
                    "data": channel_info,
                    "cached_at": datetime.now(timezone.utc)
                }},
                upsert=True
            )
            
            return {
                "success": True,
                "data": channel_info,
                "cached": False
            }

@youtube_router.get("/channel/{channel_id}")
async def get_channel_details(channel_id: str, request: Request, force_refresh: bool = False):
    """
    Fetch detailed information about a YouTube channel.
    Caches results in MongoDB (2 hours). Use force_refresh=true to bypass cache.
    """
    await rate_limit_check(request)
    try:
        return await _get_channel_details_internal(channel_id, force_refresh)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"YouTube channel fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@youtube_router.get("/channel/{channel_id}/latest-videos")
async def get_latest_videos(
    channel_id: str, 
    max_results: int = 10, 
    filter_gig: bool = True,
    force_refresh: bool = False
):
    """
    Fetch the latest videos from a YouTube channel.
    - filter_gig: If true, only return videos matching gig-related keywords (for mixed-content channels)
    - force_refresh: Bypass cache and fetch fresh data
    - Cache: 30 minutes
    """
    try:
        api_key = os.environ.get("YOUTUBE_API_KEY", "")
        if not api_key:
            raise HTTPException(status_code=500, detail="YouTube API key not configured")
        
        # Get channel details to find uploads playlist (use internal function)
        channel_response = await _get_channel_details_internal(channel_id)
        if not channel_response["success"]:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        uploads_playlist_id = channel_response["data"]["uploads_playlist_id"]
        cache_key = f"{uploads_playlist_id}_{'filtered' if filter_gig else 'all'}"
        
        # Check cache for videos (30 minute cache, reduced from 6 hours)
        if not force_refresh:
            cached_videos = await db.youtube_video_cache.find_one({
                "cache_key": cache_key,
                "cached_at": {"$gt": datetime.now(timezone.utc) - timedelta(minutes=30)}
            })
            
            if cached_videos:
                videos = cached_videos["videos"][:max_results]
                return {
                    "success": True,
                    "data": videos,
                    "cached": True,
                    "count": len(videos),
                    "filtered": filter_gig
                }
        
        # Fetch from YouTube API - get more results if filtering
        fetch_count = max_results * 3 if filter_gig else max_results
        url = "https://www.googleapis.com/youtube/v3/playlistItems"
        params = {
            "part": "snippet",
            "playlistId": uploads_playlist_id,
            "maxResults": min(fetch_count, 50),
            "key": api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    error_data = await response.json()
                    raise HTTPException(
                        status_code=response.status,
                        detail=error_data.get("error", {}).get("message", "YouTube API request failed")
                    )
                
                data = await response.json()
                
                # Get video IDs to fetch statistics
                video_ids = [item["snippet"]["resourceId"]["videoId"] 
                            for item in data.get("items", [])]
                
                if video_ids:
                    video_stats = await get_video_statistics(video_ids)
                else:
                    video_stats = {}
                
                # Extract and structure video data
                videos = []
                for item in data.get("items", []):
                    video_id = item["snippet"]["resourceId"]["videoId"]
                    stats = video_stats.get(video_id, {})
                    title = item["snippet"]["title"]
                    description = item["snippet"]["description"][:500] if item["snippet"]["description"] else ""
                    
                    # Filter out YouTube Shorts - AGGRESSIVE filtering
                    title_lower = title.lower()
                    desc_lower = description.lower()
                    combined_text = title_lower + " " + desc_lower
                    
                    # Check for explicit shorts hashtags anywhere
                    if '#shorts' in combined_text or '#short' in combined_text:
                        continue
                    
                    # Check for shorts in description
                    if 'youtube.com/shorts' in desc_lower or 'youtu.be/shorts' in desc_lower:
                        continue
                    
                    # Count hashtags in title - ANY video with 2+ hashtags is likely a Short
                    hashtag_count = title.count('#')
                    if hashtag_count >= 2:
                        continue
                    
                    # Any hashtag at all in a title under 80 chars is likely a Short
                    if hashtag_count >= 1 and len(title) < 80:
                        continue
                    
                    # Very short titles (under 30 chars) are likely Shorts
                    if len(title) < 30:
                        continue
                    
                    # Check for common Short indicators in title (even with just 1 hashtag)
                    short_indicators = ['#badpassenger', '#lostwages', '#sidehustle', '#gigwork', '#instacart', 
                                       '#doordash', '#ubereats', '#deliverydriver', '#fyp', '#viral', '#trending',
                                       '#ridesharedriver', '#investigation', '#uber', '#lyft', '#spark', '#amazon']
                    if any(ind in title_lower for ind in short_indicators):
                        continue
                    
                    # Apply keyword filter if enabled
                    if filter_gig and not matches_gig_keywords(title, description):
                        continue
                    
                    video_info = {
                        "video_id": video_id,
                        "title": title,
                        "description": description,
                        "thumbnail": item["snippet"]["thumbnails"]["default"]["url"],
                        "thumbnail_medium": item["snippet"]["thumbnails"].get("medium", {}).get("url", ""),
                        "thumbnail_high": item["snippet"]["thumbnails"].get("high", {}).get("url", ""),
                        "published_at": item["snippet"]["publishedAt"],
                        "view_count": stats.get("viewCount", "0"),
                        "like_count": stats.get("likeCount", "0"),
                        "comment_count": stats.get("commentCount", "0"),
                        "channel_title": channel_response["data"]["title"],
                        "matches_gig_filter": True
                    }
                    videos.append(video_info)
                
                # Cache the videos
                await db.youtube_video_cache.update_one(
                    {"cache_key": cache_key},
                    {"$set": {
                        "cache_key": cache_key,
                        "playlist_id": uploads_playlist_id,
                        "channel_id": channel_id,
                        "videos": videos,
                        "filtered": filter_gig,
                        "cached_at": datetime.now(timezone.utc)
                    }},
                    upsert=True
                )
                
                return {
                    "success": True,
                    "data": videos[:max_results],
                    "cached": False,
                    "count": len(videos[:max_results]),
                    "total_found": len(videos),
                    "filtered": filter_gig
                }
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"YouTube videos fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@youtube_router.get("/search")
async def search_channels(query: str, max_results: int = 5):
    """
    Search for YouTube channels by name or handle.
    Useful for finding channel IDs to use with other endpoints.
    """
    try:
        api_key = os.environ.get("YOUTUBE_API_KEY", "")
        if not api_key:
            raise HTTPException(status_code=500, detail="YouTube API key not configured")
        
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query,
            "type": "channel",
            "maxResults": min(max_results, 25),
            "key": api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    error_data = await response.json()
                    raise HTTPException(
                        status_code=response.status,
                        detail=error_data.get("error", {}).get("message", "YouTube API request failed")
                    )
                
                data = await response.json()
                
                channels = []
                for item in data.get("items", []):
                    channel_info = {
                        "channel_id": item["id"]["channelId"],
                        "title": item["snippet"]["title"],
                        "description": item["snippet"]["description"][:200] if item["snippet"]["description"] else "",
                        "thumbnail": item["snippet"]["thumbnails"]["default"]["url"],
                        "thumbnail_high": item["snippet"]["thumbnails"].get("high", {}).get("url", "")
                    }
                    channels.append(channel_info)
                
                return {
                    "success": True,
                    "data": channels,
                    "count": len(channels),
                    "query": query
                }
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"YouTube search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@youtube_router.get("/keywords")
async def get_gig_keywords():
    """
    Return the list of keywords used for filtering gig-related content.
    Useful for understanding what terms trigger the filter.
    """
    return {
        "keywords": GIG_KEYWORDS,
        "count": len(GIG_KEYWORDS),
        "usage": "Videos are filtered if title or description contains any of these keywords"
    }

# Featured Gig Channels - configured channel handles
FEATURED_CHANNELS = [
    {"handle": "@RideshareRodeo", "name": "Rideshare Rodeo"},
    {"handle": "@TheRideshareGuy", "name": "The Rideshare Guy"},
    {"handle": "@RideshareProfessor", "name": "Rideshare Professor"},
    {"handle": "@ridexserve", "name": "RideX Serve"},
    {"handle": "@Grind4thedollar", "name": "Grind4thedollar"},
    {"handle": "@bMacUberDriver", "name": "bMac Uber Driver"},
    {"handle": "@tipyouintheapp", "name": "Tip You In The App"},
    {"handle": "@teslarideshare", "name": "Tesla Rideshare"},
    {"handle": "@Oldshoe88", "name": "Oldshoe88"},
    {"handle": "@jo_ezzy", "name": "Jo Ezzy"},
    {"handle": "@traveljb", "name": "Travel JB"},
    {"handle": "@Gig_DollarMan", "name": "Gig Dollar Man"},
    {"handle": "@JourneyRideAlong", "name": "Journey Ride Along"},
    {"handle": "@thenolagrind", "name": "The Nola Grind"},
    {"handle": "@novahustles", "name": "Nova Hustles"},
    {"handle": "@FutureRideshareMillionaire", "name": "Future Rideshare Millionaire"},
    {"handle": "@nuggsdd", "name": "Nuggs"},
]

@youtube_router.get("/featured-channels")
async def get_featured_channels():
    """
    Return the list of featured gig channels.
    """
    return {
        "success": True,
        "data": FEATURED_CHANNELS,
        "count": len(FEATURED_CHANNELS)
    }

@youtube_router.get("/resolve-handle/{handle}")
async def resolve_channel_handle(handle: str):
    """
    Resolve a YouTube channel handle (e.g., @username) to a channel ID.
    Uses the forHandle parameter for accurate resolution.
    Falls back to search for custom URLs (like /c/NovaDasher).
    """
    try:
        api_key = os.environ.get("YOUTUBE_API_KEY", "")
        if not api_key:
            raise HTTPException(status_code=500, detail="YouTube API key not configured")
        
        # Check cache first
        cached = await db.youtube_handle_cache.find_one({
            "handle": handle.lower(),
            "cached_at": {"$gt": datetime.now(timezone.utc) - timedelta(days=7)}
        })
        
        if cached:
            return {
                "success": True,
                "data": cached["data"],
                "cached": True
            }
        
        # Clean handle - remove @ if present
        clean_handle = handle.lstrip("@")
        
        async with aiohttp.ClientSession() as session:
            # First try using forHandle parameter (works for @handles)
            url = "https://www.googleapis.com/youtube/v3/channels"
            params = {
                "part": "snippet,contentDetails",
                "forHandle": clean_handle,
                "key": api_key
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("items"):
                        item = data["items"][0]
                        channel_data = {
                            "channel_id": item["id"],
                            "title": item["snippet"]["title"],
                            "description": item["snippet"]["description"][:200] if item["snippet"]["description"] else "",
                            "thumbnail": item["snippet"]["thumbnails"]["default"]["url"],
                            "thumbnail_high": item["snippet"]["thumbnails"].get("high", {}).get("url", ""),
                            "handle": handle
                        }
                        
                        # Cache the result
                        await db.youtube_handle_cache.update_one(
                            {"handle": handle.lower()},
                            {"$set": {
                                "handle": handle.lower(),
                                "data": channel_data,
                                "cached_at": datetime.now(timezone.utc)
                            }},
                            upsert=True
                        )
                        
                        return {
                            "success": True,
                            "data": channel_data,
                            "cached": False
                        }
            
            # Fallback: search for the channel (for custom URLs like /c/NovaDasher)
            search_url = "https://www.googleapis.com/youtube/v3/search"
            search_params = {
                "part": "snippet",
                "q": clean_handle,
                "type": "channel",
                "maxResults": 1,
                "key": api_key
            }
            
            async with session.get(search_url, params=search_params) as response:
                if response.status != 200:
                    error_data = await response.json()
                    raise HTTPException(
                        status_code=response.status,
                        detail=error_data.get("error", {}).get("message", "YouTube API request failed")
                    )
                
                data = await response.json()
                
                if not data.get("items"):
                    raise HTTPException(status_code=404, detail=f"Channel not found: {handle}")
                
                item = data["items"][0]
                channel_data = {
                    "channel_id": item["id"]["channelId"],
                    "title": item["snippet"]["title"],
                    "description": item["snippet"]["description"][:200] if item["snippet"]["description"] else "",
                    "thumbnail": item["snippet"]["thumbnails"]["default"]["url"],
                    "thumbnail_high": item["snippet"]["thumbnails"].get("high", {}).get("url", ""),
                    "handle": handle
                }
                
                # Cache the result
                await db.youtube_handle_cache.update_one(
                    {"handle": handle.lower()},
                    {"$set": {
                        "handle": handle.lower(),
                        "data": channel_data,
                        "cached_at": datetime.now(timezone.utc)
                    }},
                    upsert=True
                )
                
                return {
                    "success": True,
                    "data": channel_data,
                    "cached": False
                }
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Handle resolution error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@youtube_router.get("/feed")
async def get_video_feed(max_per_channel: int = 3, force_refresh: bool = False):
    """
    Get a combined feed of recent videos from all featured channels.
    Returns videos sorted by publish date (newest first).
    """
    try:
        # Check cache for the full feed (15 minute cache)
        if not force_refresh:
            cached_feed = await db.youtube_feed_cache.find_one({
                "feed_type": "featured",
                "cached_at": {"$gt": datetime.now(timezone.utc) - timedelta(minutes=15)}
            })
            
            if cached_feed:
                return {
                    "success": True,
                    "data": cached_feed["data"],
                    "channels": cached_feed["channels"],
                    "cached": True,
                    "count": len(cached_feed["data"])
                }
        
        all_videos = []
        resolved_channels = []
        
        for channel_info in FEATURED_CHANNELS:
            try:
                # Resolve handle to channel ID
                handle = channel_info["handle"]
                resolve_result = await resolve_channel_handle(handle)
                
                if resolve_result["success"]:
                    channel_data = resolve_result["data"]
                    channel_id = channel_data["channel_id"]
                    
                    resolved_channels.append({
                        "channel_id": channel_id,
                        "name": channel_data["title"],
                        "thumbnail": channel_data["thumbnail_high"] or channel_data["thumbnail"],
                        "handle": handle
                    })
                    
                    # Get latest videos from this channel
                    videos_result = await get_latest_videos(
                        channel_id=channel_id,
                        max_results=max_per_channel,
                        filter_gig=False,  # Don't filter since these are dedicated gig channels
                        force_refresh=force_refresh
                    )
                    
                    if videos_result["success"]:
                        for video in videos_result["data"]:
                            video["channel_thumbnail"] = channel_data["thumbnail_high"] or channel_data["thumbnail"]
                            video["channel_handle"] = handle
                            all_videos.append(video)
                            
            except Exception as e:
                logger.warning(f"Failed to fetch videos for {channel_info['handle']}: {str(e)}")
                continue
        
        # Sort all videos by publish date (newest first)
        all_videos.sort(key=lambda x: x.get("published_at", ""), reverse=True)
        
        # Cache the feed
        await db.youtube_feed_cache.update_one(
            {"feed_type": "featured"},
            {"$set": {
                "feed_type": "featured",
                "data": all_videos,
                "channels": resolved_channels,
                "cached_at": datetime.now(timezone.utc)
            }},
            upsert=True
        )
        
        return {
            "success": True,
            "data": all_videos,
            "channels": resolved_channels,
            "cached": False,
            "count": len(all_videos)
        }
        
    except Exception as e:
        logger.error(f"Feed fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

# ============ RSS News Feed Routes ============

# RSS Feed Sources - Gig Economy News
RSS_FEEDS = [
    # Working RSS Feeds - Tested and Verified
    # Independent Gig Economy Blogs
    {"name": "The Rideshare Guy", "url": "https://therideshareguy.com/feed/", "category": "rideshare", "type": "blog"},
    {"name": "Gridwise Blog", "url": "https://gridwise.io/blog/feed/", "category": "delivery", "type": "blog"},
    {"name": "Ridester", "url": "https://www.ridester.com/blog/feed/", "category": "rideshare", "type": "blog"},
    {"name": "Ridesharing Driver", "url": "https://ridesharingdriver.com/blog/feed/", "category": "rideshare", "type": "blog"},
    {"name": "Gig Economy Show", "url": "https://gigeconomyshow.com/blog/feed/", "category": "rideshare", "type": "blog"},
    {"name": "EntreCourier", "url": "https://entrecourier.com/blog/feed/", "category": "delivery", "type": "blog"},
    
    # Official Platform Blogs (with working RSS)
    {"name": "Amazon Flex Blog", "url": "https://flex.amazon.com/blog/feed/", "category": "delivery", "type": "official"},
    {"name": "Roadie Driver Blog", "url": "https://driver.roadie.com/blog/feed/", "category": "delivery", "type": "official"},
    {"name": "Grubhub News", "url": "https://about.grubhub.com/feed/", "category": "delivery", "type": "official"},
    
    # Official Platform Blogs (via Google News RSS)
    {"name": "Uber Blog", "url": "https://news.google.com/rss/search?q=site:uber.com/blog&hl=en-US&gl=US&ceid=US:en", "category": "rideshare", "type": "official"},
    {"name": "Lyft Blog", "url": "https://news.google.com/rss/search?q=site:lyft.com/blog&hl=en-US&gl=US&ceid=US:en", "category": "rideshare", "type": "official"},
    {"name": "DoorDash Dasher", "url": "https://news.google.com/rss/search?q=site:dasher.doordash.com&hl=en-US&gl=US&ceid=US:en", "category": "delivery", "type": "official"},
    {"name": "Instacart", "url": "https://news.google.com/rss/search?q=site:instacart.com/company&hl=en-US&gl=US&ceid=US:en", "category": "shopping", "type": "official"},
    {"name": "Shipt", "url": "https://news.google.com/rss/search?q=site:corporate.shipt.com&hl=en-US&gl=US&ceid=US:en", "category": "shopping", "type": "official"},
]

# X/Twitter RSS feeds - Note: Most Nitter instances are blocked, using static display instead
# These accounts will be shown as "Featured X Accounts" section on the News page
# When a working Twitter RSS proxy is found, these can be enabled
TWITTER_FEEDS = []  # Disabled due to Nitter blocking

# Featured X/Twitter accounts (shown as buttons to follow)
FEATURED_X_ACCOUNTS = [
    {"handle": "TheRideshareGuy", "name": "Harry Campbell", "bio": "Top gig economy news & tips for Uber/Lyft/DoorDash drivers"},
    {"handle": "RideshareRodeo", "name": "Rideshare Rodeo", "bio": "Gig economy discussions & driver community"},
]

# Gig work keywords for filtering
NEWS_GIG_KEYWORDS = [
    # Platforms
    'uber', 'lyft', 'doordash', 'grubhub', 'instacart', 'shipt', 'spark', 'amazon flex',
    'gopuff', 'postmates', 'caviar', 'waitr', 'favor', 'roadie', 'walmart', 'driver',
    # General terms
    'rideshare', 'ride share', 'gig work', 'gig economy', 'gig worker', 'delivery',
    'food delivery', 'grocery', 'courier', 'earnings', 'tips', 'dasher', 'shopper',
    'driver pay', 'driver income', 'acceptance rate', 'completion rate', 'dash',
    'multi-app', 'multiapp', 'deactivat', 'incentive', 'bonus', 'surge', 'peak pay',
    'prop 22', 'ab5', 'independent contractor', 'flex', 'dashing', 'instacart shopper'
]

def clean_html(text: str) -> str:
    """Remove HTML tags and decode entities"""
    if not text:
        return ""
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', text)
    # Decode HTML entities
    clean = unescape(clean)
    # Remove extra whitespace
    clean = ' '.join(clean.split())
    return clean[:500]  # Limit length

def matches_news_keywords(title: str, summary: str) -> bool:
    """Check if article matches gig-related keywords"""
    text = (title + " " + summary).lower()
    return any(keyword in text for keyword in NEWS_GIG_KEYWORDS)

def categorize_article(title: str, summary: str, source_category: str) -> str:
    """Determine article category based on content"""
    text = (title + " " + summary).lower()
    
    # Shopping platforms
    if any(kw in text for kw in ['instacart', 'shipt', 'grocery', 'shopper']):
        return 'shopping'
    
    # Delivery platforms  
    if any(kw in text for kw in ['doordash', 'grubhub', 'uber eats', 'postmates', 'gopuff', 'delivery', 'dasher', 'food']):
        return 'delivery'
    
    # Rideshare platforms
    if any(kw in text for kw in ['uber', 'lyft', 'rideshare', 'ride share', 'passenger', 'rider']):
        return 'rideshare'
    
    # Default to source category
    return source_category

async def fetch_single_feed(session: aiohttp.ClientSession, feed_info: dict, days_back: int = 30) -> List[dict]:
    """Fetch and parse a single RSS feed (blog or Twitter)"""
    articles = []
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
    is_tweet = feed_info.get("type") == "tweet"
    
    try:
        async with session.get(feed_info["url"], timeout=aiohttp.ClientTimeout(total=15)) as response:
            if response.status != 200:
                logger.warning(f"Failed to fetch {feed_info['name']}: HTTP {response.status}")
                return []
            
            content = await response.text()
            
            # Parse feed (feedparser is synchronous, run in executor)
            loop = asyncio.get_event_loop()
            parsed = await loop.run_in_executor(None, feedparser.parse, content)
            
            for entry in parsed.entries[:20]:  # Limit per feed
                try:
                    # Parse publish date
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        pub_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                    else:
                        # Skip if no date
                        continue
                    
                    # Skip if older than cutoff
                    if pub_date < cutoff_date:
                        continue
                    
                    title = clean_html(entry.get('title', ''))
                    summary = clean_html(entry.get('summary', entry.get('description', '')))
                    
                    # For tweets, use the content as both title and snippet
                    if is_tweet:
                        # Tweet content is usually in description
                        tweet_text = clean_html(entry.get('description', entry.get('title', '')))
                        # Truncate for title
                        title = tweet_text[:100] + "..." if len(tweet_text) > 100 else tweet_text
                        summary = tweet_text
                    else:
                        # Filter blog posts by gig keywords
                        if not matches_news_keywords(title, summary):
                            continue
                    
                    # Get thumbnail image (blogs only, tweets don't have reliable images)
                    thumbnail = None
                    if not is_tweet:
                        if hasattr(entry, 'media_content') and entry.media_content:
                            thumbnail = entry.media_content[0].get('url')
                        elif hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                            thumbnail = entry.media_thumbnail[0].get('url')
                        elif hasattr(entry, 'enclosures') and entry.enclosures:
                            for enc in entry.enclosures:
                                if enc.get('type', '').startswith('image'):
                                    thumbnail = enc.get('href')
                                    break
                    
                    # Categorize article
                    category = categorize_article(title, summary, feed_info["category"])
                    
                    articles.append({
                        "id": str(uuid.uuid4()),
                        "title": title,
                        "source": feed_info["name"],
                        "category": category,
                        "type": "tweet" if is_tweet else "article",
                        "thumbnail": thumbnail if not is_tweet else None,
                        "snippet": summary[:300] + "..." if len(summary) > 300 else summary,
                        "published_at": pub_date.isoformat(),
                        "url": entry.get('link', ''),
                    })
                    
                except Exception as e:
                    logger.warning(f"Error parsing entry from {feed_info['name']}: {str(e)}")
                    continue
                    
    except asyncio.TimeoutError:
        logger.warning(f"Timeout fetching {feed_info['name']}")
    except Exception as e:
        logger.warning(f"Error fetching {feed_info['name']}: {str(e)}")
    
    return articles

@news_router.get("/feed")
async def get_news_feed(
    request: Request,
    category: Optional[str] = None,
    limit: int = 30,
    force_refresh: bool = False
):
    """
    Fetch aggregated news feed from multiple RSS sources including X/Twitter.
    - category: Filter by rideshare, delivery, shopping, or all
    - limit: Maximum number of articles to return
    - force_refresh: Bypass cache
    - Cache: 30 minutes
    """
    await rate_limit_check(request)
    
    try:
        cache_key = f"news_feed_{category or 'all'}"
        
        # Check cache (30 minute cache)
        if not force_refresh:
            cached = await db.news_feed_cache.find_one({
                "cache_key": cache_key,
                "cached_at": {"$gt": datetime.now(timezone.utc) - timedelta(minutes=30)}
            })
            
            if cached:
                articles = cached["articles"][:limit]
                return {
                    "success": True,
                    "data": articles,
                    "cached": True,
                    "count": len(articles),
                    "sources": len(RSS_FEEDS) + len(TWITTER_FEEDS)
                }
        
        # Combine all feed sources (blogs + Twitter)
        all_feeds = RSS_FEEDS + TWITTER_FEEDS
        
        # Fetch all feeds concurrently
        async with aiohttp.ClientSession(
            headers={"User-Agent": "TheGigPulse/1.0 RSS Reader"}
        ) as session:
            tasks = [fetch_single_feed(session, feed) for feed in all_feeds]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine all articles
        all_articles = []
        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
        
        # Filter by category if specified
        if category and category.lower() != 'all':
            all_articles = [a for a in all_articles if a["category"] == category.lower()]
        
        # Sort by publish date (newest first)
        all_articles.sort(key=lambda x: x.get("published_at", ""), reverse=True)
        
        # Deduplicate by title similarity
        seen_titles = set()
        unique_articles = []
        for article in all_articles:
            # Simple dedup by first 50 chars of title
            title_key = article["title"][:50].lower()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_articles.append(article)
        
        # Cache the results
        await db.news_feed_cache.update_one(
            {"cache_key": cache_key},
            {"$set": {
                "cache_key": cache_key,
                "articles": unique_articles,
                "cached_at": datetime.now(timezone.utc)
            }},
            upsert=True
        )
        
        return {
            "success": True,
            "data": unique_articles[:limit],
            "cached": False,
            "count": len(unique_articles[:limit]),
            "total": len(unique_articles),
            "sources": len(RSS_FEEDS) + len(TWITTER_FEEDS)
        }
        
    except Exception as e:
        logger.error(f"News feed fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@news_router.get("/sources")
async def get_news_sources():
    """Get list of all news sources being aggregated"""
    return {
        "success": True,
        "sources": [
            {"name": f["name"], "category": f["category"], "type": "rss"}
            for f in RSS_FEEDS
        ],
        "count": len(RSS_FEEDS)
    }

@news_router.get("/twitter-accounts")
async def get_twitter_accounts():
    """Get list of featured X/Twitter accounts for gig news"""
    return {
        "success": True,
        "accounts": FEATURED_X_ACCOUNTS,
        "count": len(FEATURED_X_ACCOUNTS),
        "note": "Follow these accounts on X/Twitter for real-time gig economy updates"
    }

# Include the router in the main app
app.include_router(api_router)
app.include_router(youtube_router)
app.include_router(news_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ Static Content API (Persisted in MongoDB) ============
# This data is stored in MongoDB to prevent loss across code changes/forks

static_content_router = APIRouter(prefix="/api/static-content", tags=["static-content"])

# Default data - only used for initial seeding
DEFAULT_WEEKLY_SHOWS = [
    {
        "id": "ws-1",
        "name": "Drivers Coast 2 Coast X Space",
        "creator": "Drivers Coast 2 Coast",
        "schedule": "Mondays 7pm EST",
        "duration": "~2 hours",
        "platform": "X Spaces",
        "url": "https://twitter.com/DriversCoast2C",
        "thumbnail": "https://static.prod-images.emergentagent.com/jobs/6aff9965-a15e-4038-b712-ce2b2890b588/images/577a8ef80304cddec1bb7ee5ecbaa37c86043a60a3f0314ffe28694664b2fe27.png"
    },
    {
        "id": "ws-2",
        "name": "Show Me The Money Club",
        "creator": "Show Me The Money Club",
        "schedule": "Tuesdays 8pm EST",
        "duration": "~1.5 hours",
        "platform": "X Spaces",
        "url": "https://twitter.com/ShowMeMoneyClub",
        "thumbnail": "https://static.prod-images.emergentagent.com/jobs/6aff9965-a15e-4038-b712-ce2b2890b588/images/9ce7df651da42c9e7ece5edbf578a848dc261f0f933db3f7b31ac418a264178a.png"
    },
    {
        "id": "ws-3",
        "name": "Off The Clock",
        "creator": "Off The Clock",
        "schedule": "Wednesdays 9pm EST",
        "duration": "~1 hour",
        "platform": "X Spaces",
        "url": "https://twitter.com/OffTheClock",
        "thumbnail": "https://static.prod-images.emergentagent.com/jobs/6aff9965-a15e-4038-b712-ce2b2890b588/images/9a0c9e45165836af5ef74ce2bd3a2c6b7102efc69a36f95e3d23153fd00a080b.png"
    }
]

DEFAULT_FEATURED_CHANNELS = [
    {
        "id": "fc-ridesharerodeo",
        "name": "Rideshare Rodeo",
        "handle": "@ridesharerodeo",
        "tag": "Gig tips & tricks",
        "thumbnail": "https://yt3.googleusercontent.com/ytc/AIdro_nF7zzgJkPCh6H0dU7_NwB7lSzxXcvO7wnr9wd5cQ=s176-c-k-c0x00ffffff-no-rj",
        "channelUrl": "https://www.youtube.com/@ridesharerodeo"
    },
    {
        "id": "fc-rideshareguy",
        "name": "The Rideshare Guy",
        "handle": "@TheRideshareGuy",
        "tag": "Industry news & reviews",
        "thumbnail": "https://yt3.googleusercontent.com/ytc/AIdro_kzMjpyZXHbVvA1Gp2ykLTZlr-3B7kGH_NMXs7z=s176-c-k-c0x00ffffff-no-rj",
        "channelUrl": "https://www.youtube.com/@TheRideshareGuy"
    },
    {
        "id": "fc-rideshareprof",
        "name": "Rideshare Professor",
        "handle": "@RideshareProf",
        "tag": "Earnings strategies",
        "thumbnail": "https://yt3.googleusercontent.com/ytc/AIdro_mJUq1H8jJX3y0cFxUOEi9Tn8ISkqTnQEKqLm_l=s176-c-k-c0x00ffffff-no-rj",
        "channelUrl": "https://www.youtube.com/@RideshareProf"
    }
]

DEFAULT_GIG_APPS = [
    {"id": "app-uber", "name": "Uber", "icon": "car", "color": "#000000", "category": "rideshare", "url": "https://www.uber.com/us/en/drive/"},
    {"id": "app-ubereats", "name": "Uber Eats", "icon": "fast-food", "color": "#06C167", "category": "delivery", "url": "https://www.ubereats.com/deliver"},
    {"id": "app-lyft", "name": "Lyft", "icon": "car-sport", "color": "#FF00BF", "category": "rideshare", "url": "https://www.lyft.com/driver"},
    {"id": "app-doordash", "name": "DoorDash", "icon": "bicycle", "color": "#FF3008", "category": "delivery", "url": "https://www.doordash.com/dasher/signup/"},
    {"id": "app-grubhub", "name": "Grubhub", "icon": "restaurant", "color": "#F63440", "category": "delivery", "url": "https://driver.grubhub.com/"},
    {"id": "app-instacart", "name": "Instacart", "icon": "cart", "color": "#43B02A", "category": "shopping", "url": "https://shoppers.instacart.com/"},
    {"id": "app-spark", "name": "Spark", "icon": "flash", "color": "#FFC220", "category": "delivery", "url": "https://drive4spark.walmart.com/"},
    {"id": "app-amazonflex", "name": "Amazon Flex", "icon": "cube", "color": "#FF9900", "category": "delivery", "url": "https://flex.amazon.com/"},
    {"id": "app-shipt", "name": "Shipt", "icon": "bag-handle", "color": "#00A859", "category": "shopping", "url": "https://www.shipt.com/be-a-shopper/"},
    {"id": "app-roadie", "name": "Roadie", "icon": "navigate", "color": "#1B8F5D", "category": "delivery", "url": "https://www.roadie.com/drivers"}
]

DEFAULT_HELPFUL_TOOLS = [
    {"id": "tool-gridwise", "name": "Gridwise", "icon": "analytics", "color": "#4A90D9", "description": "Earnings tracker & analytics for gig workers. Track mileage, earnings, and get insights to maximize income.", "url": "https://gridwise.io/", "features": ["Track earnings across all gig platforms", "Real-time demand heatmaps", "Mileage tracking with IRS-compliant reports", "Airport & event alerts", "Compare weekly earnings trends"]},
    {"id": "tool-everlance", "name": "Everlance", "icon": "speedometer", "color": "#00C7B7", "description": "Automatic mileage & expense tracker. IRS-compliant logs for tax deductions.", "url": "https://link.everlance.com/t7IY1nJY1Zb", "features": ["Automatic mileage tracking", "IRS-compliant expense reports", "Tax deduction finder", "Premium: Unlimited mileage tracking", "Photo receipt capture"]},
    {"id": "tool-worksolo", "name": "WorkSolo", "icon": "briefcase", "color": "#6366F1", "description": "All-in-one business tool for independent contractors. Invoicing, contracts, and payments.", "url": "https://worksolo.onelink.me/7Viq/7tg2zv88", "features": ["AI-powered tax estimation", "Quarterly tax reminders", "Deduction optimization", "Real-time tax liability tracking", "Works with all gig platforms"]},
    {"id": "tool-gigu", "name": "GigU", "icon": "school", "color": "#F59E0B", "description": "Educational platform for gig workers. Learn strategies to maximize your earnings.", "url": "https://gigu.me/JGCDA", "features": ["Free online courses for gig drivers", "Learn best practices & tips", "Certification programs available", "Community forum access", "New driver orientation guides"]},
    {"id": "tool-mystro", "name": "Mystro", "icon": "flash", "color": "#EF4444", "description": "Auto-accept rides across multiple platforms. Never miss a good trip again.", "url": "https://l.myst.ro/N0Q9/yew647h9", "features": ["Auto-accept rides from multiple apps", "Set minimum fare thresholds", "Hands-free driving mode", "Smart surge detection", "Battery & data optimized"]},
    {"id": "tool-maxymo", "name": "Maxymo", "icon": "car", "color": "#10B981", "description": "Smart automation for rideshare drivers. Filter rides and optimize your driving strategy.", "url": "https://maxymoapp.com/?code=Mic2676", "features": ["Multi-app management dashboard", "Accept rides from all platforms", "Earnings optimization tips", "Driver status across apps", "Reduce app switching time"]}
]

DEFAULT_FEATURED_GEAR = [
    {
        "id": "fg-redtiger",
        "name": "REDTIGER F17 4K 3 Channel Dash Cam",
        "blurb": "5GHz WiFi, GPS, 64GB Card Included",
        "image": "https://customer-assets.emergentagent.com/job_gig-essentials-hub/artifacts/bvstr1hk_f1.jpg",
        "price": "$179.99",
        "affiliateUrl": "https://www.amazon.com/dp/B0CSPBJ2HM?tag=thegigpulse-20"
    },
    {
        "id": "fg-fanttik",
        "name": "Fanttik Slim V8 APEX Car Vacuum",
        "blurb": "19000Pa Cordless, 4-in-1, Type-C",
        "image": "https://customer-assets.emergentagent.com/job_gig-essentials-hub/artifacts/5vi8o56r_f2.jpg",
        "price": "$65.99",
        "affiliateUrl": "https://www.amazon.com/dp/B0CQYTNNW7?tag=thegigpulse-20"
    },
    {
        "id": "fg-iottie",
        "name": "iOttie Easy One Touch Signature",
        "blurb": "Dashboard & Windshield Mount",
        "image": "https://customer-assets.emergentagent.com/job_gig-essentials-hub/artifacts/7ric738l_f3.jpg",
        "price": "$24.95",
        "affiliateUrl": "https://www.amazon.com/dp/B0875RKTQF?tag=thegigpulse-20"
    }
]

async def seed_static_content():
    """Seed default static content if not exists in database"""
    collections_to_seed = [
        ("static_weekly_shows", DEFAULT_WEEKLY_SHOWS, "id"),
        ("static_featured_channels", DEFAULT_FEATURED_CHANNELS, "id"),
        ("static_gig_apps", DEFAULT_GIG_APPS, "id"),
        ("static_helpful_tools", DEFAULT_HELPFUL_TOOLS, "id"),
        ("static_featured_gear", DEFAULT_FEATURED_GEAR, "id"),
    ]
    
    for collection_name, default_data, id_field in collections_to_seed:
        collection = db[collection_name]
        count = await collection.count_documents({})
        if count == 0:
            logger.info(f"Seeding {collection_name} with {len(default_data)} items")
            for item in default_data:
                await collection.update_one(
                    {id_field: item[id_field]},
                    {"$set": item},
                    upsert=True
                )

@static_content_router.get("/weekly-shows")
async def get_weekly_shows():
    """Get weekly shows from database"""
    items = await db.static_weekly_shows.find({}, {"_id": 0}).to_list(100)
    return {"success": True, "data": items, "count": len(items)}

@static_content_router.get("/featured-channels")
async def get_static_featured_channels():
    """Get featured YouTube channels from database"""
    items = await db.static_featured_channels.find({}, {"_id": 0}).to_list(100)
    return {"success": True, "data": items, "count": len(items)}

@static_content_router.get("/gig-apps")
async def get_gig_apps():
    """Get gig apps from database"""
    items = await db.static_gig_apps.find({}, {"_id": 0}).to_list(100)
    return {"success": True, "data": items, "count": len(items)}

@static_content_router.get("/helpful-tools")
async def get_helpful_tools():
    """Get helpful tools from database"""
    items = await db.static_helpful_tools.find({}, {"_id": 0}).to_list(100)
    return {"success": True, "data": items, "count": len(items)}

@static_content_router.get("/featured-gear")
async def get_featured_gear():
    """Get featured gear/essentials from database"""
    items = await db.static_featured_gear.find({}, {"_id": 0}).to_list(100)
    return {"success": True, "data": items, "count": len(items)}

@static_content_router.get("/community-favorites")
async def get_community_favorites():
    """Get community favorites from database, sorted by likes (most popular first)"""
    items = await db.static_community_favorites.find({}, {"_id": 0}).sort("likes", -1).to_list(100)
    return {"success": True, "data": items, "count": len(items)}

@static_content_router.post("/community-favorites/{item_id}/like")
async def like_community_favorite(item_id: str):
    """Increment like count for a community favorite item"""
    result = await db.static_community_favorites.update_one(
        {"id": item_id},
        {"$inc": {"likes": 1}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Get updated item
    item = await db.static_community_favorites.find_one({"id": item_id}, {"_id": 0})
    return {"success": True, "likes": item.get("likes", 0)}

@static_content_router.put("/community-favorites/{item_id}/categories")
async def update_community_favorite_categories(item_id: str, categories: list[str] = []):
    """Update categories for a community favorite item (temporary admin feature)"""
    # Validate categories
    valid_categories = ['rideshare', 'delivery', 'shopping']
    filtered_categories = [c.lower() for c in categories if c.lower() in valid_categories]
    
    result = await db.static_community_favorites.update_one(
        {"id": item_id},
        {"$set": {"categories": filtered_categories}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item = await db.static_community_favorites.find_one({"id": item_id}, {"_id": 0})
    return {"success": True, "categories": item.get("categories", [])}

app.include_router(static_content_router)

@app.on_event("startup")
async def startup_db_client():
    # Create indexes for better query performance
    await db.votes.create_index([("device_id", 1), ("created_at", 1)])
    await db.votes.create_index([("product_id", 1), ("device_id", 1)], unique=True)
    await db.gear_items.create_index([("score", -1)])
    await db.gear_items.create_index([("category", 1)])
    # YouTube cache indexes
    await db.youtube_channel_cache.create_index("channel_id", unique=True)
    await db.youtube_channel_cache.create_index("cached_at")
    await db.youtube_video_cache.create_index("cache_key", unique=True)
    await db.youtube_video_cache.create_index("cached_at")
    # News feed cache indexes
    await db.news_feed_cache.create_index("cache_key", unique=True)
    await db.news_feed_cache.create_index("cached_at")
    # Static content indexes
    await db.static_weekly_shows.create_index("id", unique=True)
    await db.static_featured_channels.create_index("id", unique=True)
    await db.static_gig_apps.create_index("id", unique=True)
    await db.static_helpful_tools.create_index("id", unique=True)
    await db.static_featured_gear.create_index("id", unique=True)
    await db.static_community_favorites.create_index("id", unique=True)
    logger.info("Database indexes created")
    
    # Seed static content if empty
    await seed_static_content()
    logger.info("Static content seeded")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
