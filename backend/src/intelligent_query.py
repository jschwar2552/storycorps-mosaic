"""Intelligent query system for finding patterns in StoryCorps data"""
import asyncio
from typing import List, Dict, Optional, Set
from collections import defaultdict
import httpx
from datetime import datetime

from .models import Interview, Location, PatternQuery
from .rate_limiting import AdaptiveRateLimiter


class IntelligentQuerySystem:
    """Smart querying system that finds patterns without downloading everything"""
    
    def __init__(self, base_url: str = "https://archive.storycorps.org"):
        self.base_url = base_url
        self.api_endpoint = f"{base_url}/wp-json/storycorps/v1/interviews"
        self.rate_limiter = AdaptiveRateLimiter(base_rate=10, max_rate=40)
        self.headers = {
            "User-Agent": "Mosaic/1.0 (Finding human connections)",
            "Accept": "application/json"
        }
        
        # Cache for avoiding duplicate queries
        self.query_cache: Dict[str, List[Interview]] = {}
        self.keyword_stats: Dict[str, int] = defaultdict(int)
    
    async def analyze_keyword_distribution(self, sample_size: int = 100) -> Dict[str, int]:
        """Analyze keyword frequency in a sample to find promising themes"""
        print(f"Analyzing keyword distribution (sample size: {sample_size})...")
        
        async with httpx.AsyncClient() as client:
            # Fetch sample pages
            interviews = []
            page = 1
            
            while len(interviews) < sample_size:
                response = await self.rate_limiter.execute(
                    client.get,
                    self.api_endpoint,
                    params={"per_page": 10, "page": page},
                    headers=self.headers,
                    timeout=15.0
                )
                
                if response.status_code != 200:
                    break
                
                data = response.json()
                if not data:
                    break
                
                for item in data:
                    interviews.append(Interview.from_api(item))
                
                page += 1
                
                # Progress update
                if len(interviews) % 50 == 0:
                    print(f"  Analyzed {len(interviews)} interviews...")
            
            # Count keywords
            keyword_counts = defaultdict(int)
            theme_counts = defaultdict(int)
            
            for interview in interviews:
                for keyword in interview.keywords:
                    keyword_counts[keyword.lower()] += 1
                
                for theme in interview.get_themes():
                    theme_counts[theme] += 1
            
            print(f"\nTop themes found:")
            for theme, count in sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  - {theme}: {count} occurrences")
            
            self.keyword_stats = dict(keyword_counts)
            return dict(theme_counts)
    
    async def find_demographic_intersections(self, theme: str, limit: int = 50) -> Dict[str, List[Interview]]:
        """Find interviews with specific theme across different demographics"""
        print(f"\nFinding demographic intersections for theme: '{theme}'")
        
        demographic_groups = defaultdict(list)
        
        async with httpx.AsyncClient() as client:
            # Search for interviews with this theme
            page = 1
            total_found = 0
            
            while total_found < limit:
                # Query by iterating through pages (since we can't search by keyword directly)
                response = await self.rate_limiter.execute(
                    client.get,
                    self.api_endpoint,
                    params={"per_page": 10, "page": page},
                    headers=self.headers,
                    timeout=15.0
                )
                
                if response.status_code != 200:
                    break
                
                data = response.json()
                if not data:
                    break
                
                # Filter for theme
                for item in data:
                    interview = Interview.from_api(item)
                    
                    if theme in [t.lower() for t in interview.get_themes()]:
                        # Categorize by location
                        location_key = self._get_location_key(interview.location)
                        demographic_groups[location_key].append(interview)
                        total_found += 1
                
                page += 1
                
                # Stop if we have enough diversity
                if len(demographic_groups) >= 4 and all(len(v) >= 3 for v in demographic_groups.values()):
                    break
            
            print(f"\nFound {total_found} interviews across {len(demographic_groups)} demographic groups:")
            for group, interviews in demographic_groups.items():
                print(f"  - {group}: {len(interviews)} interviews")
            
            return dict(demographic_groups)
    
    def _get_location_key(self, location: Location) -> str:
        """Create demographic key from location"""
        # Simple demographic categorization based on location
        # In a real system, we'd extract more demographics from descriptions
        
        if not location.region:
            return "unknown"
        
        region = location.region.lower()
        
        # Rough categorization (would be more sophisticated in production)
        urban_regions = ["new york", "california", "illinois", "massachusetts"]
        rural_regions = ["iowa", "montana", "wyoming", "vermont", "alaska"]
        
        if any(ur in region for ur in urban_regions):
            return f"urban_{region}"
        elif any(rr in region for rr in rural_regions):
            return f"rural_{region}"
        else:
            return f"mixed_{region}"
    
    async def find_story_pairs(self, theme: str, min_contrast: float = 0.7) -> List[tuple]:
        """Find pairs of stories with high demographic contrast but similar themes"""
        print(f"\nSearching for story pairs on theme: '{theme}'")
        
        # Get stories across demographics
        demographic_groups = await self.find_demographic_intersections(theme, limit=100)
        
        pairs = []
        
        # Find contrasting pairs
        group_names = list(demographic_groups.keys())
        for i in range(len(group_names)):
            for j in range(i + 1, len(group_names)):
                group_a = group_names[i]
                group_b = group_names[j]
                
                # Check if groups are contrasting enough
                if self._calculate_demographic_contrast(group_a, group_b) >= min_contrast:
                    # Find best matching stories
                    for story_a in demographic_groups[group_a][:5]:
                        for story_b in demographic_groups[group_b][:5]:
                            if self._stories_share_emotional_core(story_a, story_b):
                                pairs.append((story_a, story_b))
                                
                                if len(pairs) >= 10:  # Limit pairs
                                    break
        
        print(f"Found {len(pairs)} potential story pairs")
        return pairs
    
    def _calculate_demographic_contrast(self, group_a: str, group_b: str) -> float:
        """Calculate how different two demographic groups are"""
        # Simple heuristic - would be more sophisticated in production
        if ("urban" in group_a and "rural" in group_b) or ("rural" in group_a and "urban" in group_b):
            return 0.9
        elif group_a.split("_")[1] != group_b.split("_")[1]:  # Different states
            return 0.7
        else:
            return 0.3
    
    def _stories_share_emotional_core(self, story_a: Interview, story_b: Interview) -> bool:
        """Check if two stories share emotional themes"""
        # Look for overlapping keywords beyond the main theme
        keywords_a = set(k.lower() for k in story_a.keywords)
        keywords_b = set(k.lower() for k in story_b.keywords)
        
        emotional_keywords = {
            "love", "loss", "hope", "fear", "joy", "struggle",
            "family", "belonging", "identity", "growth", "change"
        }
        
        shared_emotional = keywords_a.intersection(keywords_b).intersection(emotional_keywords)
        
        return len(shared_emotional) >= 2
    
    async def adaptive_sampling(self, pattern_query: PatternQuery) -> List[Interview]:
        """Adaptively sample interviews until we have enough for pattern analysis"""
        print(f"\nAdaptive sampling for pattern: {pattern_query.theme}")
        
        collected_interviews = []
        demographic_counts = defaultdict(int)
        
        async with httpx.AsyncClient() as client:
            page = 1
            attempts = 0
            max_attempts = 50  # Prevent infinite loops
            
            while attempts < max_attempts:
                # Check if we have enough samples
                if self._have_sufficient_samples(demographic_counts, pattern_query):
                    break
                
                # Fetch more interviews
                response = await self.rate_limiter.execute(
                    client.get,
                    self.api_endpoint,
                    params={"per_page": 10, "page": page},
                    headers=self.headers,
                    timeout=15.0
                )
                
                if response.status_code != 200:
                    break
                
                data = response.json()
                if not data:
                    break
                
                # Process interviews
                for item in data:
                    interview = Interview.from_api(item)
                    
                    # Check if matches our pattern query
                    if self._matches_pattern_query(interview, pattern_query):
                        collected_interviews.append(interview)
                        demo_key = self._get_location_key(interview.location)
                        demographic_counts[demo_key] += 1
                
                page += 1
                attempts += 1
                
                # Progress update
                if len(collected_interviews) % 20 == 0:
                    print(f"  Collected {len(collected_interviews)} matching interviews...")
        
        print(f"\nAdaptive sampling complete:")
        print(f"  Total interviews collected: {len(collected_interviews)}")
        print(f"  Demographic distribution: {dict(demographic_counts)}")
        
        return collected_interviews
    
    def _have_sufficient_samples(self, demographic_counts: Dict[str, int], 
                                pattern_query: PatternQuery) -> bool:
        """Check if we have enough samples for meaningful analysis"""
        if pattern_query.sample_size != "adaptive":
            total = sum(demographic_counts.values())
            return total >= int(pattern_query.sample_size)
        
        # For adaptive sampling, ensure minimum diversity
        if len(demographic_counts) < 2:
            return False
        
        # Each group should have minimum samples
        for count in demographic_counts.values():
            if count < pattern_query.min_stories_per_group:
                return False
        
        # Don't collect too many
        if any(count > pattern_query.max_stories_per_group for count in demographic_counts.values()):
            return True
        
        return len(demographic_counts) >= 3  # At least 3 different groups
    
    def _matches_pattern_query(self, interview: Interview, pattern_query: PatternQuery) -> bool:
        """Check if interview matches the pattern query criteria"""
        # Check theme match
        interview_themes = [t.lower() for t in interview.get_themes()]
        if pattern_query.theme.lower() not in interview_themes:
            return False
        
        # Check demographic match (simplified for now)
        # In production, would extract demographics from description using NLP
        location_key = self._get_location_key(interview.location)
        
        for demo_filter in pattern_query.demographics:
            if "location" in demo_filter:
                if demo_filter["location"] in location_key:
                    return True
        
        return len(pattern_query.demographics) == 0  # If no demographic filters, accept all