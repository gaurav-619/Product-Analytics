import asyncio
from playwright.async_api import async_playwright

async def capture_screenshots():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 2160})
        page = await context.new_page()

        # Wait for Streamlit to load fully
        base_url = "http://localhost:8501"
        
        pages_to_capture = [
            ("01_executive_summary.png", "/Executive_Summary")
        ]
        
        for filename, path in pages_to_capture:
            print(f"Capturing {filename}...")
            await page.goto(f"{base_url}{path}")
            # Wait for any data/charts to render
            await page.wait_for_timeout(6000)
            # Remove header and footer if possible to make it look clean
            await page.evaluate("""
                const header = document.querySelector('header');
                if (header) header.style.display = 'none';
                const footer = document.querySelector('footer');
                if (footer) footer.style.display = 'none';
                
                // For Streamlit specifically
                const stHeader = document.querySelector('header[data-testid="stHeader"]');
                if (stHeader) stHeader.style.display = 'none';
                
                const menu = document.querySelector('div[data-testid="stToolbar"]');
                if (menu) menu.style.display = 'none';
            """)
            await page.screenshot(path=f"c:/Users/goura/Documents/Project/cookiepulse/assets/dashboard_screenshots/{filename}", full_page=True)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_screenshots())
