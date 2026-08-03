import re
import html
from email.utils import format_datetime
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

URL = "https://www.jftna.org/jft/"
OUT = "jftna.xml"

req = Request(URL, headers={"User-Agent": "Mozilla/5.0"})
with urlopen(req, timeout=30) as r:
    page = r.read().decode("utf-8", errors="replace")

text = re.sub(r"<script[\s\S]*?</script>", "", page, flags=re.I)
text = re.sub(r"<style[\s\S]*?</style>", "", text, flags=re.I)
text = re.sub(r"<[^>]+>", "\n", text)
text = html.unescape(text)
text = re.sub(r"\r", "", text)
lines = [re.sub(r"\s+", " ", line).strip() for line in text.split("\n")]
lines = [line for line in lines if line]
joined = "\n".join(lines)

m = re.search(r"([A-Za-z]+ \d{2}, \d{4})\n([\s\S]*?)\nPage (\d+)", joined)
if not m:
    raise SystemExit("Could not parse date/title/page from source page")

date_str = m.group(1)
title_block = m.group(2).strip().split("\n")
title = next((x for x in title_block if len(x) > 2), "Just for Today")
page_no = m.group(3)

jft_match = re.search(r"Just for Today:\s*\n?([\s\S]*?)(?:Copyright|All Rights Reserved)", joined, flags=re.I)
jft_line = jft_match.group(1).strip().replace("\n", " ") if jft_match else ""

quote_match = re.search(rf"{re.escape(title)}\nPage {page_no}\n\"\n?([\s\S]*?)\n\"", joined)
quote = quote_match.group(1).strip().replace("\n", " ") if quote_match else ""

desc_parts = []
if page_no:
    desc_parts.append(f"Page {page_no}.")
if quote:
    desc_parts.append(f"\"{quote}\"")
if jft_line:
    desc_parts.append(f"Just for Today: {jft_line}")
description = " ".join(desc_parts).strip()

pub_dt = datetime.strptime(date_str, "%B %d, %Y").replace(tzinfo=timezone.utc)
build_dt = datetime.now(timezone.utc)
guid = f"{URL}#{pub_dt.strftime('%Y-%m-%d')}"

rss = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Just for Today Meditation</title>
    <link>{escape(URL)}</link>
    <description>Unofficial RSS feed generated from the Just for Today Meditation page.</description>
    <language>en-us</language>
    <lastBuildDate>{format_datetime(build_dt)}</lastBuildDate>
    <item>
      <title>{escape(date_str)} - {escape(title)}</title>
      <link>{escape(URL)}</link>
      <guid>{escape(guid)}</guid>
      <pubDate>{format_datetime(pub_dt)}</pubDate>
      <description><![CDATA[{description}]]></description>
    </item>
  </channel>
</rss>
'''

with open(OUT, "w", encoding="utf-8") as f:
    f.write(rss)
