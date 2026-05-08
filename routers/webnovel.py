from fastapi import APIRouter, Query
from playwright.sync_api import sync_playwright
import re
import asyncio

router = APIRouter(
    prefix="/webnovel",
    tags=["Webnovel"]
)


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def scrape_search(q: str, limit: int = 15):
    results = []
    debug = {}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-gpu'
                ]
            )

            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
            )

            page = context.new_page()
            page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

            url = f"https://www.webnovel.com/search?keyword={q.replace(' ', '%20')}"
            debug["url"] = url

            # Softer loading
            page.goto(url, timeout=45000)

            try:
                page.wait_for_load_state("domcontentloaded", timeout=15000)
            except:
                pass

            # Important: wait for JS to render results
            page.wait_for_timeout(8000)

            debug["page_title"] = page.title()

            # Main selectors for search results
            search_items = page.query_selector_all(
                "div.search-result-item, div.book-item, div.novel-item, li")

            debug["items_found"] = len(search_items)

            for item in search_items[:limit]:
                try:
                    link = item.query_selector("a[href*='/book/']")
                    if not link:
                        continue

                    title_text = link.inner_text().strip()

                    if len(title_text) < 4:
                        continue

                    href = link.get_attribute("href")
                    full_url = "https://www.webnovel.com" + \
                        href if href and not href.startswith("http") else href

                    results.append({
                        "title": clean_text(title_text),
                        "url": full_url,
                    })
                except:
                    continue

            # Fallback if nothing found
            if not results:
                fallback = page.query_selector_all("a[href*='/book/']")
                debug["fallback_count"] = len(fallback)
                for link in fallback[:limit]:
                    try:
                        title = link.inner_text().strip()
                        if "shadow slave" in title.lower() or len(title) > 5:   # avoid garbage
                            href = link.get_attribute("href")
                            full_url = "https://www.webnovel.com" + \
                                href if href and not href.startswith(
                                    "http") else href
                            results.append(
                                {"title": clean_text(title), "url": full_url})
                    except:
                        continue

            browser.close()

    except Exception as e:
        debug["error"] = str(e)

    return {"results": results[:limit], "debug": debug}


@router.get("/")
async def home():
    return {
        "message": "Webnovel Scraper",
        "search": "/webnovel/search?q=shadow slave"
    }


@router.get("/search")
async def search_webnovel(q: str = Query(..., description="Search keyword"),
                          limit: int = Query(15)):

    data = await asyncio.to_thread(scrape_search, q, limit)
    results = data["results"]

    return {
        "success": True,
        "query": q,
        "results_count": len(results),
        "debug_info": data["debug"],
        "results": results
    }
