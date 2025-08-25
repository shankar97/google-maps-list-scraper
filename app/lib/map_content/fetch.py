import logging
from pathlib import Path
import time
from typing import Tuple, List, Dict, Optional, Any

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from .parse import (
    extract_rating_from_text,
    extract_price_from_text,
    extract_description_from_lines,
)


def create_driver() -> webdriver.Chrome:
    logger = logging.getLogger(__name__)
    logger.info("Creating Chrome WebDriver")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1400,1000")
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def scroll_results_panel(driver: webdriver.Chrome, times: int = 10, delay_seconds: float = 2.0) -> None:
    """Scroll the Google Maps results panel to load more items.

    Targets container with classes: "m6QErb DxyBCb kA9KIf dS8AEf XiKgde ussYcc".
    """
    logger = logging.getLogger(__name__)
    try:
        panel_selector = "div.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde.ussYcc"
        logger.info("Waiting for results panel: %s", panel_selector)
        panel = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, panel_selector))
        )
        logger.info("Results panel located; starting %d scroll iterations", times)
        for i in range(times):
            logger.info("Scroll iteration %d/%d", i + 1, times)
            try:
                driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight;",
                    panel,
                )
            except Exception:
                # Best-effort: if direct scroll fails, try sending END key via JS
                driver.execute_script(
                    "arguments[0].scrollTo(0, arguments[0].scrollHeight);",
                    panel,
                )
            time.sleep(delay_seconds)
        logger.info("Completed scrolling")
    except Exception:
        # Non-fatal: continue even if panel not found to keep existing behavior
        logger.warning("Results panel not found; skipping scrolling")


def fetch_html(url: str, save_dir: Path | None = None) -> Tuple[str, int, int]:
    logger = logging.getLogger(__name__)
    logger.info("Fetching raw HTML from URL: %s", url)
    driver = create_driver()
    try:
        driver.get(url)
        time.sleep(5)
        # Scroll results panel to load more content
        scroll_results_panel(driver, times=10, delay_seconds=2.0)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        containers_bs = len(soup.select("div.m6QErb.XiKgde"))
        containers_sel = len(driver.find_elements(By.CSS_SELECTOR, "div.m6QErb.XiKgde"))
        logger.info("Container counts — BeautifulSoup: %d, Selenium: %d", containers_bs, containers_sel)
        
        with open('page.html', "w", encoding="utf-8") as f:
            f.write(html)
        logger.info("Saved page HTML to %s", 'page.html')
        return html, containers_bs, containers_sel
    finally:
        driver.quit()



def get_text_or_none(element, selectors: List[str]) -> Optional[str]:
    """Try a list of CSS selectors relative to element and return first non-empty text."""
    for selector in selectors:
        try:
            sub = element.find_element(By.CSS_SELECTOR, selector)
            if sub is not None:
                text = (sub.text or "").strip()
                if text:
                    return text
        except Exception:
            continue
    return None


def get_price_like_text(element) -> Optional[str]:
    """Best-effort: return a price-like token from the element, if any."""
    try:
        text = (element.text or "").strip()
        price = extract_price_from_text(text)
        if price:
            return price
    except Exception:
        pass
    return None


def fetch_places(url: str, save_dir: Path | None = None) -> Dict[str, Any]:
    """Fetch a Google Maps page and parse per-card elements into structured items.

    Returns a dict with shape: {"list_description": str | None, "items": [ { name, rating, description, price } ]}
    """
    logger = logging.getLogger(__name__)
    logger.info("Fetching places from URL: %s", url)
    driver = create_driver()
    try:
        driver.get(url)
        time.sleep(5)
        # Scroll results panel to load more content
        scroll_results_panel(driver, times=10, delay_seconds=2.0)

        # Optionally persist the HTML for debugging
        try:
            html = driver.page_source
            with open('page.html', "w", encoding="utf-8") as f:
                f.write(html)
            logger.info("Saved page HTML to %s", 'page.html')
        except Exception:
            logger.info("Skipping HTML save; non-fatal error while writing file")

        # Find the cards
        cards = driver.find_elements(By.CSS_SELECTOR, "div.m6QErb.XiKgde")
        logger.info("Found %d card containers via Selenium selector", len(cards))

        items: List[Dict[str, Optional[str]]] = []
        list_description: Optional[str] = None
        for idx, el in enumerate(cards):
            txt = (el.text or "").strip()
            lines = [l.strip() for l in txt.splitlines() if l.strip()]

            name = get_text_or_none(
                el,
                [
                    "div.qBF1Pd",
                    "h1.DUwDvf",
                    "div.fontHeadlineSmall",
                    "[role='heading']",
                ],
            ) or (lines[0] if lines else None)

            rating_text = get_text_or_none(
                el,
                [
                    "span.MW4etd",
                    "div.F7nice",
                    "span[aria-label*='stars']",
                ],
            )
            rating = rating_text or extract_rating_from_text(txt)

            description = get_text_or_none(
                el,
                [
                    "div.W4Efsd",
                    "div.iP2t7d",
                    "div.kR99db",
                ],
            ) or extract_description_from_lines(lines)

            price = get_price_like_text(el) or extract_price_from_text(txt)

            if idx == 0 and list_description is None:
                list_description = description
            elif (name or rating or description or price) and description != list_description and (name != [] or name != "[]"):
                items.append(
                    {
                        "name": name,
                        "rating": rating,
                        "description": description,
                        "price": price,
                    }
                )

        logger.info("Parsed %d items; list_description present: %s", len(items), bool(list_description))
        return {"list_description": list_description, "items": items}
    finally:
        driver.quit()

