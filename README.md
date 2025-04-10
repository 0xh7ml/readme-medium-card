# Awesome Medium Card

![Awesome Medium Card](https://img.shields.io/badge/Awesome-Medium%20Card-blueviolet?style=flat-square)  
Generate stylish SVG cards for your Medium articles to showcase in your GitHub README, featuring a blurred-circle design, middle content previews, and categories.

## Overview

Awesome Medium Card is a Flask-based tool that fetches your Medium articles via RSS and creates visually appealing SVG cards. Each card displays a thumbnail, title, publication date (no time), categories (e.g., `#tech #ai`), and a preview from the article’s middle content, all overlaid on a unique purple blurred-circle background.

## Usage

```markdown
![Latest Article](https://your-deployed-url.com/user=your_medium_username&index=0)

![Second Article](https://your-deployed-url.com/?user=your_medium_username&index=1)
```