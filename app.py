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
<svg fill="none" width="100%" height="100%" viewBox="0 0 1000 140" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">
    <foreignObject width="100%" height="100%">
        <div xmlns="http://www.w3.org/1999/xhtml">
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                    font-family: sans-serif;
                }}
                @keyframes gradientBackground {{
                    0% {{
                        background-position-x: 0%;
                    }}
                    100% {{
                        background-position-x: 100%;
                    }}
                }}
                .flex {{
                    display: flex;
                    align-items: center;
                    width: 100%;
                    height: 100%;
                }}
                .outer-container {{
                    width: 100%;
                    height: 100%;
                    min-height: 140px;
                }}
                .container {{
                    height: 100%;
                    width: 100%;
                    border: 1px solid rgba(0,0,0,.2);
                    padding: 10px 20px;
                    border-radius: 10px;
                    background: rgb(255,255,255);
                    background: linear-gradient(60deg, rgba(255,255,255,1) 0%, rgba(255,255,255,1) 47%, rgba(246,246,246,1) 50%, rgba(255,255,255,1) 53%, rgba(255,255,255,1) 100%);
                    background-size: 600% 400%;
                    animation: gradientBackground 3s ease infinite;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }}
                img {{
                    margin-right: 10px;
                    width: 150px;
                    height: 100%;
                    min-height: 98px; /* 140px - 2 * 10px padding - 2 * 1px border */
                    object-fit: cover;
                }}
                .right {{
                    flex: 1;
                    min-width: 0; /* This helps with text overflow */
                }}
                a {{
                    text-decoration: none;
                    color: inherit;
                }}
                p {{
                    line-height: 1.5;
                    color: #555;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    display: -webkit-box;
                    -webkit-line-clamp: 2;
                    -webkit-box-orient: vertical;
                }}
                h3 {{
                    color: #333;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }}
                small {{
                    color: #888;
                    display: block;
                    margin-top: 5px;
                    margin-bottom: 8px;
                }}
            </style>
            <div class="outer-container flex">
                <a class="container flex" href="{html.escape(article['link'])}" target="__blank">
                    <img src="{html.escape(article['thumbnail'] or 'https://via.placeholder.com/150')}" alt="Thumbnail"/>
                    <div class="right">
                        <h3>{html.escape(article['title'])}</h3>
                        <small>{html.escape(article['published'])}</small>
                        <p>{html.escape(article['categories'])}</p>
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
