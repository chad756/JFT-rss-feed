"""Builds jftna.xml: an RSS feed with today's NA "Just for Today" reading.

Primary source: https://jft.na.org/ (NA World Services)
Backup source:  https://www.uncoastna.org/justfortoday/justfortoday.aspx
If both fail, the existing jftna.xml is left untouched and the run exits with an error.
"""
import html
import re
import sys
import time
from datetime import datetime
from email.utils import format_datetime
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

OUT = "jftna.xml"
TZ = ZoneInfo("America/Edmonton")
SOURCES = [
    "https://jft.na.org/",
    "https://www.uncoastna.org/justfortoday/justfortoday.aspx",
]
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-CA,en;q=0.9",
}


def fetch(url):
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers=HEADERS), timeout=30) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            print(f"  {url} attempt {attempt + 1} failed: {e}")
            time.sleep(5)
    return None


def clean(fragment):
    fragment = re.sub(r"<br\s*/?>\s*<br\s*/?>", "\n\n", fragment, flags=re.I)
    fragment = re.sub(r"<[^>]+>", "", fragment)
    fragment = html.unescape(fragment)
    lines = [re.sub(r"\s+", " ", p).strip() for p in fragment.split("\n\n")]
    return "\n\n".join(p for p in lines if p)


def parse(page):
    # Only look at the first Just for Today block (the backup page also has
    # a Spiritual Principle a Day reading after it).
    page = re.sub(r"<!--[\s\S]*?-->", "", page)
    start = page.find("quote_today")
    if start == -1:
        return None
    block = page[start:]
    end = block.find("</table>")
    block = block[: end if end != -1 else None]

    cells = [clean(c) for c in re.findall(r"<td[^>]*>([\s\S]*?)</td>", block, flags=re.I)]
    cells = [c for c in cells if c and c != "."]
    if len(cells) < 5:
        return None

    date_str, title = cells[0], cells[1]
    page_no = next((c for c in cells if re.fullmatch(r"Page \d+", c)), "")
    quote = next((c for c in cells if c.startswith('"')), "").strip('"').strip()
    jft = next((c for c in cells if c.lower().startswith("just for today:")), "")
    jft = jft.split(":", 1)[1].strip() if jft else ""
    body = [c for c in cells if c not in (date_str, title, page_no, jft) and not c.startswith('"')
            and not c.lower().startswith("just for today:")]
    body = "\n\n".join(body)

    try:
        day = datetime.strptime(date_str, "%B %d, %Y").replace(tzinfo=TZ)
    except ValueError:
        return None
    if not (title and quote and jft):
        return None
    return dict(date_str=date_str, day=day, title=title, page_no=page_no,
                quote=quote, body=body, jft=jft)


def parse_backup(page):
    # Uncoast NA page: first "accordion-body meditation" block is Just for Today.
    m = re.search(r"Just For Today\s*(?:&mdash;|\u2014|-)\s*([A-Z][a-z]+ \d{1,2}, \d{4})", page)
    start = page.find("accordion-body meditation")
    if not m or start == -1:
        return None
    block = page[start:]
    end = block.find("meditation-source-link")
    block = block[: end if end != -1 else None]
    cells = [clean(c) for c in re.findall(r"<(?:p|blockquote)[^>]*>([\s\S]*?)</(?:p|blockquote)>", block, flags=re.I)]
    fake = "".join(f"<td>{escape(c)}</td>" for c in [m.group(1)] + cells)
    return parse('<div class="quote_today"><table>' + html.unescape(fake) + "</table>")


def main():
    data, used = None, None
    for url in SOURCES:
        print(f"Trying {url}")
        page = fetch(url)
        reader = parse_backup if "uncoastna" in url else parse
        data = reader(page) if page else None
        if data:
            used = url
            break
        print("  could not read the reading from this source")
    if not data:
        sys.exit("No source worked. Keeping the existing jftna.xml.")

    # Short description for signage: quote + daily affirmation.
    description = f'"{data["quote"]}" Just for Today: {data["jft"]}'
    full = "".join(f"<p>{escape(p)}</p>" for p in data["body"].split("\n\n"))
    full = (f"<p><em>{escape(data['quote'])}</em></p>{full}"
            f"<p><strong>Just for Today:</strong> {escape(data['jft'])}</p>")

    now = datetime.now(TZ)
    guid = f"https://jft.na.org/#{data['day']:%Y-%m-%d}"
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>Just for Today - Daily NA Meditation</title>
    <link>https://jft.na.org/</link>
    <description>Today's Just for Today reading from Narcotics Anonymous World Services. Copyright NA World Services, Inc. Internal use only.</description>
    <language>en-ca</language>
    <ttl>60</ttl>
    <lastBuildDate>{format_datetime(now)}</lastBuildDate>
    <item>
      <title>{escape(data['title'])}</title>
      <link>https://jft.na.org/</link>
      <guid isPermaLink="false">{escape(guid)}</guid>
      <pubDate>{format_datetime(data['day'])}</pubDate>
      <description>{escape(description)}</description>
      <content:encoded><![CDATA[{full}]]></content:encoded>
    </item>
  </channel>
</rss>
"""
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(rss)
    print(f"Wrote {OUT}: {data['date_str']} - {data['title']} (from {used})")


if __name__ == "__main__":
    main()
