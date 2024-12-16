from fastapi import APIRouter
from app.tasks.workflows import scrape_titles, scrape_with_click
from pydantic import BaseModel
from app.utils.scraper_helpers import open_page, extract_title
router = APIRouter(prefix="/scraper", tags=["Scraper"])

class ScrapeTitlesRequest(BaseModel):
    url: str
    selector: str

class ScrapeWithClickRequest(BaseModel):
    url: str
    click_selector: str
    content_selector: str

class ScraperTask(BaseModel):
    url: str

@router.post("/run")
async def run_scraper(task: ScraperTask):
    driver = open_page(task.url)
    try:
        title = extract_title(driver)
        return {"url": task.url, "title": title}
    except Exception as e:
        return {"message": "Error during scraping", "details": str(e)}
    finally:
        driver.quit()

@router.post("/titles")
async def get_titles(task: ScrapeTitlesRequest):
    """Endpoint to scrape titles."""
    return {"titles": scrape_titles(task.url, task.selector)}

@router.post("/with-click")
async def get_content_with_click(task: ScrapeWithClickRequest):
    """Endpoint to scrape content after clicking an element."""
    return {"content": scrape_with_click(task.url, task.click_selector, task.content_selector)}