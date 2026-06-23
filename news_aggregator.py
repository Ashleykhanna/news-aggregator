import feedparser
import datetime
import textwrap
import ssl
import re
import urllib.request
from dataclasses import dataclass
from typing import Optional


_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE


def _fetch_raw(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=_ssl_ctx, timeout=10) as r:
        return r.read()


FEEDS = {
    "BBC News":       "http://feeds.bbci.co.uk/news/rss.xml",
    "The Guardian":   "https://www.theguardian.com/world/rss",
    "Hacker News":    "https://hnrss.org/frontpage",
    "Ars Technica":   "https://feeds.arstechnica.com/arstechnica/index",
    "The Verge":      "https://www.theverge.com/rss/index.xml",
    "CNN":            "http://rss.cnn.com/rss/cnn_topstories.rss",
    "NPR":            "https://feeds.npr.org/1001/rss.xml",
    "TechCrunch":     "https://techcrunch.com/feed/",
    "ABC News":       "https://feeds.abcnews.com/abcnews/topstories",
    "Al Jazeera":     "https://www.aljazeera.com/xml/rss/all.xml",
}

CATEGORIES = {
    "tech":    ["Hacker News", "Ars Technica", "The Verge", "TechCrunch"],
    "world":   ["BBC News", "The Guardian", "Reuters", "Al Jazeera"],
    "us":      ["CNN", "NPR", "ABC News"],
}


@dataclass
class Article:
    title: str
    source: str
    link: str
    published: Optional[str] = None
    summary: Optional[str] = None

    def display(self, index: int, show_summary: bool = False):
        print(f"\n  [{index:>3}] {self.title}")
        print(f"        Source : {self.source}")
        if self.published:
            print(f"        Date   : {self.published}")
        print(f"        Link   : {self.link}")
        if show_summary and self.summary:
            wrapped = textwrap.fill(
                self.summary, width=78,
                initial_indent="        ", subsequent_indent="        "
            )
            print(f"        Summary:\n{wrapped}")


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def fetch_feed(source_name: str, url: str) -> list[Article]:
    articles = []
    try:
        raw = _fetch_raw(url)
        feed = feedparser.parse(raw)
        for entry in feed.entries[:15]:
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                dt = datetime.datetime(*entry.published_parsed[:6])
                published = dt.strftime("%Y-%m-%d %H:%M")
            summary = _strip_html(getattr(entry, "summary", "") or "")
            articles.append(Article(
                title=_strip_html(entry.get("title", "No title")),
                source=source_name,
                link=entry.get("link", ""),
                published=published,
                summary=summary or None,
            ))
    except Exception as e:
        print(f"  [!] Failed to fetch {source_name}: {e}")
    return articles


def fetch_sources(sources: dict[str, str]) -> list[Article]:
    all_articles: list[Article] = []
    for name, url in sources.items():
        print(f"  Fetching {name}...", end=" ", flush=True)
        arts = fetch_feed(name, url)
        print(f"{len(arts)} articles")
        all_articles.extend(arts)
    return all_articles


def sort_by_date(articles: list[Article]) -> list[Article]:
    return sorted(articles, key=lambda a: a.published or "", reverse=True)


def search(articles: list[Article], query: str) -> list[Article]:
    q = query.lower()
    return [a for a in articles if q in a.title.lower() or (a.summary and q in a.summary.lower())]


def filter_by_source(articles: list[Article], source: str) -> list[Article]:
    return [a for a in articles if source.lower() in a.source.lower()]


def filter_by_category(articles: list[Article], cat: str) -> list[Article]:
    sources = CATEGORIES.get(cat.lower(), [])
    return [a for a in articles if a.source in sources]


def print_menu():
    print("""
┌─────────────────────────────────────┐
│         NEWS AGGREGATOR             │
├─────────────────────────────────────┤
│  1. Show all headlines              │
│  2. Search articles                 │
│  3. Filter by source                │
│  4. Filter by category (tech/world) │
│  5. Read article detail             │
│  6. Refresh feeds                   │
│  7. List sources                    │
│  q. Quit                            │
└─────────────────────────────────────┘""")


def paginate(articles: list[Article], page_size: int = 20):
    """Show articles page by page."""
    total = len(articles)
    start = 0
    while start < total:
        end = min(start + page_size, total)
        for i, a in enumerate(articles[start:end], start + 1):
            a.display(i)
        if end >= total:
            break
        more = input(f"\n  Showing {end}/{total}. Press Enter for more, or 'q' to stop: ").strip().lower()
        if more == "q":
            break
        start = end


def run():
    print("\nFetching news feeds...")
    articles = sort_by_date(fetch_sources(FEEDS))
    print(f"\nLoaded {len(articles)} articles.\n")

    while True:
        print_menu()
        choice = input("Choose: ").strip().lower()

        if choice == "q":
            print("Goodbye!")
            break

        elif choice == "1":
            paginate(articles)

        elif choice == "2":
            query = input("Search: ").strip()
            results = search(articles, query)
            if results:
                print(f"\n  {len(results)} result(s) for '{query}':")
                for i, a in enumerate(results, 1):
                    a.display(i, show_summary=True)
            else:
                print(f"  No results for '{query}'.")

        elif choice == "3":
            print("\n  Sources: " + ", ".join(FEEDS.keys()))
            source = input("  Enter source name (partial ok): ").strip()
            results = filter_by_source(articles, source)
            if results:
                paginate(results)
            else:
                print(f"  No articles for '{source}'.")

        elif choice == "4":
            print(f"\n  Categories: {', '.join(CATEGORIES.keys())}")
            cat = input("  Category: ").strip()
            results = filter_by_category(articles, cat)
            if results:
                print(f"\n  {len(results)} articles in '{cat}':")
                paginate(results)
            else:
                print(f"  Unknown category '{cat}'.")

        elif choice == "5":
            try:
                idx = int(input("  Article number: ").strip()) - 1
                if 0 <= idx < len(articles):
                    articles[idx].display(idx + 1, show_summary=True)
                else:
                    print("  Invalid number.")
            except ValueError:
                print("  Enter a valid number.")

        elif choice == "6":
            print("\n  Refreshing...")
            articles = sort_by_date(fetch_sources(FEEDS))
            print(f"  {len(articles)} articles loaded.")

        elif choice == "7":
            print("\n  Configured sources:")
            for name, url in FEEDS.items():
                cat = next((c for c, srcs in CATEGORIES.items() if name in srcs), "—")
                print(f"    {name:20s}  [{cat}]  {url}")

        else:
            print("  Unknown option.")


if __name__ == "__main__":
    run()
