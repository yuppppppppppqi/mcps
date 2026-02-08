from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright
import os
import asyncio


# Initialize FastMCP server
mcp = FastMCP("unsplash-downloader")

@mcp.tool()
async def download_images(
    query: str, 
    count: int = 1, 
    save_dir: str = "images",
    orientation: str = "landscape",
    license_type: str = "free"
) -> str:
    """
    Search and download images from Unsplash using Playwright.
    
    Args:
        query: Search query for Unsplash (e.g., "cats", "nature").
        count: Number of images to download (default: 1).
        save_dir: Directory to save downloaded images (relative to script execution or absolute).
        orientation: Image orientation filter. Options: "landscape", "portrait", "squarish" (default: "landscape").
        license_type: License filter. Options: "free", "plus" (default: "free").
    
    Returns:
        String message summarizing the result including file paths and license info.
    """
    # Create save directory if it doesn't exist
    if not os.path.isabs(save_dir) and save_dir:
        save_dir = os.path.abspath(os.path.join(os.getcwd(), save_dir))
    elif not save_dir:
        save_dir = os.path.abspath("images")
    
    os.makedirs(save_dir, exist_ok=True)
    
    downloaded_files = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )
        page = await context.new_page()
        
        try:
            # Build URL
            url = f"https://unsplash.com/s/photos/{query}?orientation={orientation or 'landscape'}&license={license_type or 'free'}"
            await page.goto(url, wait_until="load", timeout=60000)
            
            # Additional wait for images to render
            await asyncio.sleep(5)
            
            # Use JS evaluation to get sources - proven robust in non-headless
            srcs = await page.evaluate("""
                () => {
                    const selectors = [
                        'figure img',
                        'img[data-test="photo-grid-masonry-img"]',
                        'img[src*="images.unsplash.com/photo-"]'
                    ];
                    let sources = [];
                    for (const selector of selectors) {
                        const imgs = Array.from(document.querySelectorAll(selector));
                        if (imgs.length > 0) {
                            sources = imgs.map(img => img.src).filter(src => src && !src.includes('profile') && !src.includes('avatar'));
                            if (sources.length > 0) break;
                        }
                    }
                    return sources;
                }
            """)
            
            valid_image_tasks = srcs[:count] if srcs else []

            # Download worker
            async def download_single_image(src, index):
                try:
                    response = await page.request.get(src)
                    if response.status == 200:
                        filename = f"{query}_{index + 1}.jpg"
                        filepath = os.path.join(save_dir, filename)
                        data = await response.body()
                        with open(filepath, "wb") as f:
                            f.write(data)
                        return filepath
                except:
                    return None
            
            if valid_image_tasks:
                tasks = [download_single_image(src, i) for i, src in enumerate(valid_image_tasks)]
                results = await asyncio.gather(*tasks)
                downloaded_files = [f for f in results if f is not None]
                
        except Exception as e:
            return f"Error occurred: {str(e)}"
        finally:
            await browser.close()

    return f"Downloaded {len(downloaded_files)} images to {save_dir} (orientation={orientation}, license={license_type}): {', '.join(downloaded_files)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
