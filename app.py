# PRESTIGE 360 Brand Engine v3.0
# Dark gradient header bar for white logo
# White tagline text

from flask import Flask, request, send_file, jsonify, send_from_directory
from PIL import Image, ImageDraw, ImageFont
import io
import os
import base64
import uuid
import time
import requests

app = Flask(__name__)

# =========================
# Storage for generated images
# =========================
generated_images = {}

# =========================
# Paths
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POST_OUTPUT_DIR = os.path.join(BASE_DIR, 'post_output')
os.makedirs(POST_OUTPUT_DIR, exist_ok=True)

# =========================
# Font Configuration
# =========================
FONT_BOLD_PATH = "Montserrat-Bold.ttf"

# =========================
# PRESTIGE 360 Brand Colors
# =========================
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY_LIGHT = (120, 120, 120)  # Darker for better visibility on light backgrounds
GRAY_SUBTITLE = (50, 50, 50)   # Much darker for subtitle text

# Prestige Orange Gradient Colors
PRESTIGE_ORANGE_START = (255, 49, 49)    # #FF3131
PRESTIGE_ORANGE_END = (242, 106, 33)     # #F26A21
PRESTIGE_ORANGE_MID = (248, 78, 42)      # Middle color for solid use

# =========================
# PRESTIGE 360 Brand Defaults
# =========================
DEFAULT_BRAND_NAME = os.environ.get('BRAND_NAME', 'PRESTIGE 360')
DEFAULT_TAGLINE = os.environ.get('TAGLINE', 'Commercial Design From Concept to Opening')
DEFAULT_WEBSITE = os.environ.get('WEBSITE_URL', 'www.prestige360design.com')
# NEW: Cloudinary URL for white logo
LOGO_URL = os.environ.get('LOGO_URL', 'https://res.cloudinary.com/dotimxrnh/image/upload/v1772677159/WHITE_Prestige_y3ucpo.png')

# =========================
# Layout Configuration - VERTICAL 4:5 for Instagram/Facebook
# =========================
CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1350  # 4:5 aspect ratio
MARGIN_LEFT = 50
MARGIN_RIGHT = 50
MARGIN_TOP = 35
MARGIN_BOTTOM = 50

# Header gradient bar height
HEADER_GRADIENT_HEIGHT = 100

# =========================
# Text Limits - ADJUSTED FOR BETTER FIT
# =========================
ORANGE_BOX_MAX_LINES = 2
ORANGE_BOX_MAX_WIDTH = 650  # Reduced to prevent overflow
BIG_TEXT_MAX_LINES = 3
BIG_TEXT_MAX_WIDTH = 850    # Reduced to prevent text cutting
DESCRIPTION_MAX_LINES = 2
DESCRIPTION_MAX_WIDTH = 850

# =========================
# Load Fonts AT STARTUP
# =========================
def load_font(size, name):
    try:
        font = ImageFont.truetype(FONT_BOLD_PATH, size)
        print(f"✅ {name} loaded at {size}px")
        return font
    except Exception as e:
        print(f"❌ {name} error: {e}")
        return ImageFont.load_default()

# Font sizes
orange_box_font = load_font(52, "orange_box_font")
big_text_font = load_font(72, "big_text_font")
description_font = load_font(28, "description_font")
website_font = load_font(24, "website_font")
tagline_font = load_font(18, "tagline_font")

# Cached logo
cached_logo = None


def cleanup_old_images():
    """Remove images older than 10 minutes"""
    current_time = time.time()
    keys_to_delete = []
    for key, value in generated_images.items():
        if current_time - value['timestamp'] > 600:
            keys_to_delete.append(key)
    for key in keys_to_delete:
        del generated_images[key]


def fit_cover(img, target_w, target_h):
    """Scale and crop to fill - ensures image covers entire canvas"""
    img_w, img_h = img.size
    print(f"📐 fit_cover: input {img_w}x{img_h} → target {target_w}x{target_h}")
    
    scale = max(target_w / img_w, target_h / img_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)
    
    print(f"📐 fit_cover: scaling to {new_w}x{new_h} (scale: {scale:.2f})")
    
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    
    result = img.crop((left, top, left + target_w, top + target_h))
    print(f"📐 fit_cover: final size {result.size}")
    
    return result


