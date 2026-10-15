"""Builds tv.json: live sports broadcasts on French TV for the next two weeks.

Source: the French TV guide from xmltvfr.fr (https://github.com/racacax/XML-TV-Fr).
Game On matches its games against this file to show the exact channel (Canal+ Foot, beIN SPORTS MAX 4…).
"""
import gzip
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

SOURCE = "https://xmltvfr.fr/xmltv/xmltv_fr.xml.gz"

# Channels that broadcast live sport in France (XMLTV ids).
SPORT_CHANNELS = re.compile(
    r"^(CanalPlus(Foot|Sport|Sport360|Live\d+|PremierLeague|Ligue1)?|beINSPORTS\w*|RMCSport\d|DAZN\d?|"
    r"Ligue1Plus\d*|Eurosport[12]|LEquipe\w*|InfosportPlus|TF1|M6|France[234]|TMC|W9|NT1)\.fr$"
)
SPORT_WORDS = re.compile(r"sport|football|basket|rugby|mma|ufc|tennis|handball|hockey|nfl|nba", re.I)
MIN_LENGTH = timedelta(minutes=60)  # a live game; skips magazines and short highlights
DAYS_BACK, DAYS_AHEAD = 1, 14


def parse_time(value: str) -> datetime:
    # XMLTV: "20261020205500 +0200"
    return datetime.strptime(value, "%Y%m%d%H%M%S %z")


def main(path: str | None = None) -> None:
    now = datetime.now(timezone.utc)
    window = (now - timedelta(days=DAYS_BACK), now + timedelta(days=DAYS_AHEAD))
    if path:
        stream = gzip.open(path)
    else:
        request = urllib.request.Request(SOURCE, headers={"User-Agent": "game-on-tv (personal TV guide filter)"})
        stream = gzip.GzipFile(fileobj=urllib.request.urlopen(request, timeout=300))

    names: dict[str, str] = {}
    programmes = []
    for _, element in ET.iterparse(stream, events=("end",)):
        if element.tag == "channel":
            channel_id = element.get("id", "")
            if SPORT_CHANNELS.match(channel_id):
                names[channel_id] = element.findtext("display-name", channel_id).strip()
            element.clear()
        elif element.tag == "programme":
            channel_id = element.get("channel", "")
            if channel_id in names:
                start, stop = parse_time(element.get("start")), parse_time(element.get("stop"))
                title = (element.findtext("title") or "").strip()
                subtitle = (element.findtext("sub-title") or "").strip()
                categories = " ".join(c.text or "" for c in element.findall("category"))
                if (window[0] <= start <= window[1] and stop - start >= MIN_LENGTH
                        and SPORT_WORDS.search(f"{categories} {title} {subtitle}")):
                    programmes.append({
                        "start": start.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                        "end": stop.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                        "channel": names[channel_id],
                        "title": title,
                        "subtitle": subtitle,
                    })
            element.clear()

    programmes.sort(key=lambda p: (p["start"], p["channel"]))
    with open("tv.json", "w", encoding="utf-8") as f:
        json.dump({"updated": now.isoformat(), "programmes": programmes}, f, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(programmes)} programmes on {len(names)} channels")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
