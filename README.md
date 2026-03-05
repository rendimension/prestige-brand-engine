# Prestige 360 Brand Engine

Image compositor for Prestige 360 Design social media automation.

## Features

- **Multi-theme support**: light, dark, image-heavy
- **Orange gradient underline**: Brand signature element
- **Logo integration**: Automatic logo placement
- **Text wrapping**: Auto-wrap and truncate long text
- **Vertical 4:5 format**: Optimized for Instagram/Facebook

## Brand Colors

- Primary: `#FF3131` → `#F26A21` (orange gradient)
- Text: White (dark theme) / Black (light theme)

## API Endpoints

### POST /render-slide

Main endpoint for n8n automation.

**Request body:**
```json
{
  "image_url": "https://example.com/image.jpg",
  "headline": "Your headline text",
  "subtitle": "Supporting text",
  "theme": "dark",
  "show_website": true
}
```

**Themes:**
- `light` - White overlay, black text
- `dark` - Dark gradients, white text (default)
- `image` - Minimal overlay, image-focused

**Response:**
```json
{
  "success": true,
  "download_url": "https://xxx.railway.app/download/uuid",
  "png_url": "https://xxx.railway.app/post_output/slide_uuid.png"
}
```

## Environment Variables

- `BRAND_NAME` - Default: "PRESTIGE 360"
- `TAGLINE` - Default: "Commercial Design From Concept to Opening"
- `WEBSITE_URL` - Default: "www.prestige360design.com"
- `LOGO_URL` - Default: "https://i.imgur.com/IvU0SRy.png"

## Deployment

Deploy to Railway and set environment variables as needed.
