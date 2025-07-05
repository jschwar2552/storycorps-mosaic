"""Mock StoryCorps API for testing rate limiting and data collection"""
import asyncio
import json
import random
import time
from datetime import datetime
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

# Rate limiting state
request_counts: Dict[str, List[float]] = {}
RATE_LIMIT = 30  # 30 requests per second (we'll test finding this limit)

# Sample story data
SAMPLE_STORIES = [
    {
        "id": f"story_{i}",
        "title": f"Story {i}: {theme}",
        "participants": [
            {
                "name": f"Person {i}",
                "age": random.randint(18, 90),
                "location": random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
                "background": random.choice(["Urban", "Rural", "Suburban", "International"])
            }
        ],
        "themes": [theme, random.choice(["family", "love", "struggle", "hope"])],
        "transcript": f"This is a story about {theme}. " * 50,
        "recorded_date": datetime.now().isoformat(),
        "duration": random.randint(300, 1800),
        "keywords": [theme, "life", "experience", "memory"]
    }
    for i, theme in enumerate(["immigration", "family", "love", "loss", "identity", 
                               "community", "resilience", "culture", "tradition",
                               "struggle", "achievement", "memory", "hope"] * 10)
]


def check_rate_limit(client_ip: str) -> bool:
    """Check if client has exceeded rate limit"""
    now = time.time()
    
    # Clean old requests
    if client_ip in request_counts:
        request_counts[client_ip] = [t for t in request_counts[client_ip] if now - t < 1.0]
    else:
        request_counts[client_ip] = []
    
    # Check rate
    if len(request_counts[client_ip]) >= RATE_LIMIT:
        return False
    
    # Record request
    request_counts[client_ip].append(now)
    return True


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to all requests"""
    client_ip = request.client.host or "127.0.0.1"
    
    if not check_rate_limit(client_ip):
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded"},
            headers={
                "X-RateLimit-Limit": str(RATE_LIMIT),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time()) + 1)
            }
        )
    
    response = await call_next(request)
    
    # Add rate limit headers
    remaining = RATE_LIMIT - len(request_counts.get(client_ip, []))
    response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    
    return response


@app.get("/wp-json/storycorps/v1/interviews")
async def list_interviews(
    page: int = 1,
    per_page: int = 10,
    search: Optional[str] = None,
    theme: Optional[str] = None
):
    """List interviews with pagination"""
    # Simulate processing delay
    await asyncio.sleep(random.uniform(0.01, 0.05))
    
    # Filter stories
    filtered_stories = SAMPLE_STORIES
    
    if search:
        filtered_stories = [s for s in filtered_stories if search.lower() in s["title"].lower()]
    
    if theme:
        filtered_stories = [s for s in filtered_stories if theme in s["themes"]]
    
    # Paginate
    start = (page - 1) * per_page
    end = start + per_page
    page_stories = filtered_stories[start:end]
    
    return {
        "data": page_stories,
        "meta": {
            "total": len(filtered_stories),
            "page": page,
            "per_page": per_page,
            "total_pages": (len(filtered_stories) + per_page - 1) // per_page
        }
    }


@app.get("/wp-json/storycorps/v1/interviews/{story_id}")
async def get_interview(story_id: str):
    """Get single interview details"""
    # Simulate processing delay
    await asyncio.sleep(random.uniform(0.01, 0.05))
    
    # Find story
    story = next((s for s in SAMPLE_STORIES if s["id"] == story_id), None)
    
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    
    return story


@app.get("/wp-json/storycorps/v1/search")
async def search_interviews(
    q: str,
    limit: int = 10,
    offset: int = 0
):
    """Search interviews"""
    # Simulate processing delay
    await asyncio.sleep(random.uniform(0.02, 0.08))
    
    # Simple search
    results = []
    for story in SAMPLE_STORIES:
        if (q.lower() in story["title"].lower() or 
            q.lower() in story["transcript"].lower() or
            any(q.lower() in theme for theme in story["themes"])):
            results.append(story)
    
    return {
        "results": results[offset:offset + limit],
        "total": len(results),
        "query": q
    }


@app.get("/api/stats")
async def get_stats():
    """Get API statistics for testing"""
    return {
        "rate_limit": RATE_LIMIT,
        "active_clients": len(request_counts),
        "total_stories": len(SAMPLE_STORIES)
    }


@app.post("/api/reset")
async def reset_rate_limits():
    """Reset rate limits for testing"""
    request_counts.clear()
    return {"status": "reset"}


if __name__ == "__main__":
    print("Starting Mock StoryCorps API on http://localhost:8001")
    print(f"Rate limit: {RATE_LIMIT} requests/second")
    print(f"Total stories: {len(SAMPLE_STORIES)}")
    uvicorn.run(app, host="0.0.0.0", port=8001)