def load_logo():
    """Load Prestige logo from Cloudinary URL (cached)"""
    global cached_logo
    if cached_logo is not None:
        return cached_logo.copy()
    
    try:
        print(f"🔄 Loading logo from: {LOGO_URL}")
        resp = requests.get(LOGO_URL, timeout=15)
        resp.raise_for_status()
        logo = Image.open(io.BytesIO(resp.content))
        logo = logo.convert("RGBA")
        # Resize to fit header - max height 45px
        max_height = 45
        ratio = max_height / logo.height
        new_width = int(logo.width * ratio)
        logo = logo.resize((new_width, max_height), Image.LANCZOS)
        cached_logo = logo
        print(f"✅ Logo loaded: {new_width}x{max_height}")
        return logo.copy()
    except Exception as e:
        print(f"⚠️ Could not load logo: {e}")
        return None


def create_header_gradient(width, canvas_height, gradient_height=100):
    """
    Create dark gradient bar at top for white logo visibility
    Like Hugo Brand Engine style
    Returns full canvas size image with gradient only at top
    """
    gradient = Image.new('RGBA', (width, canvas_height), (0, 0, 0, 0))
    
    for y in range(gradient_height):
        # Strong at top, fades to transparent
        alpha = int(200 * (1 - (y / gradient_height) ** 0.7))
        for x in range(width):
            gradient.putpixel((x, y), (0, 0, 0, alpha))
    
    return gradient


def create_light_overlay(width, height, opacity=0.75):
    """Create white semi-transparent overlay for light theme"""
    overlay = Image.new('RGBA', (width, height), (255, 255, 255, int(255 * opacity)))
    return overlay


def create_gradient_overlay(width, height):
    """Create gradient for image-heavy theme: dark at top, CENTER BAND, and bottom"""
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    
    # Top gradient (for logo visibility) - STRONGER
    top_height = 140
    for y in range(top_height):
        alpha = int(220 * (1 - (y / top_height) ** 0.6))
        for x in range(width):
            overlay.putpixel((x, y), (0, 0, 0, alpha))
    
    # CENTER BAND gradient (for text visibility) - NEW
    # Starts at content area and extends down
    center_start = 400
    center_height = 450
    for y in range(center_height):
        # Fade in, stay strong, fade out
        progress = y / center_height
        if progress < 0.2:
            alpha = int(180 * (progress / 0.2))
        elif progress > 0.8:
            alpha = int(180 * ((1 - progress) / 0.2))
        else:
            alpha = 180
        for x in range(width):
            overlay.putpixel((x, center_start + y), (0, 0, 0, alpha))
    
    # Bottom gradient (for website visibility)
    bottom_height = 120
    start_y = height - bottom_height
    for y in range(bottom_height):
        alpha = int(200 * (y / bottom_height))
        for x in range(width):
            overlay.putpixel((x, start_y + y), (0, 0, 0, alpha))
    
    return overlay


def wrap_text(text, font, max_width, draw):
    """Wrap text to fit within max_width."""
    if not text:
        return []
    
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]
        
        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines


def truncate_lines(lines, max_lines, font, max_width, draw):
    """Truncate to max_lines with ellipsis."""
    if len(lines) <= max_lines:
        return lines
    
    truncated = lines[:max_lines]
    last_line = truncated[-1]
    
    while True:
        test_line = last_line + '...'
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]
        
        if width <= max_width:
            truncated[-1] = test_line
            break
        else:
            words = last_line.split()
            if len(words) <= 1:
                truncated[-1] = '...'
                break
            last_line = ' '.join(words[:-1])
    
    return truncated


def draw_orange_box(draw, text, x, y, font, max_width, max_lines, padding=15):
    """Draw text inside orange box, returns box height"""
    if not text:
        return 0
    
    # Wrap and truncate text
    lines = wrap_text(text.upper(), font, max_width - (padding * 2), draw)
    lines = truncate_lines(lines, max_lines, font, max_width - (padding * 2), draw)
    
    if not lines:
        return 0
    
    # Calculate box dimensions
    line_height = font.size + 8
    total_text_height = len(lines) * line_height
    box_height = total_text_height + (padding * 2)
    
    # Find max line width for box width
    max_line_width = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        max_line_width = max(max_line_width, line_width)
    
    box_width = max_line_width + (padding * 2)
    
    # Draw orange box
    draw.rectangle(
        [x, y, x + box_width, y + box_height],
        fill=PRESTIGE_ORANGE_MID
    )
    
    # Draw text inside box
    text_y = y + padding
    for line in lines:
        draw.text((x + padding, text_y), line, font=font, fill=WHITE)
        text_y += line_height
    
    return box_height


def draw_big_text(draw, text, x, y, font, max_width, max_lines, color):
    """Draw big text with wrapping, returns total height"""
    if not text:
        return 0
    
    lines = wrap_text(text.upper(), font, max_width, draw)
    lines = truncate_lines(lines, max_lines, font, max_width, draw)
    
    if not lines:
        return 0
    
    line_height = font.size + 10
    text_y = y
    
    for line in lines:
        draw.text((x, text_y), line, font=font, fill=color)
        text_y += line_height
    
    return len(lines) * line_height


