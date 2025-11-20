import os
import io
import zipfile
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from bson.objectid import ObjectId

from database import db, create_document, get_documents
from schemas import Project, Product

app = FastAPI(title="Zenview Eyewear Builder")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helpers

def to_collection_name(cls_name: str) -> str:
    return cls_name.lower()

# API Models
class CreateProjectRequest(BaseModel):
    project: Project

class UpdateProjectRequest(BaseModel):
    id: str
    project: Project

class ImageGenRequest(BaseModel):
    type: str  # hero | lifestyle | closeup | flatlay
    prompt: Optional[str] = None

# Routes
@app.get("/")
def root():
    return {"brand": "Zenview Eyewear", "tagline": "See Without Noise"}

@app.get("/test")
def test_database():
    status = {
        "backend": "running",
        "database": "disconnected",
        "collections": []
    }
    try:
        if db is not None:
            status["database"] = "connected"
            status["collections"] = db.list_collection_names()
    except Exception as e:
        status["error"] = str(e)
    return status

@app.post("/api/projects")
def create_project(payload: CreateProjectRequest):
    try:
        project = payload.project
        collection = to_collection_name(Project.__name__)
        _id = create_document(collection, project)
        return {"id": _id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects")
def list_projects():
    try:
        collection = to_collection_name(Project.__name__)
        docs = get_documents(collection)
        for d in docs:
            d["id"] = str(d.pop("_id"))
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}")
def get_project(project_id: str):
    try:
        collection = to_collection_name(Project.__name__)
        docs = db[collection].find_one({"_id": ObjectId(project_id)})
        if not docs:
            raise HTTPException(status_code=404, detail="Project not found")
        docs["id"] = str(docs.pop("_id"))
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/projects/{project_id}")
def update_project(project_id: str, payload: UpdateProjectRequest):
    try:
        collection = to_collection_name(Project.__name__)
        # Ensure ids match
        if project_id != payload.id:
            raise HTTPException(status_code=400, detail="Mismatched ids")
        data = payload.project.model_dump()
        db[collection].update_one({"_id": ObjectId(project_id)}, {"$set": data})
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Simple Nano Banana integration placeholder
# This endpoint returns a pseudo URL and stored prompt for now
PREDEFINED_PROMPTS = {
    "hero": "Ultra realistic luxury sunglasses on a clean marble pedestal, soft natural light, shallow depth of field, premium editorial look, elegant reflections, crisp shadows, shot on a high end camera, photorealistic.",
    "lifestyle": "Fashion model wearing premium sunglasses in a modern European street, soft cinematic light, neutral tones, quiet luxury styling.",
    "closeup": "Macro shot of handcrafted acetate sunglasses hinge and lens edge, extremely realistic textures, high detail, crisp reflections.",
    "flatlay": "Minimalist flat lay of three premium eyewear frames on concrete or marble, balanced shadows and clean composition.",
}

@app.post("/api/generate-image")
def generate_image(req: ImageGenRequest):
    # Here you'd call Nano Banana API. For this environment, we'll return a placeholder URL
    prompt = req.prompt or PREDEFINED_PROMPTS.get(req.type, "")
    # Use a neutral placeholder with text params
    url = f"https://placehold.co/1600x900/png?text=Zenview+{req.type.title()}"
    return {"type": req.type, "prompt": prompt, "url": url}

