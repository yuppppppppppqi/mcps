from mcp.server.fastmcp import FastMCP
from rembg import remove
from PIL import Image
import os
import io
from pydantic import Field
from typing import Annotated

# Initialize FastMCP server
mcp = FastMCP("remove-bg")

@mcp.tool()
def remove_background(
    image_path: str, 
    output_path: str = None,
    alpha_matting: bool = False,
    alpha_matting_foreground_threshold: Annotated[int, Field(ge=0, le=255, description="Foreground threshold (0-255)")] = 240,
    alpha_matting_background_threshold: Annotated[int, Field(ge=0, le=255, description="Background threshold (0-255)")] = 10,
    alpha_matting_erode_size: Annotated[int, Field(ge=0, description="Erosion size (>=0)")] = 10
) -> str:
    """
    Remove background from an image using rembg.
    
    Args:
        image_path: Absolute path to the input image file.
        output_path: Optional absolute path for the output image. 
                     If not provided, defaults to [original_filename]_nobg.png in the same directory.
        alpha_matting: Enable alpha matting for better edge handling (default: False).
        alpha_matting_foreground_threshold: Threshold for foreground (default: 240).
        alpha_matting_background_threshold: Threshold for background (default: 10).
        alpha_matting_erode_size: Erosion size (default: 10).
    
    Returns:
        The absolute path to the processed image with background removed.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at: {image_path}")

    try:
        # Load image
        input_image = Image.open(image_path)
        
        # Remove background
        output_image = remove(
            input_image,
            alpha_matting=alpha_matting,
            alpha_matting_foreground_threshold=alpha_matting_foreground_threshold,
            alpha_matting_background_threshold=alpha_matting_background_threshold,
            alpha_matting_erode_size=alpha_matting_erode_size
        )
        
        # Determine output path
        if output_path is None:
            base, ext = os.path.splitext(image_path)
            output_path = f"{base}_nobg.png"
            
        # Save output
        output_image.save(output_path)
        
        return output_path
    
    except Exception as e:
        raise RuntimeError(f"Failed to remove background: {str(e)}")

# Add a test run functionality
if __name__ == "__main__":
    # This block allows running the server directly with 'mcp run server.py'
    mcp.run(transport="stdio")
