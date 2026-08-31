#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from urllib import request, robotparser
from urllib.parse import urlparse


USER_AGENT = "EduVisionAI-MathLab-Discovery/1.0 (+metadata-only; respectful-crawler)"


def inspect_url(url: str, timeout: float) -> dict:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    robots = robotparser.RobotFileParser(robots_url)
    try:
        robots.read()
        allowed = robots.can_fetch(USER_AGENT, url)
        robots_checked = True
    except OSError:
        allowed = False
        robots_checked = False
    digest = ""
    status = None
    content_type = ""
    if allowed:
        req = request.Request(url, headers={"User-Agent": USER_AGENT})
        with request.urlopen(req, timeout=timeout) as response:
            status = response.status
            content_type = response.headers.get_content_type()
            digest = hashlib.sha256(response.read()).hexdigest()
    return {
        "url": url,
        "domain": parsed.netloc.lower(),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "content_hash": digest,
        "robots_checked": robots_checked,
        "robots_allowed": allowed,
        "http_status": status,
        "content_type": content_type,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect one URL without bypassing robots/login/paywall")
    parser.add_argument("url")
    parser.add_argument("--timeout", type=float, default=20)
    args = parser.parse_args()
    print(json.dumps(inspect_url(args.url, args.timeout), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
