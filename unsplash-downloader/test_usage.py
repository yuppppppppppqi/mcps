from server import download_images
import os
import asyncio

async def test_download():
    print("Testing download_images...")
    try:
        # Create a test directory
        test_dir = "test_output"
        
        # Run download with orientation and license filters
        result = await download_images("brain", count=3, save_dir=test_dir, orientation="landscape", license_type="free")
        print(f"Result: {result}")
        
        # Verify file exists
        files = os.listdir(test_dir)
        if len(files) > 0:
            print(f"Success! Found files: {files}")
        else:
            print("Failed! No files found.")
            
    except Exception as e:
        print(f"Test failed with error: {e}")

if __name__ == "__main__":
    asyncio.run(test_download())
