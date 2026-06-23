# News Aggregator

A command-line Python news aggregator that fetches live headlines from 10 RSS feeds

## Features

- Live headlines from 10 news sources
- Sorted by most recent first
- Keyword search across titles and summaries
- Filter by source or category (tech / world / us)
- Paginated browsing (20 articles per page)
- Article detail view with full summary
- One-command feed refresh

## Requirements

- Python 3.10+
- `feedparser` library

## Installation

```bash
pip install feedparser
```

## Usage

```bash
cd news_aggregator
python news_aggregator.py
```
## Notes

- SSL certificate verification is disabled to allow feeds that use self-signed or expired certificates. Only use this on trusted RSS URLs.
- Each source fetches up to 15 articles per refresh.
- Articles with no publication date are sorted to the bottom.