def draw_orange_underline(draw, x, y, width, height=4):
    """Draw orange gradient underline"""
    for i in range(width):
        ratio = i / width
        r = int(PRESTIGE_ORANGE_START[0] + (PRESTIGE_ORANGE_END[0] - PRESTIGE_ORANGE_START[0]) * ratio)
        g = int(PRESTIGE_ORANGE_START[1] + (PRESTIGE_ORANGE_END[1] - PRESTIGE_ORANGE_START[1]) * ratio)
        b = int(PRESTIGE_ORANGE_START[2] + (PRESTIGE_ORANGE_END[2] - PRESTIGE_ORANGE_START[2]) * ratio)
        draw.line([(x + i, y), (x + i, y + height)], fill=(r, g, b))


def draw_arrow(draw, x, y, size=40, color=PRESTIGE_ORANGE_MID):
    """Draw swipe arrow →"""
    # Arrow body
    draw.line([(x, y), (x + size, y)], fill=color, width=4)
    # Arrow head
    draw.line([(x + size - 15, y - 12), (x + size, y)], fill=color, width=4)
    draw.line([(x + size - 15, y + 12), (x + size, y)], fill=color, width=4)


def render_slide(image_source, headline="", big_text="", description="", 
                 slide_number=1, total_slides=6, show_arrow=True, show_website=True):
    """
    Render Prestige 360 carousel slide
    
    Theme is auto-determined:
    - Slide 1 and last slide = Light theme (but with dark header gradient for logo)
    - Middle slides = Image-heavy theme with gradients
    """
    
    # Determine theme based on slide position
    is_light_theme = (slide_number == 1) or (slide_number == total_slides)
    
    # Create canvas
    canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (255, 255, 255, 255))
    
    # Load background image
    if isinstance(image_source, Image.Image):
        photo = image_source
    elif isinstance(image_source, bytes):
        photo = Image.open(io.BytesIO(image_source))
    elif isinstance(image_source, str) and os.path.exists(image_source):
        photo = Image.open(image_source)
    elif isinstance(image_source, str) and image_source.startswith('http'):
        resp = requests.get(image_source, timeout=60)
        resp.raise_for_status()
        photo = Image.open(io.BytesIO(resp.content))
    else:
        raise ValueError("Invalid image source")
    
    photo = photo.convert("RGBA")
    fitted = fit_cover(photo, CANVAS_WIDTH, CANVAS_HEIGHT)
    canvas.paste(fitted, (0, 0))
    
    # Apply theme overlay
    if is_light_theme:
        overlay = create_light_overlay(CANVAS_WIDTH, CANVAS_HEIGHT, 0.78)
        canvas = Image.alpha_composite(canvas, overlay)
        # ADD dark header gradient on TOP for white logo visibility
        header_gradient = create_header_gradient(CANVAS_WIDTH, CANVAS_HEIGHT, HEADER_GRADIENT_HEIGHT)
        canvas = Image.alpha_composite(canvas, header_gradient)
        text_color = BLACK
        subtitle_color = (40, 40, 40)  # Very dark for light backgrounds
    else:
        overlay = create_gradient_overlay(CANVAS_WIDTH, CANVAS_HEIGHT)
        canvas = Image.alpha_composite(canvas, overlay)
        text_color = WHITE
        subtitle_color = WHITE  # WHITE for dark backgrounds
    
    # Create draw object
    draw = ImageDraw.Draw(canvas)
    
    # === HEADER: Logo (WHITE logo on dark gradient) - LEFT ===
    logo = load_logo()
    if logo:
        canvas.paste(logo, (MARGIN_LEFT, MARGIN_TOP), logo)
    
    # === HEADER: Tagline IN WHITE - ALIGNED RIGHT ===
    # Show tagline on ALL slides for brand consistency
    tagline = DEFAULT_TAGLINE
    # Calculate tagline width to align right
    tagline_bbox = draw.textbbox((0, 0), tagline, font=tagline_font)
    tagline_width = tagline_bbox[2] - tagline_bbox[0]
    tagline_x = CANVAS_WIDTH - MARGIN_RIGHT - tagline_width  # Right aligned
    draw.text(
        (tagline_x, MARGIN_TOP + 15),
        tagline,
        font=tagline_font,
        fill=WHITE  # WHITE text on dark gradient
    )
    
    # === CONTENT AREA ===
    # Calculate vertical positions (centered in lower portion)
    content_start_y = 450  # Start content in middle-lower area
    
    # Draw orange box with headline
    current_y = content_start_y
    if headline:
        box_height = draw_orange_box(
            draw, headline, 
            MARGIN_LEFT, current_y,
            orange_box_font, ORANGE_BOX_MAX_WIDTH, ORANGE_BOX_MAX_LINES
        )
        current_y += box_height + 25
    
    # Draw arrow (to the right of orange box area)
    if show_arrow and slide_number < total_slides:
        arrow_x = CANVAS_WIDTH - MARGIN_RIGHT - 60
        arrow_y = content_start_y + 30
        draw_arrow(draw, arrow_x, arrow_y, size=45, color=PRESTIGE_ORANGE_MID)
    
    # Draw big text
    if big_text:
        big_text_height = draw_big_text(
            draw, big_text,
            MARGIN_LEFT, current_y,
            big_text_font, BIG_TEXT_MAX_WIDTH, BIG_TEXT_MAX_LINES,
            text_color
        )
        current_y += big_text_height + 10
        
        # Draw orange underline after big text
        draw_orange_underline(draw, MARGIN_LEFT, current_y, 250, height=5)
        current_y += 25
    
    # Draw description
    if description:
        desc_lines = wrap_text(description, description_font, DESCRIPTION_MAX_WIDTH, draw)
        desc_lines = truncate_lines(desc_lines, DESCRIPTION_MAX_LINES, description_font, DESCRIPTION_MAX_WIDTH, draw)
        
        line_height = description_font.size + 6
        for line in desc_lines:
            draw.text((MARGIN_LEFT, current_y), line, font=description_font, fill=subtitle_color)
            current_y += line_height
    
    # === FOOTER: Website - ALIGNED RIGHT ===
    if show_website:
        website = DEFAULT_WEBSITE
        # Calculate website width to align right
        website_bbox = draw.textbbox((0, 0), website, font=website_font)
        website_width = website_bbox[2] - website_bbox[0]
        website_x = CANVAS_WIDTH - MARGIN_RIGHT - website_width  # Right aligned
        draw.text(
            (website_x, CANVAS_HEIGHT - MARGIN_BOTTOM - 25),
            website,
            font=website_font,
            fill=WHITE  # Always WHITE for visibility
        )
    
    return canvas