# Export HTML/CSS/JS for Shopify or static hosting
@app.get("/api/projects/{project_id}/export.zip")
async def export_project_zip(project_id: str):
    try:
        collection = to_collection_name(Project.__name__)
        project = db[collection].find_one({"_id": ObjectId(project_id)})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        html, css, js = build_export_bundle(project)

        memfile = io.BytesIO()
        with zipfile.ZipFile(memfile, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("index.html", html)
            zf.writestr("styles.css", css)
            zf.writestr("main.js", js)
        memfile.seek(0)

        return StreamingResponse(memfile, media_type="application/zip", headers={
            "Content-Disposition": f"attachment; filename=zenview-{project_id}.zip"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Helper to craft premium minimal export

def build_export_bundle(project: dict):
    theme = project.get("theme", {})
    sections = project.get("sections", {})
    products = project.get("products", [])
    images = project.get("images", {})

    accent = theme.get("accent", "#C2A676")

    html = f"""<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\" />
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
<title>Zenview Eyewear</title>
<link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">
<link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>
<link href=\"https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600&family=Inter:wght@300;400;500;600&display=swap\" rel=\"stylesheet\">
<link rel=\"stylesheet\" href=\"./styles.css\" />
</head>
<body>
<header class=\"nav\">
  <div class=\"nav-inner\">
    <div class=\"brand\">Zenview</div>
    <nav>
      <a href=\"#collections\">Collections</a>
      <a href=\"#story\">Story</a>
      <a href=\"#craft\">Craft</a>
      <a href=\"#lookbook\">Lookbook</a>
      <a href=\"#faq\">FAQ</a>
    </nav>
  </div>
</header>
<section class=\"hero\">
  <div class=\"hero-content\">
    <h1>{sections.get('hero_title', 'Zenview Eyewear')}</h1>
    <p class=\"sub\">{sections.get('hero_subtitle', 'See Without Noise')}</p>
    <a class=\"cta\" href=\"#collections\">{sections.get('hero_cta', 'Shop the Collection')}</a>
  </div>
  <div class=\"hero-media\" style=\"background-image:url('{images.get('hero') or 'https://placehold.co/1600x900?text=Zenview+Hero'}')\"></div>
</section>
<section id=\"collections\" class=\"collections\">
  <h2>Signature Collection</h2>
  <div class=\"grid\">
    {''.join([f"<div class='card'><div class='img' style=\\\"background-image:url('{(p.get('image') or 'https://placehold.co/800x600?text=Frame')}')\\\"></div><div class='info'><div class='name'>{p.get('name')}</div><div class='price'>$ {p.get('price')}</div></div></div>" for p in products])}
  </div>
</section>
<section id=\"story\" class=\"story\">
  <div class=\"split\">
    <div class=\"image\" style=\"background-image:url('{images.get('lifestyle') or 'https://placehold.co/1200x1400?text=Lifestyle'}')\"></div>
    <div class=\"copy\">
      <h3>{sections.get('story_title')}</h3>
      <p>{sections.get('story_body')}</p>
    </div>
  </div>
</section>
<section id=\"craft\" class=\"craft\">
  <h2>{sections.get('craft_title')}</h2>
  <div class=\"features\">
    {''.join([f"<div class='feat'><div class='dot'></div><p>{pt}</p></div>" for pt in sections.get('craft_points', [])])}
  </div>
</section>
<section id=\"lookbook\" class=\"lookbook\">
  <h2>{sections.get('lookbook_title')}</h2>
  <div class=\"masonry\">
    <img src=\"{images.get('lifestyle') or 'https://placehold.co/800x1000'}\" />
    <img src=\"{images.get('flatlay') or 'https://placehold.co/1000x800'}\" />
    <img src=\"{images.get('closeup') or 'https://placehold.co/900x900'}\" />
  </div>
</section>
<section id=\"testimonials\" class=\"testimonials\">
  {''.join([f"<blockquote>\u201C{t}\u201D</blockquote>" for t in sections.get('testimonials', [])])}
</section>
<section id=\"faq\" class=\"faq\">
  {''.join([f"<details><summary>{f.get('q')}</summary><p>{f.get('a')}</p></details>" for f in sections.get('faqs', [])])}
</section>
<footer class=\"footer\">
  <div class=\"inner\">
    <div class=\"blurb\">Zenview Eyewear — {sections.get('hero_subtitle')}</div>
    <form class=\"newsletter\"><input type=\"email\" placeholder=\"Email\"/><button>Join</button></form>
  </div>
</footer>
<script src=\"./main.js\"></script>
</body>
</html>"""

    css = f""":root{{--accent:{accent};--bg:#FAFAF8;--text:#111;--muted:#9A8C71}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font-family:Inter,system-ui;-webkit-font-smoothing:antialiased;}}
.nav{{position:sticky;top:0;background:rgba(250,250,248,.7);backdrop-filter:saturate(180%) blur(16px);border-bottom:1px solid rgba(0,0,0,.06);z-index:10}}
.nav-inner{{max-width:1200px;margin:0 auto;display:flex;justify-content:space-between;align-items:center;padding:16px 24px}}
.nav a{{color:#333;text-decoration:none;margin-left:20px;font-size:14px}}
.brand{{font-family:'Playfair Display',serif;font-size:20px;letter-spacing:.05em}}
.hero{{display:grid;grid-template-columns:1.1fr .9fr;min-height:80vh;align-items:stretch}}
.hero-content{{padding:12vh 8vw}}
.hero h1{{font-family:'Playfair Display',serif;font-size:64px;line-height:1.02;margin:0 0 12px}}
.hero .sub{{opacity:.7;font-size:18px;margin-bottom:24px}}
.cta{{display:inline-block;background:var(--text);color:#fff;padding:14px 22px;border-radius:999px;box-shadow:0 8px 24px rgba(0,0,0,.08);transition:transform .3s ease, box-shadow .3s ease}}
.cta:hover{{transform:translateY(-2px);box-shadow:0 12px 28px rgba(0,0,0,.12)}}
.hero-media{{background-size:cover;background-position:center;border-left:1px solid rgba(0,0,0,.06)}}
.collections{{max-width:1200px;margin:120px auto;padding:0 24px}}
.collections h2{{font-family:'Playfair Display',serif;font-size:36px;margin:0 0 24px}}
.grid{{display:grid;gap:24px;grid-template-columns:repeat(auto-fill,minmax(260px,1fr))}}
.card{{background:#fff;border:1px solid rgba(0,0,0,.06);border-radius:18px;overflow:hidden;box-shadow:0 10px 40px rgba(0,0,0,.06);transform:translateY(0);transition:transform .35s ease}}
.card:hover{{transform:translateY(-6px)}}
.card .img{{padding-top:66%;background-size:cover;background-position:center}}
.card .info{{display:flex;justify-content:space-between;align-items:center;padding:16px 14px}}
.card .name{{font-weight:500}}
.card .price{{color:var(--muted)}}
.story .split{{display:grid;grid-template-columns:1fr 1fr;gap:40px;max-width:1200px;margin:100px auto;padding:0 24px;align-items:center}}
.story .image{{background-size:cover;background-position:center;border-radius:22px;height:560px;box-shadow:0 20px 60px rgba(0,0,0,.08)}}
.story h3{{font-family:'Playfair Display',serif;font-size:34px;margin:0 0 12px}}
.craft{{max-width:1200px;margin:120px auto;padding:0 24px}}
.craft h2{{font-family:'Playfair Display',serif;font-size:32px;margin:0 0 18px}}
.features{{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:18px}}
.feat{{display:flex;gap:10px;align-items:flex-start;background:#fff;border:1px solid rgba(0,0,0,.06);border-radius:14px;padding:16px 18px}}
.dot{{width:8px;height:8px;border-radius:50%;background:var(--accent);margin-top:9px}}
.lookbook{{max-width:1200px;margin:120px auto;padding:0 24px}}
.masonry{{columns:3;column-gap:16px}}
.masonry img{{width:100%;margin:0 0 16px;border-radius:16px;box-shadow:0 14px 40px rgba(0,0,0,.08)}}
.testimonials{{max-width:900px;margin:120px auto;padding:0 24px;display:grid;gap:20px}}
blockquote{{font-family:'Playfair Display',serif;font-size:20px;line-height:1.6;margin:0;padding:0 0 0 16px;border-left:2px solid var(--accent);color:#333}}
.faq{{max-width:900px;margin:120px auto;padding:0 24px;display:grid;gap:10px}}
details{{background:#fff;border:1px solid rgba(0,0,0,.06);border-radius:14px;padding:14px 16px}}
summary{{cursor:pointer;font-weight:500}}
.footer{{margin-top:140px;border-top:1px solid rgba(0,0,0,.06);padding:40px 0;background:rgba(255,255,255,.7);backdrop-filter:blur(10px)}}
.footer .inner{{max-width:1200px;margin:0 auto;padding:0 24px;display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap}}
.newsletter input{{border:1px solid rgba(0,0,0,.12);border-radius:999px;padding:12px 16px;margin-right:8px}}
.newsletter button{{background:var(--text);color:#fff;border:none;border-radius:999px;padding:12px 18px;cursor:pointer}}
"""

    js = """
// Smooth anchor scrolling
const links = document.querySelectorAll('a[href^="#"]');
links.forEach(l=>l.addEventListener('click',e=>{e.preventDefault();document.querySelector(l.getAttribute('href')).scrollIntoView({behavior:'smooth'})}))
// Parallax hero
window.addEventListener('scroll',()=>{const y=window.scrollY;const media=document.querySelector('.hero-media');if(media){media.style.transform=`translateY(${y*0.08}px)`}})
"""

    return html, css, js
