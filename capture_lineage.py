import asyncio
from playwright.async_api import async_playwright

async def capture_dbt_lineage():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Wide view to fit the DAG
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        print("Navigating to dbt docs lineage graph...")
        # g_v=1 opens the graph view directly
        await page.goto("http://localhost:8080/#!/overview?g_v=1")
        
        # Wait for the network to be idle and graph to render
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(10000) # extra wait for the canvas/svg to draw
        
        # Hide the sidebar and overlays to make it clean
        await page.evaluate("""
            const sidebar = document.querySelector('.sidebar');
            if (sidebar) sidebar.style.display = 'none';
            const navbar = document.querySelector('.navbar');
            if (navbar) navbar.style.display = 'none';
        """)
        
        print("Capturing dbt_lineage.png...")
        await page.screenshot(path="c:/Users/goura/Documents/Project/cookiepulse/assets/dbt_lineage.png", full_page=True)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_dbt_lineage())
