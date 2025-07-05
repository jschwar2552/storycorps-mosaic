"""Pattern discovery system using Claude for deep analysis"""
import os
from typing import List, Dict, Optional
from datetime import datetime
import json
import asyncio

# Try to import anthropic
try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    AsyncAnthropic = None

from .models import Interview, UnityPattern, StoryPair, PatternQuery
from .intelligent_query import IntelligentQuerySystem


class PatternDiscoveryEngine:
    """Discovers unity patterns and story pairs using Claude's analysis"""
    
    def __init__(self, anthropic_api_key: Optional[str] = None):
        self.api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if ANTHROPIC_AVAILABLE and self.api_key:
            self.client = AsyncAnthropic(api_key=self.api_key)
        else:
            self.client = None
            if not ANTHROPIC_AVAILABLE:
                print("⚠️  Anthropic module not installed. Install with: pip install anthropic")
        
        self.query_system = IntelligentQuerySystem()
        
        # Cache for Claude's insights
        self.pattern_cache: Dict[str, UnityPattern] = {}
        self.pair_cache: Dict[str, StoryPair] = {}
    
    async def discover_unity_pattern(self, theme: str, sample_size: str = "adaptive") -> UnityPattern:
        """Discover unity patterns for a specific theme across demographics"""
        
        # Create pattern query
        pattern_query = PatternQuery(
            theme=theme,
            demographics=[],  # Let system find diverse demographics
            sample_size=sample_size
        )
        
        # Get interviews using intelligent sampling
        interviews = await self.query_system.adaptive_sampling(pattern_query)
        
        if len(interviews) < 10:
            print(f"Warning: Only found {len(interviews)} interviews for theme '{theme}'")
        
        # Group by demographics
        demographic_groups = {}
        for interview in interviews:
            demo_key = self.query_system._get_location_key(interview.location)
            if demo_key not in demographic_groups:
                demographic_groups[demo_key] = []
            demographic_groups[demo_key].append(interview)
        
        # Have Claude analyze the pattern
        unity_score, insights = await self._analyze_unity_pattern(theme, demographic_groups)
        
        # Create pattern object
        pattern = UnityPattern(
            theme=theme,
            demographic_groups=list(demographic_groups.keys()),
            unity_score=unity_score,
            sample_stories=interviews[:10],  # Keep sample of stories
            sample_size=len(interviews),
            insights=insights
        )
        
        # Cache the pattern
        self.pattern_cache[pattern.id] = pattern
        
        return pattern
    
    async def _analyze_unity_pattern(self, theme: str, 
                                   demographic_groups: Dict[str, List[Interview]]) -> tuple[float, str]:
        """Use Claude to analyze unity patterns across demographic groups"""
        
        # Prepare data for Claude
        analysis_prompt = f"""Analyze these StoryCorps interviews about "{theme}" from different demographic groups.
        
Your task is to:
1. Identify the common human experiences that unite these different groups
2. Rate the unity score from 0.0 to 1.0 (where 1.0 means the theme completely transcends demographics)
3. Provide insights about what connects these diverse perspectives

Here are sample stories from each demographic group:

"""
        
        for group_name, interviews in demographic_groups.items():
            analysis_prompt += f"\n{group_name.upper()}:\n"
            
            # Include 2-3 stories per group
            for interview in interviews[:3]:
                analysis_prompt += f"\nTitle: {interview.title}\n"
                analysis_prompt += f"Description: {interview.description[:300]}...\n"
                analysis_prompt += f"Keywords: {', '.join(interview.keywords[:5])}\n"
                analysis_prompt += "-" * 40 + "\n"
        
        analysis_prompt += """
Please respond with:
1. UNITY_SCORE: [0.0-1.0]
2. COMMON_THREADS: List the specific experiences/emotions that appear across all groups
3. INSIGHTS: A paragraph explaining what makes this theme universal despite surface differences
4. SURPRISING_CONNECTIONS: Any unexpected similarities between contrasting groups
"""
        
        # Call Claude
        response = await self.client.messages.create(
            model="claude-3-haiku-20240307",  # Using Haiku for cost efficiency
            max_tokens=1000,
            temperature=0.7,
            messages=[{
                "role": "user",
                "content": analysis_prompt
            }]
        )
        
        # Parse Claude's response
        response_text = response.content[0].text
        
        # Extract unity score (simple parsing - would be more robust in production)
        unity_score = 0.7  # Default
        if "UNITY_SCORE:" in response_text:
            try:
                score_line = [line for line in response_text.split('\n') if "UNITY_SCORE:" in line][0]
                unity_score = float(score_line.split(":")[-1].strip())
            except:
                pass
        
        return unity_score, response_text
    
    async def find_powerful_story_pair(self, theme: str) -> Optional[StoryPair]:
        """Find a powerful story pair that shows unity across difference"""
        
        # Get potential pairs
        pairs = await self.query_system.find_story_pairs(theme)
        
        if not pairs:
            print(f"No story pairs found for theme '{theme}'")
            return None
        
        # Have Claude analyze the best pair
        best_pair = None
        best_score = 0
        
        for story_a, story_b in pairs[:5]:  # Analyze top 5 pairs
            pair_analysis = await self._analyze_story_pair(story_a, story_b)
            
            if pair_analysis.unity_score > best_score:
                best_score = pair_analysis.unity_score
                best_pair = pair_analysis
        
        if best_pair:
            self.pair_cache[best_pair.id] = best_pair
        
        return best_pair
    
    async def _analyze_story_pair(self, story_a: Interview, story_b: Interview) -> StoryPair:
        """Use Claude to deeply analyze a story pair"""
        
        analysis_prompt = f"""Analyze these two StoryCorps interviews to find deep human connections despite surface differences.

STORY A:
Title: {story_a.title}
Location: {story_a.location.region or 'Unknown'}, {story_a.location.country or 'Unknown'}
Description: {story_a.description}
Keywords: {', '.join(story_a.keywords)}

STORY B:
Title: {story_b.title}
Location: {story_b.location.region or 'Unknown'}, {story_b.location.country or 'Unknown'}
Description: {story_b.description}
Keywords: {', '.join(story_b.keywords)}

Please analyze:
1. SURFACE_DIFFERENCES: List 3-5 obvious differences (location, age, background, etc.)
2. DEEP_CONNECTIONS: List 3-5 profound similarities in their human experience
3. UNITY_SCORE: Rate 0.0-1.0 how powerfully these stories connect across difference
4. ANALYSIS: Write 2-3 paragraphs explaining why these stories show our shared humanity

Focus on emotional resonance, shared struggles, common hopes, and universal human experiences.
"""
        
        response = await self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1500,
            temperature=0.7,
            messages=[{
                "role": "user",
                "content": analysis_prompt
            }]
        )
        
        response_text = response.content[0].text
        
        # Parse response (simplified - would be more robust in production)
        surface_differences = []
        deep_connections = []
        unity_score = 0.75
        
        # Extract sections
        lines = response_text.split('\n')
        current_section = None
        
        for line in lines:
            if "SURFACE_DIFFERENCES:" in line:
                current_section = "surface"
            elif "DEEP_CONNECTIONS:" in line:
                current_section = "deep"
            elif "UNITY_SCORE:" in line:
                try:
                    unity_score = float(line.split(":")[-1].strip())
                except:
                    pass
                current_section = None
            elif "ANALYSIS:" in line:
                current_section = "analysis"
            elif current_section == "surface" and line.strip().startswith("-"):
                surface_differences.append(line.strip("- "))
            elif current_section == "deep" and line.strip().startswith("-"):
                deep_connections.append(line.strip("- "))
        
        # Create story pair
        return StoryPair(
            story_a=story_a,
            story_b=story_b,
            surface_differences=surface_differences[:5],
            deep_connections=deep_connections[:5],
            claude_analysis=response_text,
            unity_score=unity_score
        )
    
    async def discover_macro_patterns(self, themes: Optional[List[str]] = None) -> Dict[str, UnityPattern]:
        """Discover macro patterns across multiple themes"""
        
        if not themes:
            # Use most common themes
            theme_counts = await self.query_system.analyze_keyword_distribution()
            themes = list(theme_counts.keys())[:10]
        
        patterns = {}
        
        for theme in themes:
            print(f"\nDiscovering pattern for theme: {theme}")
            try:
                pattern = await self.discover_unity_pattern(theme)
                patterns[theme] = pattern
                
                # Save pattern to file for caching
                with open(f"patterns/pattern_{theme}.json", "w") as f:
                    json.dump(pattern.dict(), f, indent=2, default=str)
                
            except Exception as e:
                print(f"Error discovering pattern for {theme}: {e}")
                continue
            
            # Small delay between themes
            await asyncio.sleep(2)
        
        return patterns
    
    def get_unity_dashboard_data(self) -> Dict:
        """Get data formatted for the unity dashboard"""
        
        dashboard_data = {
            "patterns": [],
            "theme_connections": {},
            "demographic_bridges": [],
            "unity_scores": {}
        }
        
        for pattern in self.pattern_cache.values():
            dashboard_data["patterns"].append({
                "theme": pattern.theme,
                "unity_score": pattern.unity_score,
                "sample_size": pattern.sample_size,
                "demographics": pattern.demographic_groups,
                "insights": pattern.insights[:200] + "..."  # Truncate for dashboard
            })
            
            dashboard_data["unity_scores"][pattern.theme] = pattern.unity_score
        
        # Find demographic bridges (themes that connect different groups)
        for pattern in self.pattern_cache.values():
            if pattern.unity_score > 0.8 and len(pattern.demographic_groups) > 2:
                dashboard_data["demographic_bridges"].append({
                    "theme": pattern.theme,
                    "groups": pattern.demographic_groups,
                    "score": pattern.unity_score
                })
        
        return dashboard_data