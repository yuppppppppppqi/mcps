from mcp.server.fastmcp import FastMCP
from playwright.async_api import async_playwright
import os
import time
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
    if not os.path.isabs(save_dir):
        save_dir = os.path.abspath(os.path.join(os.getcwd(), save_dir))
    
    os.makedirs(save_dir, exist_ok=True)
    
    downloaded_files = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True) # Run headless=False to see what's happening, can be changed later
        page = await browser.new_page()
        
        try:
            # Build URL with orientation and license filters
            url = f"https://unsplash.com/s/photos/{query}?orientation={orientation}&license={license_type}"
            await page.goto(url)
            await page.wait_for_load_state("networkidle")
            
            # Select image elements (this selector might need adjustment based on Unsplash's DOM)
            # Unsplash usually uses <figure> or <img> within specific containers.
            # We'll look for the download buttons or high-res images.
            # Strategy: Find images, get their source or click into them to download.
            # Easier strategy for now: Get the 'src' of the search results (which might be smaller) 
            # OR try to find the download link.
            
            # Unsplash structure often changes, but let's try to find results.
            # 'figure[data-test="photo-grid-masonry-figure"]' is a common pattern or similar.
            
            # Let's wait for images to load
            await page.wait_for_selector("img", timeout=10000)
            
            # Get all image elements that look like photos (ignoring avatars etc)
            # Usually main photos are large.
            
            # A more robust way might be to click the first N photos and find the download button,
            # but that takes time.
            # Let's try to grab 'src' from the gallery first, assuming high enough quality for now,
            # or try to construct the download URL if possible.
            
            # Unsplash adds 'w=...' parameters. We can try to modify them for higher res.
            
            images = await page.locator("figure img").all()
            
            # 1. Collect valid URLs first
            valid_image_tasks = []
            
            for i, img in enumerate(images):
                if len(valid_image_tasks) >= count:
                    break
                
                src = await img.get_attribute("src")
                if not src:
                    continue
                
                # Filter out small icons or user avatars
                if "profile" in src or "avatar" in src:
                    continue
                    
                valid_image_tasks.append(src)

            # 2. Define download worker
            async def download_single_image(src, index):
                try:
                    # Download the image using playwright request context (async)
                    response = await page.request.get(src)
                    if response.status == 200:
                        filename = f"{query}_{index + 1}.jpg"
                        filepath = os.path.join(save_dir, filename)
                        
                        # Read binary data
                        data = await response.body()
                        
                        # Write to file (sync but fast enough, or could use asyncio.to_thread)
                        with open(filepath, "wb") as f:
                            f.write(data)
                        
                        return filepath
                except Exception as e:
                    print(f"Failed to download {src}: {e}")
                    return None
            
            # 3. Execute downloads in parallel
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