# =========================
# ROUTES
# =========================

@app.route('/')
def home():
    return jsonify({
        "service": "Prestige 360 Brand Engine",
        "version": "3.0",
        "status": "running",
        "brand": DEFAULT_BRAND_NAME,
        "logo_url": LOGO_URL,
        "features": [
            "dark_header_gradient",
            "white_logo",
            "white_tagline",
            "auto_theme_alternation",
            "orange_box_headlines",
            "text_wrapping",
            "swipe_arrows"
        ],
        "theme_pattern": "First and Last = Light + Dark Header, Middle = Image",
        "canvas_size": f"{CANVAS_WIDTH}x{CANVAS_HEIGHT}",
        "fonts": {
            "Montserrat-Bold": os.path.isfile(FONT_BOLD_PATH),
        },
        "images_in_cache": len(generated_images)
    })


@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'version': '3.0',
        'brand': 'Prestige 360',
        'logo_url': LOGO_URL,
        'images_in_cache': len(generated_images)
    })


@app.route('/post_output/<filename>')
def serve_output(filename):
    return send_from_directory(POST_OUTPUT_DIR, filename)


@app.route('/download/<image_id>')
def download_image(image_id):
    """Download generated image by ID"""
    try:
        if image_id not in generated_images:
            return jsonify({'error': 'Image not found or expired'}), 404
        
        image_data = generated_images[image_id]['data']
        img_buffer = io.BytesIO(image_data)
        img_buffer.seek(0)
        
        return send_file(
            img_buffer,
            mimetype='image/png',
            as_attachment=False,
            download_name=f'prestige_{image_id}.png'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/render-slide', methods=['POST'])
def render_slide_endpoint():
    """Main endpoint for n8n"""
    try:
        cleanup_old_images()
        
        data = request.get_json(force=True)
        
        # Get image
        image_source = None
        
        if data.get('image_base64'):
            image_data = base64.b64decode(data['image_base64'])
            image_source = Image.open(io.BytesIO(image_data))
        elif data.get('image_url'):
            image_source = data['image_url']
        else:
            return jsonify({"error": "No image provided (need image_url or image_base64)"}), 400
        
        # Get text params
        headline = data.get('headline', '')
        big_text = data.get('big_text', data.get('subtitle', ''))  # Support both names
        description = data.get('description', '')
        
        # Handle bullets as description fallback
        if not description and data.get('bullets'):
            bullets = data['bullets']
            if isinstance(bullets, list) and bullets:
                description = bullets[0] if len(bullets) == 1 else '. '.join(bullets[:2])
        
        # Slide position for theme alternation
        slide_number = data.get('slide_number', 1)
        total_slides = data.get('total_slides', 6)
        show_arrow = data.get('show_arrow', True)
        show_website = data.get('show_website', True)
        
        # Render
        img = render_slide(
            image_source=image_source,
            headline=headline,
            big_text=big_text,
            description=description,
            slide_number=slide_number,
            total_slides=total_slides,
            show_arrow=show_arrow,
            show_website=show_website
        )
        
        # Save to buffer
        img_buffer = io.BytesIO()
        img.convert("RGB").save(img_buffer, format='PNG', quality=95)
        img_buffer.seek(0)
        
        # Store in cache
        image_id = str(uuid.uuid4())
        generated_images[image_id] = {
            'data': img_buffer.getvalue(),
            'timestamp': time.time()
        }
        
        # Save to file
        filename = f"slide_{image_id}.png"
        output_path = os.path.join(POST_OUTPUT_DIR, filename)
        img.convert("RGB").save(output_path, format='PNG', quality=95)
        
        # Build URLs
        base_url = request.host_url.rstrip('/')
        
        # Determine which theme was used
        is_light = (slide_number == 1) or (slide_number == total_slides)
        
        return jsonify({
            "success": True,
            "filename": filename,
            "download_url": f"{base_url}/download/{image_id}",
            "png_url": f"{base_url}/post_output/{filename}",
            "image_id": image_id,
            "slide_number": slide_number,
            "theme_used": "light_with_dark_header" if is_light else "image"
        })
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/render-carousel', methods=['POST'])
def render_carousel_endpoint():
    """Render complete carousel (6 slides) in one call"""
    try:
        cleanup_old_images()
        
        data = request.get_json(force=True)
        slides_data = data.get('slides', [])
        
        if not slides_data:
            return jsonify({"error": "No slides provided"}), 400
        
        total_slides = len(slides_data)
        results = []
        
        for i, slide in enumerate(slides_data):
            slide_number = i + 1
            
            # Get image
            image_source = slide.get('image_url')
            if not image_source and slide.get('image_base64'):
                image_data = base64.b64decode(slide['image_base64'])
                image_source = Image.open(io.BytesIO(image_data))
            
            if not image_source:
                continue
            
            # Render slide
            img = render_slide(
                image_source=image_source,
                headline=slide.get('headline', ''),
                big_text=slide.get('big_text', slide.get('subtitle', '')),
                description=slide.get('description', ''),
                slide_number=slide_number,
                total_slides=total_slides,
                show_arrow=(slide_number < total_slides),
                show_website=True
            )
            
            # Save
            img_buffer = io.BytesIO()
            img.convert("RGB").save(img_buffer, format='PNG', quality=95)
            img_buffer.seek(0)
            
            image_id = str(uuid.uuid4())
            generated_images[image_id] = {
                'data': img_buffer.getvalue(),
                'timestamp': time.time()
            }
            
            filename = f"slide_{image_id}.png"
            output_path = os.path.join(POST_OUTPUT_DIR, filename)
            img.convert("RGB").save(output_path, format='PNG', quality=95)
            
            base_url = request.host_url.rstrip('/')
            
            results.append({
                "slide_number": slide_number,
                "download_url": f"{base_url}/download/{image_id}",
                "png_url": f"{base_url}/post_output/{filename}",
                "theme": "light_with_dark_header" if (slide_number == 1 or slide_number == total_slides) else "image"
            })
        
        return jsonify({
            "success": True,
            "total_slides": len(results),
            "slides": results
        })
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/clear-logo-cache', methods=['POST'])
def clear_logo_cache():
    """Force reload of logo from URL"""
    global cached_logo
    cached_logo = None
    logo = load_logo()
    return jsonify({
        "success": True,
        "logo_loaded": logo is not None,
        "logo_url": LOGO_URL
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Prestige 360 Brand Engine v3.0 starting on port {port}")
    print(f"📍 Brand: {DEFAULT_BRAND_NAME}")
    print(f"📍 Logo: {LOGO_URL}")
    print(f"📍 Website: {DEFAULT_WEBSITE}")
    print(f"🎨 Theme Pattern: First & Last = Light + Dark Header, Middle = Image")
    print(f"✨ NEW: Dark header gradient for white logo visibility")
    app.run(host='0.0.0.0', port=port, debug=False)
