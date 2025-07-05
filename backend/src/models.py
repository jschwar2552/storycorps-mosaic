"""Data models for Mosaic project"""
from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class Location(BaseModel):
    """Geographic location information"""
    region: Optional[str] = None  # State/Province
    country: Optional[str] = None
    locality: Optional[List[str]] = []  # City/Town
    
    @classmethod
    def from_api(cls, data: dict) -> "Location":
        """Create Location from StoryCorps API data"""
        return cls(
            region=data.get("region", [None])[0] if data.get("region") else None,
            country=data.get("country", [None])[0] if data.get("country") else None,
            locality=data.get("locality", [])
        )


class Participant(BaseModel):
    """Interview participant information"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    uuid: Optional[str] = None
    demographics: Dict[str, str] = Field(default_factory=dict)
    
    @property
    def full_name(self) -> str:
        """Get full name of participant"""
        parts = [p for p in [self.first_name, self.last_name] if p]
        return " ".join(parts) or "Anonymous"


class Interview(BaseModel):
    """StoryCorps interview data model"""
    id: int
    interview_id: str
    title: str
    description: str
    keywords: List[str] = Field(default_factory=list)
    location: Location
    participants: List[Participant] = Field(default_factory=list)
    audio_url: Optional[str] = None
    audio_length: Optional[int] = None  # Duration in seconds
    created_date: Optional[datetime] = None
    
    # Extracted demographics (to be filled by analysis)
    extracted_demographics: Dict[str, str] = Field(default_factory=dict)
    
    @classmethod
    def from_api(cls, data: dict) -> "Interview":
        """Create Interview from StoryCorps API response"""
        # Parse participants
        participants = []
        if data.get("additional_participants"):
            for p in data["additional_participants"]:
                participants.append(Participant(
                    first_name=p.get("first_name"),
                    last_name=p.get("last_name"),
                    uuid=p.get("uuid")
                ))
        
        # Parse audio URL
        audio_url = None
        audio_length = None
        if data.get("audio"):
            audio_url = data["audio"].get("url")
            audio_length = data["audio"].get("length")
        
        # Parse date
        created_date = None
        if data.get("created_date"):
            try:
                created_date = datetime.fromisoformat(data["created_date"].replace("Z", "+00:00"))
            except:
                pass
        
        return cls(
            id=data["id"],
            interview_id=data.get("interview_id", f"INT{data['id']}"),
            title=data.get("title", "Untitled"),
            description=data.get("description", ""),
            keywords=data.get("keywords", []),
            location=Location.from_api(data.get("location", {})),
            participants=participants,
            audio_url=audio_url,
            audio_length=audio_length,
            created_date=created_date
        )
    
    def get_themes(self) -> List[str]:
        """Get normalized themes from keywords"""
        # Normalize keywords to themes
        themes = []
        theme_mapping = {
            "family": ["family", "parent", "child", "mother", "father", "spouse"],
            "belonging": ["belonging", "community", "home", "identity"],
            "struggle": ["struggle", "hardship", "challenge", "overcome"],
            "hope": ["hope", "dream", "future", "aspiration"],
            "loss": ["loss", "grief", "death", "mourning"],
            "love": ["love", "romance", "relationship", "marriage"],
            "work": ["work", "career", "job", "profession"],
            "immigration": ["immigration", "immigrant", "migration", "journey"]
        }
        
        for keyword in self.keywords:
            keyword_lower = keyword.lower()
            for theme, related_words in theme_mapping.items():
                if any(word in keyword_lower for word in related_words):
                    if theme not in themes:
                        themes.append(theme)
        
        return themes


class UnityPattern(BaseModel):
    """Pattern of unity across demographics"""
    id: Optional[str] = None
    theme: str
    demographic_groups: List[str]
    unity_score: float = Field(ge=0.0, le=1.0)  # 0-1 score
    sample_stories: List[Interview] = Field(default_factory=list)
    sample_size: int = 0
    insights: str  # Claude's analysis
    discovered_date: datetime = Field(default_factory=datetime.now)
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.id:
            self.id = f"{self.theme}_{'-'.join(self.demographic_groups[:2])}_{self.discovered_date.strftime('%Y%m%d')}"


class StoryPair(BaseModel):
    """Curated pair of stories showing deep connections"""
    id: Optional[str] = None
    story_a: Interview
    story_b: Interview
    surface_differences: List[str] = Field(default_factory=list)
    deep_connections: List[str] = Field(default_factory=list)
    claude_analysis: str
    unity_score: float = Field(ge=0.0, le=1.0)
    curation_date: datetime = Field(default_factory=datetime.now)
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.id:
            self.id = f"pair_{self.story_a.id}_{self.story_b.id}"
    
    def get_demographic_contrast(self) -> Dict[str, tuple]:
        """Get demographic differences between stories"""
        contrasts = {}
        
        # Location contrast
        if self.story_a.location.region != self.story_b.location.region:
            contrasts["location"] = (
                self.story_a.location.region or "Unknown",
                self.story_b.location.region or "Unknown"
            )
        
        # Add more demographic contrasts as we extract them
        
        return contrasts


class PatternQuery(BaseModel):
    """Query parameters for finding unity patterns"""
    theme: str
    demographics: List[Dict[str, str]]
    sample_size: str = "adaptive"  # "adaptive" or specific number
    min_stories_per_group: int = 10
    max_stories_per_group: int = 50