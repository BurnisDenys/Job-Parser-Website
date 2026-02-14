from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from database import JobDatabase
from parser import InternationalJobParser
from site_tester import SiteTester
import logging


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Job Parser API")

# Add CORS middleware to allow requests from any domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Initialize database, parser and site tester
db = JobDatabase()
parser = InternationalJobParser()
tester = SiteTester()


# Define data models for requests/responses
class SearchRequest(BaseModel):
    query: str
    location: str
    salary: Optional[str] = None
    experience: str = "all"
    pages: int = 2
    page: int = 0
    sources: List[str]


class JobResponse(BaseModel):
    id: Optional[int] = None
    title: str
    company: str
    location: str
    salary: str
    summary: str
    link: str
    source: str
    parsed_at: str


# API Endpoints

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve home page"""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>File index.html not found</h1>"


@app.get("/test")
async def test():
    """Test endpoint to check if server is working"""
    return {"message": "Server is working!"}


@app.options("/api/{path:path}")
async def options_handler(path: str):
    """Handle CORS preflight requests"""
    return JSONResponse({"message": "OK"})


@app.post("/api/search")
async def search_jobs(request: SearchRequest):
    """Search for jobs without AI"""
    try:
        logger.info(f"Search request: {request.query} in {request.location}")
        
        # Map old sources to new ones
        source_mapping = {
            'indeed': 'indeed',
            'stepstone': 'stepstone',
            'xing': 'linkedin',
            'remotive': 'indeed',
            'olx': 'stepstone',
            'linkedin': 'linkedin',
            'glassdoor': 'indeed',
            'stackoverflow': 'eures',
            'github': 'stepstone'
        }
        
        # Convert sources using mapping
        sources = [source_mapping.get(s, s) for s in request.sources]
        # Remove duplicates
        sources = list(set(sources))
        
        # Use default sources if none provided
        if not sources:
            sources = ['indeed', 'linkedin', 'stepstone']
        
        logger.info(f"📊 Testing sites...")
        site_tests = {}
        for source in sources:
            site_tests[source] = {
                'available': True,
                'status': 'checking'
            }
        
        # Parse jobs - just simple parsing without AI
        logger.info(f"🔍 Parsing {sources}...")
        jobs = parser.parse_all_sites(
            query=request.query,
            location=request.location,
            sources=sources,
            page=request.page,
            max_pages=request.pages
        )
        
        logger.info(f"Found {len(jobs)} vacancies")
        
        # Filter jobs based on criteria
        filtered_jobs = InternationalJobParser.filter_jobs(
            jobs,
            min_salary=int(request.salary) if request.salary else None,
            experience_level=request.experience
        )
        
        # Save jobs to database
        saved_count = db.save_jobs(filtered_jobs)
        
        # Save search history
        db.save_search_history(
            query=request.query,
            location=request.location,
            sources=request.sources,
            results_count=len(filtered_jobs)
        )
        
        # Prepare statistics
        stats = {
            'total': len(filtered_jobs),
            'saved': saved_count,
            'indeed': len([j for j in filtered_jobs if j['source'] == 'Indeed']),
            'stepstone': len([j for j in filtered_jobs if j['source'] == 'StepStone']),
            'xing': len([j for j in filtered_jobs if j['source'] == 'LinkedIn']),
            'site_tests': site_tests
        }
        
        return {"jobs": filtered_jobs, "stats": stats}
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/jobs")
async def get_jobs(limit: int = 50, offset: int = 0):
    """Get jobs from database"""
    try:
        jobs = db.get_all_jobs(limit=limit, offset=offset)
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/statistics")
async def get_statistics():
    """Get statistics about jobs"""
    try:
        stats = db.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search-history")
async def get_search_history():
    """Get search history""" 
    try:
        history = db.get_search_history()
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/jobs/old")
async def delete_old_jobs(days: int = 30):
    """Delete old jobs"""
    try:
        deleted = db.clear_old_jobs(days=days)
        return {"deleted": deleted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    logger.info("🚀 Starting FastAPI server...")
    logger.info("📱 Open browser: http://localhost:8000")
    logger.info("📚 API documentation: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
