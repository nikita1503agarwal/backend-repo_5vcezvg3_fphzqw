"""
Database Schemas for Zenview Eyewear SaaS

Each Pydantic model corresponds to a MongoDB collection. The collection name
is the lowercase of the class name.
"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, HttpUrl

class Product(BaseModel):
    name: str = Field(..., description="Product display name")
    price: float = Field(..., ge=0, description="Price in USD")
    description: Optional[str] = Field(None, description="Short description")
    image: Optional[HttpUrl] = Field(None, description="Primary image URL")
    gallery: Optional[List[HttpUrl]] = Field(default_factory=list, description="Additional product images")

class Theme(BaseModel):
    accent: str = Field("#C2A676", description="Muted gold/beige accent color")
    background: str = Field("#FAFAF8", description="Soft white background")
    text: str = Field("#111111", description="Primary text color")
    serif: str = Field("'Playfair Display', serif", description="Serif font for headings")
    sans: str = Field("Inter, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, 'Helvetica Neue', Arial, 'Noto Sans', 'Apple Color Emoji', 'Segoe UI Emoji'", description="Sans font for body")

class Images(BaseModel):
    hero: Optional[HttpUrl] = None
    lifestyle: Optional[HttpUrl] = None
    closeup: Optional[HttpUrl] = None
    flatlay: Optional[HttpUrl] = None

class Sections(BaseModel):
    # Editable section content
    hero_title: str = Field("Zenview Eyewear", description="Main headline")
    hero_subtitle: str = Field("See Without Noise", description="Tagline")
    hero_cta: str = Field("Shop the Collection", description="Primary CTA")

    story_title: str = Field("Quiet Luxury, Considered Design", description="Story section heading")
    story_body: str = Field("Handcrafted eyewear balancing proportion, material and restraint.", description="Story copy")

    craft_title: str = Field("Craftsmanship & Materials", description="Craft section heading")
    craft_points: List[str] = Field(default_factory=lambda: [
        "Premium Italian acetate, hand-polished",
        "Anti-reflective Zeiss lenses",
        "Featherlight titanium hardware",
        "Precision-balanced comfort fit",
    ])

    lookbook_title: str = Field("Lookbook", description="Lookbook heading")

    testimonials: List[str] = Field(default_factory=lambda: [
        "Understated and impeccably made.",
        "The only frames I wear now.",
        "Pure, quiet confidence.",
    ])

    faqs: List[Dict[str, str]] = Field(default_factory=lambda: [
        {"q": "What makes Zenview different?", "a": "A focus on restraint, proportion and material honesty."},
        {"q": "Do you ship internationally?", "a": "Yes, we ship worldwide with premium tracked service."},
        {"q": "What is your return policy?", "a": "30-day returns in original condition for a full refund."},
    ])

class Project(BaseModel):
    name: str = Field("Zenview Eyewear", description="Project / brand name")
    description: Optional[str] = Field(None, description="Short description of the project")
    products: List[Product] = Field(default_factory=lambda: [
        Product(name="Aero 01", price=420.0, description="Sculptural acetate, balanced silhouette"),
        Product(name="Linea 02", price=460.0, description="Slim titanium, architectural lines"),
        Product(name="Shade 03", price=480.0, description="Deep lens profile, cinematic"),
    ])
    theme: Theme = Field(default_factory=Theme)
    sections: Sections = Field(default_factory=Sections)
    images: Images = Field(default_factory=Images)
    exported_html: Optional[str] = Field(None, description="Last exported HTML content")
    published_path: Optional[str] = Field(None, description="Relative path for hosted preview")
