from flask import Flask, request, Response
from bs4 import BeautifulSoup
import html2text
import feedparser
import html
import base64
import requests
from io import BytesIO

app = Flask(__name__)

@app.route("/", methods=["GET"])
def preview_card_svg():
    # Get and validate query parameters
    username = request.args.get('user')
    if not username:
        return {"status": "error", "error": "Invalid or missing Medium username"}, 400

    try:
        index = int(request.args.get('index', 0))
        if index < 0:
            return {"status": "error", "error": "Index must be non-negative"}, 400
    except ValueError:
        return {"status": "error", "error": "Invalid index parameter"}, 400

    # Construct and parse the Medium RSS feed
    feed_url = f"https://medium.com/feed/@{username}"
    try:
        feed = feedparser.parse(feed_url)
        if feed.bozo:
            return {"status": "error", "error": "Invalid RSS feed"}, 400
        entries = feed.entries
    except Exception as e:
        return {"status": "error", "error": f"Failed to fetch feed: {str(e)}"}, 500

    if not entries:
        return {"status": "error", "error": "No articles found"}, 404

    if index >= len(entries):
        return {"status": "error", "error": "Article index out of range"}, 404

    # Process the selected article
    entry = entries[index]
    text = html2text.HTML2Text()
    text.ignore_links = True

    content_html = entry.get('content', [{'value': ''}])[0]['value']
    if not content_html:
        content_html = entry.get('summary', '')

    # Get thumbnail
    thumbnail = ''
    try:
        if 'media_thumbnail' in entry and entry.media_thumbnail:
            thumbnail = entry.media_thumbnail[0].get('url', '')
        if not thumbnail:
            soup = BeautifulSoup(content_html, 'html.parser')
            img = soup.find('img')
            thumbnail = img.get('src', '') if img else ''
    except Exception:
        thumbnail = ''
    
    # Extract categories and format as hashtags
    categories = entry.get('tags', [])
    if categories:
        # Handle case where tags are dictionaries (e.g., [{'term': 'cat1'}, ...])
        if isinstance(categories[0], dict):
            category_string = ' '.join(f"#{tag['term']}" for tag in categories if 'term' in tag)
        else:
            category_string = ' '.join(f"#{tag}" for tag in categories)
    else:
        category_string = ''
    
    # Convert thumbnail to base64
    thumbnail_base64 = ''
    if thumbnail:
        try:
            response = requests.get(thumbnail)
            if response.status_code == 200:
                image_data = BytesIO(response.content)
                thumbnail_base64 = f"data:image/jpeg;base64,{base64.b64encode(image_data.read()).decode('utf-8')}"
        except Exception:
            thumbnail_base64 = ''

    article = {
        "title": entry.title[:50] + "..." if len(entry.title) > 50 else entry.title,
        "link": entry.link,
        "thumbnail": thumbnail_base64,
        "published": ' '.join(entry.get('published', '').split()[:4]),
        "categories": category_string
    }

    # Generate SVG with new template and previous size
    card_height = 160
    svg_content = []

    svg_content.append(f"""
<svg id="visual" viewBox="0 0 800 {card_height}" width="800" height="{card_height}" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1">
    <defs>
        <filter id="blur1" x="-10%" y="-10%" width="120%" height="120%">
            <feFlood flood-opacity="0" result="BackgroundImageFix"></feFlood>
            <feBlend mode="normal" in="SourceGraphic" in2="BackgroundImageFix" result="shape"></feBlend>
            <feGaussianBlur stdDeviation="53" result="effect1_foregroundBlur"></feGaussianBlur>
        </filter>
        <linearGradient id="contentGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#db2777;stop-opacity:0.8"/> <!-- Pinkish -->
            <stop offset="100%" style="stop-color:#7c3aed;stop-opacity:0.8"/> <!-- Purple -->
        </linearGradient>
    </defs>
    <rect width="800" height="{card_height}" fill="#F7CACA"></rect>
    <g filter="url(#blur1)">
        <circle cx="419" cy="24" fill="#001122" r="357"></circle>
        <circle cx="24" cy="22" fill="#715DF2" r="357"></circle>
        <circle cx="700" cy="310" fill="#001122" r="357"></circle>
        <circle cx="566" cy="547" fill="#001122" r="357"></circle>
        <circle cx="174" cy="554" fill="#715DF2" r="357"></circle>
        <circle cx="322" cy="368" fill="#001122" r="357"></circle>
    </g>
    <foreignObject width="100%" height="100%">
        <div xmlns="http://www.w3.org/1999/xhtml">
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                }}
                @keyframes gradientShift {{
                    0% {{ background-position: 0% 50%; }}
                    50% {{ background-position: 100% 50%; }}
                    100% {{ background-position: 0% 50%; }}
                }}
                .container {{
                    display: flex;
                    width: 100%;
                    height: 100%;
                    min-height: {card_height}px;
                    background: linear-gradient(135deg, #db2777 0%, #7c3aed 100%);
                    background-size: 200% 200%;
                    animation: gradientShift 6s ease infinite;
                    border-radius: 12px;
                    margin: 10px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                    overflow: hidden;
                }}
                .thumbnail {{
                    width: 200px;
                    height: 100%;
                    object-fit: cover;
                    border-right: 1px solid rgba(255,255,255,0.2);
                }}
                .content {{
                    flex: 1;
                    padding: 15px;
                    color: #ffffff;
                }}
                a {{
                    text-decoration: none;
                    color: inherit;
                    display: flex;
                    width: 100%;
                    height: 100%;
                }}
                h3 {{
                    font-size: 18px;
                    font-weight: 600;
                    margin-bottom: 8px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }}
                .date {{
                    font-size: 14px;
                    opacity: 0.8;
                    margin-bottom: 10px;
                    display: block;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }}
                p {{
                    font-size: 16px;
                    line-height: 1.4;
                    opacity: 0.9;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    display: -webkit-box;
                    -webkit-line-clamp: 3;
                    -webkit-box-orient: vertical;
                }}
                .categories {{
                    font-size: 16px;
                    opacity: 0.8;
                    margin-bottom: 12px;
                    display: block;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }}
            </style>
            <div class="outer-container">
                <a class="container" href="{html.escape(article['link'])}" target="_blank">
                    <img class="thumbnail" src="{html.escape(article['thumbnail'] or 'https://via.placeholder.com/200')}" alt="Thumbnail"/>
                    <div class="content">
                        <h3>{html.escape(article['title'])}</h3>
                        <span class="date">{html.escape(article['published'])}</span>
                        <span class="categories">{html.escape(article['categories'])}</span>
                    </div>
                </a>
            </div>
        </div>
    </foreignObject>
</svg>
""")

    # Return SVG response
    return Response(''.join(svg_content), mimetype='image/svg+xml')

if __name__ == "__main__":
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
    )
