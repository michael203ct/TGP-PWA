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

# ============ Arena Models ============

# Driver Wins - Trip sharing
class DriverWinTrip(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    platform: str  # uber, lyft, doordash, instacart, etc.
    total_amount: float
    base_pay: Optional[float] = None
    tip_amount: Optional[float] = None
    miles: Optional[float] = None
    minutes: Optional[int] = None
    note: Optional[str] = None
    personal_link: Optional[str] = None
    fires: int = 1  # Start with 1 fire
    fired_by: List[str] = Field(default_factory=list)  # device_ids
    session_id: str  # For editing own trips
    tip_updated: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

class DriverWinTripCreate(BaseModel):
    username: str
    platform: str
    total_amount: float
    base_pay: Optional[float] = None
    tip_amount: Optional[float] = None
    miles: Optional[float] = None
    minutes: Optional[int] = None
    note: Optional[str] = None
    personal_link: Optional[str] = None
    session_id: str

class DriverWinTripUpdate(BaseModel):
    total_amount: Optional[float] = None
    base_pay: Optional[float] = None
    tip_amount: Optional[float] = None
    miles: Optional[float] = None
    minutes: Optional[int] = None
    note: Optional[str] = None
    session_id: str

# Live Pulse - Live sessions and competitions
class LivePulseSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    host_name: str
    host_key: str  # Secret key for host access
    youtube_url: Optional[str] = None
    twitch_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_live: bool = False
    total_earnings: float = 0
    platform_breakdown: Dict[str, float] = Field(default_factory=dict)
    trip_count: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

class LivePulseSessionCreate(BaseModel):
    title: str
    description: Optional[str] = None
    host_name: str
    youtube_url: Optional[str] = None
    twitch_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    start_time: Optional[datetime] = None

class LivePulseTripAdd(BaseModel):
    host_key: str
    platform: str
    amount: float
    base_pay: Optional[float] = None
    tip_amount: Optional[float] = None
    note: Optional[str] = None

class Competition(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    competition_type: str  # "2v2", "3v3", "solo_tally", "team_relay"
    scheduled_time: datetime
    status: str = "pending"  # pending, approved, live, completed
    participants: List[Dict] = Field(default_factory=list)
    created_by: str  # username
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CompetitionCreate(BaseModel):
    title: str
    description: Optional[str] = None
    competition_type: str
    scheduled_time: datetime
    created_by: str

# Arena Router
arena_router = APIRouter(prefix="/api/arena", tags=["arena"])

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

@api_router.delete("/subscribers/clear-test")
async def clear_test_subscribers():
    """Admin endpoint to clear test email subscribers"""
    result = await db.email_subscribers.delete_many({
        "email": {"$regex": "^test.*@example\\.com$"}
    })
    return {"success": True, "deleted": result.deleted_count}

@api_router.delete("/subscribers/{email}")
async def delete_subscriber(email: str):
    """Admin endpoint to delete a specific subscriber"""
    result = await db.email_subscribers.delete_one({"email": email.lower()})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Subscriber not found")
    return {"success": True}

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
    
    # Extract handle from URL
    channel_url = suggestion.get("url", "")
    channel_name = suggestion.get("name", "")
    
    # Try to extract handle from URL
    handle = ""
    if "@" in channel_url:
        # URL like youtube.com/@handle
        handle = "@" + channel_url.split("@")[-1].split("/")[0].split("?")[0]
    elif "/c/" in channel_url:
        # URL like youtube.com/c/channelname
        handle = "@" + channel_url.split("/c/")[-1].split("/")[0].split("?")[0]
    elif "/channel/" in channel_url:
        # URL like youtube.com/channel/UCxxxxx - use channel ID format
        handle = "@" + channel_url.split("/channel/")[-1].split("/")[0].split("?")[0]
    else:
        # Fallback - just use name without spaces
        handle = "@" + channel_name.replace(" ", "")
    
    # Check if channel already exists in approved channels
    existing = await db.approved_video_channels.find_one({"handle": handle})
    if not existing:
        # Add to approved_video_channels for the video feed
        new_channel = {
            "handle": handle,
            "name": channel_name
        }
        await db.approved_video_channels.insert_one(new_channel)
    
    # Clear the video feed cache so new channel appears
    await db.youtube_feed_cache.delete_many({"feed_type": "featured"})
    
    # Update suggestion status
    await db.channel_suggestions.update_one(
        {"id": suggestion_id},
        {"$set": {"status": "approved"}}
    )
    return {"success": True, "message": f"Channel '{channel_name}' added to video feed!"}

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
    """Helper function to fetch detailed statistics and duration for videos"""
    try:
        api_key = os.environ.get("YOUTUBE_API_KEY", "")
        if not api_key:
            return {}
            
        url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            "part": "statistics,contentDetails",
            "id": ",".join(video_ids),
            "key": api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                data = await response.json()
                stats = {}
                for item in data.get("items", []):
                    video_data = item.get("statistics", {})
                    # Add duration from contentDetails
                    content_details = item.get("contentDetails", {})
                    video_data["duration"] = content_details.get("duration", "")
                    stats[item["id"]] = video_data
                return stats
    except Exception:
        return {}

def parse_iso8601_duration(duration_str: str) -> int:
    """Parse ISO 8601 duration (e.g., PT1H23M45S) to seconds"""
    import re
    if not duration_str:
        return 0
    
    # Pattern for ISO 8601 duration: PT1H23M45S
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, duration_str)
    
    if not match:
        return 0
    
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    
    return hours * 3600 + minutes * 60 + seconds

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
                    
                    # Count hashtags in title - ANY video with 3+ hashtags is likely a Short
                    hashtag_count = title.count('#')
                    if hashtag_count >= 3:
                        continue
                    
                    # Check for common Short indicators in title
                    short_indicators = ['#fyp', '#viral', '#trending', '#foryou', '#foryoupage']
                    if any(ind in title_lower for ind in short_indicators):
                        continue
                    
                    # Filter out videos under 3 minutes (180 seconds) - catches Shorts and short clips
                    duration_str = stats.get("duration", "")
                    duration_seconds = parse_iso8601_duration(duration_str)
                    if duration_seconds > 0 and duration_seconds < 180:
                        continue
                    
                    # Apply keyword filter if enabled
                    if filter_gig and not matches_gig_keywords(title, description):
                        continue
                    
                    # Filter videos older than 14 days
                    published_at_str = item["snippet"]["publishedAt"]
                    try:
                        published_date = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
                        cutoff_date = datetime.now(timezone.utc) - timedelta(days=14)
                        if published_date < cutoff_date:
                            continue
                    except Exception:
                        pass  # If date parsing fails, include the video
                    
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
                        "matches_gig_filter": True,
                        "duration": duration_str,
                        "duration_seconds": duration_seconds
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

@youtube_router.post("/hide/{video_id}")
async def hide_video(video_id: str):
    """Hide a video from the feed (admin function). Stores video_id in hidden_videos collection."""
    try:
        await db.hidden_videos.update_one(
            {"video_id": video_id},
            {"$set": {"video_id": video_id, "hidden_at": datetime.now(timezone.utc)}},
            upsert=True
        )
        # Clear the feed cache so hidden video is immediately removed
        await db.youtube_feed_cache.delete_many({"feed_type": "featured"})
        return {"success": True, "message": f"Video {video_id} hidden"}
    except Exception as e:
        logger.error(f"Error hiding video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@youtube_router.delete("/hide/{video_id}")
async def unhide_video(video_id: str):
    """Unhide a video (admin function)."""
    try:
        result = await db.hidden_videos.delete_one({"video_id": video_id})
        # Clear the feed cache so unhidden video appears again
        await db.youtube_feed_cache.delete_many({"feed_type": "featured"})
        if result.deleted_count == 0:
            return {"success": False, "message": "Video was not hidden"}
        return {"success": True, "message": f"Video {video_id} unhidden"}
    except Exception as e:
        logger.error(f"Error unhiding video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@youtube_router.get("/hidden")
async def get_hidden_videos():
    """Get list of all hidden video IDs (admin function)."""
    try:
        hidden = await db.hidden_videos.find({}, {"_id": 0, "video_id": 1}).to_list(1000)
        return {"success": True, "data": [h["video_id"] for h in hidden], "count": len(hidden)}
    except Exception as e:
        logger.error(f"Error fetching hidden videos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
    Return the list of featured gig channels (combines hardcoded + approved suggestions).
    """
    # Get approved channels from database
    approved_channels = await db.approved_video_channels.find({}, {"_id": 0}).to_list(100)
    
    # Combine with default channels
    all_channels = FEATURED_CHANNELS + approved_channels
    
    return {
        "success": True,
        "data": all_channels,
        "count": len(all_channels)
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
        # Check cache for the full feed (30 minute cache for faster loads)
        if not force_refresh:
            cached_feed = await db.youtube_feed_cache.find_one({
                "feed_type": "featured",
                "cached_at": {"$gt": datetime.now(timezone.utc) - timedelta(minutes=30)}
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
        
        # Fetch videos from channels concurrently for faster loading
        import asyncio
        
        async def fetch_channel_videos(channel_info):
            try:
                handle = channel_info["handle"]
                resolve_result = await resolve_channel_handle(handle)
                
                if resolve_result["success"]:
                    channel_data = resolve_result["data"]
                    channel_id = channel_data["channel_id"]
                    
                    channel_resolved = {
                        "channel_id": channel_id,
                        "name": channel_data["title"],
                        "thumbnail": channel_data["thumbnail_high"] or channel_data["thumbnail"],
                        "handle": handle
                    }
                    
                    videos_result = await get_latest_videos(
                        channel_id=channel_id,
                        max_results=max_per_channel,
                        filter_gig=False,
                        force_refresh=force_refresh
                    )
                    
                    videos = []
                    if videos_result["success"]:
                        for video in videos_result["data"]:
                            video["channel_thumbnail"] = channel_data["thumbnail_high"] or channel_data["thumbnail"]
                            video["channel_handle"] = handle
                            videos.append(video)
                    
                    return channel_resolved, videos
            except Exception as e:
                logger.warning(f"Failed to fetch videos for {channel_info['handle']}: {str(e)}")
            return None, []
        
        # Run all channel fetches concurrently
        # Get approved channels from database and combine with default
        approved_channels = await db.approved_video_channels.find({}, {"_id": 0}).to_list(100)
        all_feed_channels = FEATURED_CHANNELS + approved_channels
        
        results = await asyncio.gather(*[fetch_channel_videos(ch) for ch in all_feed_channels])
        
        for channel_resolved, videos in results:
            if channel_resolved:
                resolved_channels.append(channel_resolved)
            all_videos.extend(videos)
        
        # Sort all videos by publish date (newest first)
        all_videos.sort(key=lambda x: x.get("published_at", ""), reverse=True)
        
        # Filter out hidden videos
        hidden_videos = await db.hidden_videos.find({}, {"_id": 0, "video_id": 1}).to_list(1000)
        hidden_ids = set(h["video_id"] for h in hidden_videos)
        all_videos = [v for v in all_videos if v.get("video_id") not in hidden_ids]
        
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

def resolve_google_news_url(url: str) -> str:
    """
    Attempt to resolve Google News redirect URLs to their actual destination.
    Google News RSS URLs have encoded article URLs in the path.
    """
    if not url or 'news.google.com/rss/articles/' not in url:
        return url
    
    # Google News URLs contain base64-encoded article URLs
    # For now, return the URL as-is but mark it needs resolution
    # The frontend will handle opening these URLs
    return url

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
    {"id": "ws-1", "name": "Drivers Coast 2 Coast X Space", "creator": "@DriversC2C", "schedule": "Mondays 7pm EST", "duration": "~2 hours", "platform": "X Spaces", "url": "https://x.com/DriversC2C", "thumbnail": "https://customer-assets.emergentagent.com/job_rideheart/artifacts/xgqfe4ue_DriversC2C.jpg"},
    {"id": "ws-2", "name": "Show Me The Money Club Podcast", "creator": "The Rideshare Guy", "schedule": "Tuesdays 6pm EST", "duration": "~1.5 hours", "platform": "YouTube", "url": "https://youtube.com/playlist?list=PLicaiyRJvVbwrofXH-sOxoFuCvXrybwRl&si=76nHGGF9blHDpaIU", "thumbnail": "https://customer-assets.emergentagent.com/job_rideheart/artifacts/9623hrj4_Show%20Me%20The%20Money%20Club.jpg"},
    {"id": "ws-3", "name": "Off The Clock Podcast", "creator": "Vinny Kuzz", "schedule": "Wednesdays 9pm EST", "duration": "~2 hours", "platform": "YouTube", "url": "https://youtube.com/playlist?list=PLApTPUXT30jdwrG2QlHnX5UHj8m7WHeDR&si=74OQFTBd8TCos9_M", "thumbnail": "https://customer-assets.emergentagent.com/job_rideheart/artifacts/6ol4w7sj_Off%20The%20Clock.jpg"}
]

DEFAULT_FEATURED_CHANNELS = [
    {"id": "fc-ridesharerodeo", "name": "Rideshare Rodeo", "handle": "@RideshareRodeo", "tag": "Gig tips & tricks", "thumbnail": "https://customer-assets.emergentagent.com/job_rideheart/artifacts/o524ke00_Rideshare%20Rodeo.jpg", "channelUrl": "https://www.youtube.com/@RideshareRodeo"},
    {"id": "fc-rideshareguy", "name": "The Rideshare Guy", "handle": "@Therideshareguy", "tag": "Industry news & reviews", "thumbnail": "https://customer-assets.emergentagent.com/job_rideheart/artifacts/20dx6o5m_RSG.jpg", "channelUrl": "https://www.youtube.com/@Therideshareguy"},
    {"id": "fc-rideshareprof", "name": "Rideshare Professor", "handle": "@AskTorsten", "tag": "Earnings strategies", "thumbnail": "https://customer-assets.emergentagent.com/job_rideheart/artifacts/0r3f9g4y_Rideshare%20Professor.jpg", "channelUrl": "https://www.youtube.com/@AskTorsten"}
]

DEFAULT_GIG_APPS = [
    {
        "id": "app-uber",
        "name": "Uber",
        "icon": "car",
        "color": "#6B7280",
        "category": "rideshare",
        "url": "https://drivers.uber.com/i/j4uz56c",
        "description": "The world's largest rideshare platform. Drive passengers to their destinations and earn on your own schedule.",
        "features": ["Flexible hours - drive when you want", "Weekly payouts + instant cash out", "Quests & surge pricing bonuses", "In-app navigation & safety features", "24/7 driver support"]
    },
    {
        "id": "app-ubereats",
        "name": "Uber Eats",
        "icon": "fast-food",
        "color": "#06C167",
        "category": "delivery",
        "url": "https://drivers.uber.com/i/j4uz56c",
        "description": "Deliver food from local restaurants to hungry customers. No passengers, just packages.",
        "features": ["Deliver by car, bike, or scooter", "See earnings before accepting", "Stack multiple deliveries", "Keep 100% of tips", "Flexible scheduling"]
    },
    {
        "id": "app-lyft",
        "name": "Lyft",
        "icon": "car-sport",
        "color": "#FF00BF",
        "category": "rideshare",
        "url": "https://www.lyft.com/drive-with-lyft?utm_medium=d2da_iacc",
        "description": "A friendlier rideshare experience. Drive passengers around your city and earn competitive rates.",
        "features": ["Driver-friendly community", "Earnings guarantees for new drivers", "Streak bonuses & ride challenges", "Express Pay - cash out instantly", "Rental & vehicle programs available"]
    },
    {
        "id": "app-doordash",
        "name": "DoorDash",
        "icon": "bicycle",
        "color": "#FF3008",
        "category": "delivery",
        "url": "https://www.doordash.com/dasher/signup/",
        "description": "America's #1 food delivery app. Dash when you want and earn what you need.",
        "features": ["See pay before you accept", "Peak Pay during busy times", "Challenges & completion bonuses", "Fast Pay - instant earnings access", "Deliver food, groceries, or packages"]
    },
    {
        "id": "app-grubhub",
        "name": "Grubhub",
        "icon": "restaurant",
        "color": "#F63440",
        "category": "delivery",
        "url": "https://driver.grubhub.com/",
        "description": "Deliver from your favorite local restaurants. Flexible scheduling with competitive pay.",
        "features": ["Schedule blocks in advance", "Keep 100% of tips", "Contribution pay guarantee", "Catering deliveries for bigger orders", "Driver specialist support"]
    },
    {
        "id": "app-instacart",
        "name": "Instacart",
        "icon": "cart",
        "color": "#43B02A",
        "category": "shopping",
        "url": "http://inst.cr/t/ejlhZllTdEgx",
        "description": "Shop and deliver groceries from stores like Costco, Kroger, and more. Great tips from appreciative customers.",
        "features": ["Shop at stores you know", "Batch multiple orders together", "See earnings + tip upfront", "Instant cashout available", "In-store & delivery options"]
    },
    {
        "id": "app-spark",
        "name": "Spark",
        "icon": "flash",
        "color": "#FFC220",
        "category": "delivery",
        "url": "https://drive4spark.walmart.com/",
        "description": "Walmart's delivery platform. Deliver groceries, general merchandise, and express orders.",
        "features": ["Consistent Walmart order volume", "Incentive trips & bonuses", "Shop & deliver or curbside pickup", "See trip details before accepting", "First access to high-value orders"]
    },
    {
        "id": "app-amazonflex",
        "name": "Amazon Flex",
        "icon": "cube",
        "color": "#FF9900",
        "category": "delivery",
        "url": "https://flex.amazon.com/",
        "description": "Deliver packages for Amazon. Grab delivery blocks and earn $18-25/hour.",
        "features": ["Predictable block-based scheduling", "Deliver from local warehouses", "Same-day & grocery deliveries", "Earn $18-$25+ per hour", "Use your own vehicle"]
    },
    {
        "id": "app-shipt",
        "name": "Shipt",
        "icon": "bag-handle",
        "color": "#00A859",
        "category": "shopping",
        "url": "https://www.shipt.com/shopper/be-a-shopper",
        "description": "Personal shopping and delivery from Target, CVS, and more. Build relationships with regular customers.",
        "features": ["Shop from Target & other stores", "Build a base of member matches", "Preferred shopper program", "Keep 100% of tips", "Flexible metro scheduling"]
    },
    {
        "id": "app-roadie",
        "name": "Roadie",
        "icon": "navigate",
        "color": "#1B8F5D",
        "category": "delivery",
        "url": "https://www.roadie.com/drivers",
        "description": "Deliver big and bulky items that don't fit in regular delivery vehicles. Great for SUV and truck owners.",
        "features": ["Big item deliveries = bigger pay", "Long-distance gigs available", "Same-day local deliveries", "Partner with major retailers", "Ideal for larger vehicles"]
    }
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

DEFAULT_COMMUNITY_FAVORITES = [
    {"id": "cf-lotus-bags", "name": "Lotus Trolley Reusable Shopping Bags", "category": "shopping", "description": "4-bag set that fits perfectly in your shopping cart. Eco-friendly and durable.", "image": "https://customer-assets.emergentagent.com/job_rideheart/artifacts/trlp3nm8_Lotus%20Trolley%20Shopping%20Bags.jpg", "price": "$44.99", "rating": "4.7", "reviews": "12.5k", "affiliateUrl": "https://www.amazon.com/dp/B071YTZ86J?tag=thegigpulse-20", "likes": 4, "categories": ["shopping"]},
    {"id": "cf-insulated-bag", "name": "XXXL Insulated Food Delivery Bag", "category": "delivery", "description": "Keep food hot/cold. 23x14x15 inches, perfect for large orders.", "image": "https://customer-assets.emergentagent.com/job_rideheart/artifacts/et447jey_10.jpg", "price": "$21.99", "rating": "4.6", "reviews": "9.8k", "affiliateUrl": "https://www.amazon.com/dp/B07XXZGVSM?tag=thegigpulse-20", "likes": 4, "categories": ["delivery", "shopping"]},
    {"id": "cf-headrest-hooks", "name": "Car Headrest Hooks (4-Pack)", "category": "rideshare", "description": "Organize bags, groceries, and delivery items. Strong metal construction.", "image": "https://customer-assets.emergentagent.com/job_rideheart/artifacts/edsncv3u_8.jpg", "price": "$9.99", "rating": "4.4", "reviews": "22.3k", "affiliateUrl": "https://www.amazon.com/dp/B01LXT4726?tag=thegigpulse-20", "likes": 3, "categories": ["delivery", "shopping", "rideshare"]},
    {"id": "cf-energizer-powerbank", "name": "Energizer 30000mAh Power Bank", "category": "rideshare", "description": "High-capacity portable charger. Keep your devices powered all day.", "image": "https://customer-assets.emergentagent.com/job_rideheart/artifacts/jkh0uvu7_2.jpg", "price": "$31.99", "rating": "4.5", "reviews": "8.2k", "affiliateUrl": "https://www.amazon.com/dp/B0CW5SYK7G?tag=thegigpulse-20", "likes": 1, "categories": ["rideshare", "delivery", "shopping"]},
    {"id": "cf-vantrue-s1pro", "name": "Vantrue S1 Pro Dash Cam", "category": "rideshare", "description": "2.7K front dash cam with WiFi, GPS, STARVIS 2, and voice control.", "image": "https://customer-assets.emergentagent.com/job_rideheart/artifacts/lcltr8rd_3.jpg", "price": "$149.99", "rating": "4.6", "reviews": "3.8k", "affiliateUrl": "https://www.amazon.com/dp/B0F4WK84NS?tag=thegigpulse-20", "likes": 1, "categories": ["rideshare", "delivery", "shopping"]},
    {"id": "cf-vantrue-nexus2x", "name": "Vantrue Nexus 2X Dual Dash Cam", "category": "rideshare", "description": "5G WiFi, 2.7K HDR front + 1080P cabin camera with STARVIS 2.", "image": "https://customer-assets.emergentagent.com/job_rideheart/artifacts/5253yjfg_4.jpg", "price": "$199.99", "rating": "4.7", "reviews": "2.1k", "affiliateUrl": "https://www.amazon.com/dp/B0D9GRRXH5?tag=thegigpulse-20", "likes": 1, "categories": ["rideshare", "delivery", "shopping"]},
    {"id": "cf-reusable-shopping-bags", "name": "Extra Large Reusable Shopping Bags (2-Pack)", "category": "shopping", "description": "Heavy duty extra large reusable bags with reinforced handles. Perfect for Instacart, Shipt shoppers.", "image": "https://customer-assets.emergentagent.com/job_gigtracker-9/artifacts/pjzudbmn_19.jpg", "price": "$12.99", "rating": "4.6", "reviews": "8.2k", "affiliateUrl": "https://www.amazon.com/dp/B07RTWWKV6?tag=thegigpulse-20", "likes": 1, "categories": ["shopping", "delivery"]},
    {"id": "cf-hikenture-wagon", "name": "Hikenture Folding Wagon Cart", "category": "delivery", "description": "330 lbs capacity, 2X larger collapsible wagon for heavy deliveries.", "image": "https://customer-assets.emergentagent.com/job_rideheart/artifacts/sbu2evly_5.jpg", "price": "$129.99", "rating": "4.8", "reviews": "5.6k", "affiliateUrl": "https://www.amazon.com/dp/B08ZCRVK5Z?tag=thegigpulse-20", "likes": 0, "categories": ["shopping"]},
    {"id": "cf-samsonite-lumbar", "name": "Samsonite Lumbar Support Pillow", "category": "rideshare", "description": "Memory foam back support for long drives. Relieves lower back pain.", "image": "https://customer-assets.emergentagent.com/job_rideheart/artifacts/gobz84w8_6.jpg", "price": "$29.99", "rating": "4.5", "reviews": "15.2k", "affiliateUrl": "https://www.amazon.com/dp/B072K59NYZ?tag=thegigpulse-20", "likes": 0, "categories": ["rideshare", "delivery", "shopping"]},
    {"id": "cf-headlamp-light", "name": "Rechargeable LED Headlamp", "category": "delivery", "description": "Hands-free lighting for night deliveries. USB rechargeable with multiple modes.", "image": "https://customer-assets.emergentagent.com/job_rideheart/artifacts/7exu64l7_7.jpg", "price": "$19.99", "rating": "4.6", "reviews": "8.7k", "affiliateUrl": "https://www.amazon.com/dp/B0D412H2VX?tag=thegigpulse-20", "likes": 0, "categories": ["delivery", "shopping"]},
    {"id": "cf-dustbuster-vacuum", "name": "BLACK+DECKER Dustbuster Handheld Vacuum", "category": "rideshare", "description": "Cordless lithium hand vacuum for quick car cleanups between rides.", "image": "https://customer-assets.emergentagent.com/job_rideheart/artifacts/b30765dk_9.jpg", "price": "$49.99", "rating": "4.3", "reviews": "41.5k", "affiliateUrl": "https://www.amazon.com/dp/B01DAI5CF6?tag=thegigpulse-20", "likes": 0, "categories": ["rideshare", "shopping", "delivery"]},
    {"id": "cf-ozium-2pack", "name": "Ozium Air Sanitizer 3.5oz (2-Pack)", "category": "rideshare", "description": "Eliminates odors and sanitizes air. New Car Smell scent.", "image": "https://customer-assets.emergentagent.com/job_rideheart/artifacts/ob6akki5_11.jpg", "price": "$14.99", "rating": "4.7", "reviews": "28.5k", "affiliateUrl": "https://www.amazon.com/dp/B097QJZ5TV?tag=thegigpulse-20", "likes": 0, "categories": ["rideshare", "delivery", "shopping"]},
    {"id": "cf-ozium-6pack", "name": "Ozium Air Sanitizer 0.8oz (6-Pack)", "category": "rideshare", "description": "Travel-size air sanitizers. Perfect for keeping multiple in car, bag, and home.", "image": "https://customer-assets.emergentagent.com/job_rideheart/artifacts/t63m42s0_12.jpg", "price": "$19.99", "rating": "4.6", "reviews": "15.2k", "affiliateUrl": "https://www.amazon.com/dp/B088NNZ1YG?tag=thegigpulse-20", "likes": 0, "categories": ["rideshare", "shopping", "delivery"]},
    {"id": "cf-fortem-organizer", "name": "FORTEM Car Trunk Organizer", "category": "rideshare", "description": "Collapsible trunk storage with lid. Multiple compartments, waterproof base.", "image": "https://customer-assets.emergentagent.com/job_rideheart/artifacts/3gn0xkh7_13.jpg", "price": "$34.99", "rating": "4.5", "reviews": "19.8k", "affiliateUrl": "https://www.amazon.com/dp/B09QRKCYZS?tag=thegigpulse-20", "likes": 0, "categories": ["delivery", "shopping"]},
    {"id": "cf-anker-carcharger", "name": "Anker USB C Car Charger 40W", "category": "rideshare", "description": "Dual USB-C ports, PowerIQ 3.0 fast charging. Compact design.", "image": "https://customer-assets.emergentagent.com/job_rideheart/artifacts/ti768hlo_14.jpg", "price": "$17.99", "rating": "4.7", "reviews": "32.1k", "affiliateUrl": "https://www.amazon.com/dp/B0843SCLYH?tag=thegigpulse-20", "likes": 0, "categories": ["rideshare", "delivery", "shopping"]},
    {"id": "cf-esr-magsafe", "name": "ESR MagSafe Car Mount Charger", "category": "rideshare", "description": "Magnetic phone mount with wireless charging. Air vent clip included.", "image": "https://customer-assets.emergentagent.com/job_rideheart/artifacts/2yutz7t0_15.jpg", "price": "$39.99", "rating": "4.4", "reviews": "11.3k", "affiliateUrl": "https://www.amazon.com/dp/B08HNBHSQV?tag=thegigpulse-20", "likes": 0, "categories": ["rideshare", "shopping", "delivery"]},
    {"id": "cf-lamicall-mount", "name": "Lamicall Phone Mount for Car Vent", "category": "rideshare", "description": "Universal air vent phone holder with secure grip. 360 rotation.", "image": "https://customer-assets.emergentagent.com/job_rideheart/artifacts/vo8x0pxk_16.jpg", "price": "$15.99", "rating": "4.5", "reviews": "45.2k", "affiliateUrl": "https://www.amazon.com/dp/B0BHNYJGRF?tag=thegigpulse-20", "likes": 0, "categories": ["rideshare", "delivery", "shopping"]},
    {"id": "cf-vomit-bags", "name": "YGDZ Vomit Bags (24-Pack)", "category": "rideshare", "description": "Disposable emesis bags with twist ties. Essential for rideshare emergencies.", "image": "https://customer-assets.emergentagent.com/job_rideheart/artifacts/dtn792zw_17.jpg", "price": "$13.99", "rating": "4.6", "reviews": "8.9k", "affiliateUrl": "https://www.amazon.com/dp/B01LYBWJBC?tag=thegigpulse-20", "likes": 0, "categories": ["rideshare"]},
    {"id": "cf-chemicalguys-wipes", "name": "Chemical Guys Interior Cleaner Wipes (30ct)", "category": "rideshare", "description": "All-in-one interior wipes for dashboard, leather, vinyl, glass.", "image": "https://customer-assets.emergentagent.com/job_rideheart/artifacts/mv6bf8v3_18.jpg", "price": "$12.99", "rating": "4.4", "reviews": "6.7k", "affiliateUrl": "https://www.amazon.com/dp/B0DKQ2W13G?tag=thegigpulse-20", "likes": 0, "categories": ["rideshare", "shopping", "delivery"]}
]

async def seed_static_content():
    """Seed default static content if not exists in database"""
    collections_to_seed = [
        ("static_weekly_shows", DEFAULT_WEEKLY_SHOWS, "id"),
        ("static_featured_channels", DEFAULT_FEATURED_CHANNELS, "id"),
        ("static_gig_apps", DEFAULT_GIG_APPS, "id"),
        ("static_helpful_tools", DEFAULT_HELPFUL_TOOLS, "id"),
        ("static_featured_gear", DEFAULT_FEATURED_GEAR, "id"),
        ("static_community_favorites", DEFAULT_COMMUNITY_FAVORITES, "id"),
    ]
    
    for collection_name, default_data, id_field in collections_to_seed:
        collection = db[collection_name]
        logger.info(f"Syncing {collection_name} with {len(default_data)} items")
        for item in default_data:
            # Check if item exists and has a price that was manually changed
            existing = await collection.find_one({id_field: item[id_field]})
            if existing and 'price' in existing and 'price' in item:
                # Preserve manually set price
                item_to_set = {k: v for k, v in item.items() if k != 'price'}
                await collection.update_one(
                    {id_field: item[id_field]},
                    {"$set": item_to_set, "$setOnInsert": {"price": item.get("price")}},
                    upsert=True
                )
            else:
                await collection.update_one(
                    {id_field: item[id_field]},
                    {"$set": item},
                    upsert=True
                )

@static_content_router.get("/weekly-shows")
async def get_weekly_shows():
    """Get weekly shows from database, ordered by day of week"""
    items = await db.static_weekly_shows.find({}, {"_id": 0}).to_list(100)
    
    # Sort by day of week order
    day_order = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6, 'Sunday': 7}
    
    def get_day_order(show):
        schedule = show.get('schedule', '')
        for day, order in day_order.items():
            if day in schedule:
                return order
        return 99
    
    items.sort(key=get_day_order)
    return {"success": True, "data": items, "count": len(items)}

@static_content_router.get("/featured-channels")
async def get_static_featured_channels():
    """Get featured YouTube channels from database in specific order"""
    items = await db.static_featured_channels.find({}, {"_id": 0}).to_list(100)
    # Define explicit order
    order = {"fc-ridesharerodeo": 1, "fc-rideshareguy": 2, "fc-rideshareprof": 3}
    items.sort(key=lambda x: order.get(x.get("id"), 99))
    return {"success": True, "data": items, "count": len(items)}

@static_content_router.get("/gig-apps")
async def get_gig_apps():
    """Get gig apps from database"""
    items = await db.static_gig_apps.find({}, {"_id": 0}).to_list(100)
    return {"success": True, "data": items, "count": len(items)}

@static_content_router.get("/helpful-tools")
async def get_helpful_tools():
    """Get helpful tools from database in specific order"""
    items = await db.static_helpful_tools.find({}, {"_id": 0}).to_list(100)
    # Order: Gridwise, WorkSolo, Everlance, GigU, Mystro, Maxymo
    order = {"tool-gridwise": 1, "tool-worksolo": 2, "tool-everlance": 3, "tool-gigu": 4, "tool-mystro": 5, "tool-maxymo": 6}
    items.sort(key=lambda x: order.get(x.get("id"), 99))
    return {"success": True, "data": items, "count": len(items)}

@static_content_router.get("/featured-gear")
async def get_featured_gear():
    """Get featured gear/essentials from database in specific order"""
    items = await db.static_featured_gear.find({}, {"_id": 0}).to_list(100)
    # Order: REDTIGER, Fanttik, iOttie
    order = {"fg-redtiger": 1, "fg-fanttik": 2, "fg-iottie": 3}
    items.sort(key=lambda x: order.get(x.get("id"), 99))
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

# Price update model
class PriceUpdate(BaseModel):
    price: str

@static_content_router.put("/featured-gear/{item_id}/price")
async def update_featured_gear_price(item_id: str, price_update: PriceUpdate):
    """Update price for a featured gear item (admin function)"""
    result = await db.static_featured_gear.update_one(
        {"id": item_id},
        {"$set": {"price": price_update.price}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"success": True, "message": f"Price updated to {price_update.price}"}

@static_content_router.put("/community-favorites/{item_id}/price")
async def update_community_favorites_price(item_id: str, price_update: PriceUpdate):
    """Update price for a community favorites item (admin function)"""
    result = await db.static_community_favorites.update_one(
        {"id": item_id},
        {"$set": {"price": price_update.price}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"success": True, "message": f"Price updated to {price_update.price}"}

app.include_router(static_content_router)

# ============ Arena API Endpoints ============

# Driver Wins endpoints
@arena_router.get("/driver-wins")
async def get_driver_wins(limit: int = 50):
    """Get recent driver win trips (newest first)"""
    trips = await db.driver_wins.find({}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return {"success": True, "trips": trips}

@arena_router.post("/driver-wins")
async def create_driver_win(trip: DriverWinTripCreate):
    """Create a new driver win trip"""
    trip_dict = trip.dict()
    trip_dict["id"] = str(uuid.uuid4())
    trip_dict["fires"] = 1
    trip_dict["fired_by"] = []
    trip_dict["tip_updated"] = False
    trip_dict["created_at"] = datetime.now(timezone.utc)
    trip_dict["updated_at"] = None
    
    await db.driver_wins.insert_one(trip_dict)
    # Remove _id before returning
    trip_dict.pop("_id", None)
    return {"success": True, "trip": trip_dict}

@arena_router.put("/driver-wins/{trip_id}")
async def update_driver_win(trip_id: str, update: DriverWinTripUpdate):
    """Update a driver win trip (only owner can edit)"""
    existing = await db.driver_wins.find_one({"id": trip_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if existing.get("session_id") != update.session_id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this trip")
    
    update_dict = {k: v for k, v in update.dict().items() if v is not None and k != "session_id"}
    update_dict["updated_at"] = datetime.now(timezone.utc)
    
    # Check if tip was updated
    if "tip_amount" in update_dict or "total_amount" in update_dict:
        update_dict["tip_updated"] = True
    
    await db.driver_wins.update_one(
        {"id": trip_id},
        {"$set": update_dict}
    )
    
    updated = await db.driver_wins.find_one({"id": trip_id}, {"_id": 0})
    return {"success": True, "trip": updated}

@arena_router.post("/driver-wins/{trip_id}/fire")
async def fire_driver_win(trip_id: str, device_id: str):
    """Fire (upvote) a driver win trip"""
    existing = await db.driver_wins.find_one({"id": trip_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    fired_by = existing.get("fired_by", [])
    if device_id in fired_by:
        # Already fired, remove fire
        await db.driver_wins.update_one(
            {"id": trip_id},
            {"$pull": {"fired_by": device_id}, "$inc": {"fires": -1}}
        )
        action = "unfired"
    else:
        # Add fire
        await db.driver_wins.update_one(
            {"id": trip_id},
            {"$push": {"fired_by": device_id}, "$inc": {"fires": 1}}
        )
        action = "fired"
    
    updated = await db.driver_wins.find_one({"id": trip_id}, {"_id": 0})
    return {"success": True, "action": action, "fires": updated.get("fires", 1)}

@arena_router.delete("/driver-wins/{trip_id}")
async def delete_driver_win(trip_id: str, session_id: str):
    """Delete a driver win trip (only owner can delete)"""
    existing = await db.driver_wins.find_one({"id": trip_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if existing.get("session_id") != session_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this trip")
    
    await db.driver_wins.delete_one({"id": trip_id})
    return {"success": True}

# Live Pulse endpoints
@arena_router.get("/live-pulse/sessions")
async def get_live_pulse_sessions():
    """Get all live pulse sessions (live now and upcoming)"""
    now = datetime.now(timezone.utc)
    
    # Get live sessions
    live = await db.live_pulse_sessions.find(
        {"is_live": True}, 
        {"_id": 0, "host_key": 0}
    ).to_list(20)
    
    # Get upcoming sessions (not live, scheduled in future)
    upcoming = await db.live_pulse_sessions.find(
        {"is_live": False, "start_time": {"$gte": now}},
        {"_id": 0, "host_key": 0}
    ).sort("start_time", 1).to_list(20)
    
    return {"success": True, "live": live, "upcoming": upcoming}

@arena_router.get("/live-pulse/sessions/{session_id}")
async def get_live_pulse_session(session_id: str):
    """Get a specific live pulse session details"""
    session = await db.live_pulse_sessions.find_one({"id": session_id}, {"_id": 0, "host_key": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"success": True, "session": session}

@arena_router.post("/live-pulse/sessions")
async def create_live_pulse_session(session: LivePulseSessionCreate):
    """Create a new live pulse session"""
    session_dict = session.dict()
    session_dict["id"] = str(uuid.uuid4())
    session_dict["host_key"] = str(uuid.uuid4())[:8]  # Short secret key
    session_dict["is_live"] = False
    session_dict["total_earnings"] = 0
    session_dict["platform_breakdown"] = {}
    session_dict["trip_count"] = 0
    session_dict["created_at"] = datetime.now(timezone.utc)
    session_dict["updated_at"] = None
    
    await db.live_pulse_sessions.insert_one(session_dict)
    
    # Return with host_key for the creator
    session_dict.pop("_id", None)
    return {"success": True, "session": session_dict}

@arena_router.post("/live-pulse/sessions/{session_id}/go-live")
async def go_live(session_id: str, host_key: str):
    """Start a live session (host only)"""
    session = await db.live_pulse_sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.get("host_key") != host_key:
        raise HTTPException(status_code=403, detail="Invalid host key")
    
    await db.live_pulse_sessions.update_one(
        {"id": session_id},
        {"$set": {"is_live": True, "start_time": datetime.now(timezone.utc)}}
    )
    return {"success": True}

@arena_router.post("/live-pulse/sessions/{session_id}/end")
async def end_live(session_id: str, host_key: str):
    """End a live session (host only)"""
    session = await db.live_pulse_sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.get("host_key") != host_key:
        raise HTTPException(status_code=403, detail="Invalid host key")
    
    await db.live_pulse_sessions.update_one(
        {"id": session_id},
        {"$set": {"is_live": False, "end_time": datetime.now(timezone.utc)}}
    )
    return {"success": True}

@arena_router.post("/live-pulse/sessions/{session_id}/add-trip")
async def add_live_trip(session_id: str, trip: LivePulseTripAdd):
    """Add a trip to a live session (host only)"""
    session = await db.live_pulse_sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.get("host_key") != trip.host_key:
        raise HTTPException(status_code=403, detail="Invalid host key")
    
    # Update totals
    platform = trip.platform.lower()
    current_breakdown = session.get("platform_breakdown", {})
    current_breakdown[platform] = current_breakdown.get(platform, 0) + trip.amount
    
    await db.live_pulse_sessions.update_one(
        {"id": session_id},
        {
            "$inc": {"total_earnings": trip.amount, "trip_count": 1},
            "$set": {
                "platform_breakdown": current_breakdown,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    # Also log the individual trip
    trip_log = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "platform": platform,
        "amount": trip.amount,
        "base_pay": trip.base_pay,
        "tip_amount": trip.tip_amount,
        "note": trip.note,
        "created_at": datetime.now(timezone.utc)
    }
    await db.live_pulse_trips.insert_one(trip_log)
    
    updated = await db.live_pulse_sessions.find_one({"id": session_id}, {"_id": 0, "host_key": 0})
    return {"success": True, "session": updated}

# Host mode - verify host key
@arena_router.get("/live-pulse/host/{session_id}")
async def verify_host(session_id: str, key: str):
    """Verify host key for host mode access"""
    session = await db.live_pulse_sessions.find_one({"id": session_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.get("host_key") != key:
        raise HTTPException(status_code=403, detail="Invalid host key")
    
    # Return full session with host_key for host
    session.pop("_id", None)
    return {"success": True, "session": session, "is_host": True}

# Competitions endpoints
@arena_router.get("/competitions")
async def get_competitions(status: Optional[str] = None):
    """Get competitions"""
    query = {}
    if status:
        query["status"] = status
    
    competitions = await db.competitions.find(query, {"_id": 0}).sort("scheduled_time", 1).to_list(50)
    return {"success": True, "competitions": competitions}

@arena_router.post("/competitions")
async def create_competition(comp: CompetitionCreate):
    """Create a new competition (pending approval)"""
    comp_dict = comp.dict()
    comp_dict["id"] = str(uuid.uuid4())
    comp_dict["status"] = "pending"
    comp_dict["participants"] = []
    comp_dict["created_at"] = datetime.now(timezone.utc)
    
    await db.competitions.insert_one(comp_dict)
    comp_dict.pop("_id", None)
    return {"success": True, "competition": comp_dict}

@arena_router.post("/competitions/{comp_id}/approve")
async def approve_competition(comp_id: str):
    """Approve a competition (admin only)"""
    await db.competitions.update_one(
        {"id": comp_id},
        {"$set": {"status": "approved"}}
    )
    return {"success": True}

app.include_router(arena_router)

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
    # Arena indexes
    await db.driver_wins.create_index("id", unique=True)
    await db.driver_wins.create_index([("created_at", -1)])
    await db.live_pulse_sessions.create_index("id", unique=True)
    await db.live_pulse_sessions.create_index("is_live")
    await db.competitions.create_index("id", unique=True)
    await db.competitions.create_index([("scheduled_time", 1)])
    logger.info("Database indexes created")
    
    # Seed static content if empty
    await seed_static_content()
    logger.info("Static content seeded")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
