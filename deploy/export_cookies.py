#!/usr/bin/env python3
"""
Cookie Export Script - Run on your LOCAL Windows machine
Exports YouTube cookies from Firefox/Chrome for use on the server.

Usage:
    python export_cookies.py

Then upload the generated cookies.txt to your Ubuntu server:
    scp cookies.txt user@server:/opt/discordbot/
"""

import sys
import os
from datetime import datetime

def export_cookies():
    """Export YouTube cookies from browser to cookies.txt"""

    try:
        import browser_cookie3
    except ImportError:
        print("Installing browser_cookie3...")
        os.system(f"{sys.executable} -m pip install browser_cookie3")
        import browser_cookie3

    print("YouTube Cookie Exporter")
    print("=" * 40)

    cookies_found = []

    # Try Firefox first
    try:
        print("\n[1] Checking Firefox...")
        firefox_cookies = browser_cookie3.firefox(domain_name='.youtube.com')
        cookies_found.extend(list(firefox_cookies))
        print(f"    Found {len(list(browser_cookie3.firefox(domain_name='.youtube.com')))} cookies")
    except Exception as e:
        print(f"    Firefox: {e}")

    # Try Chrome
    try:
        print("[2] Checking Chrome...")
        chrome_cookies = browser_cookie3.chrome(domain_name='.youtube.com')
        cookies_found.extend(list(chrome_cookies))
        print(f"    Found cookies from Chrome")
    except Exception as e:
        print(f"    Chrome: {e}")

    # Try Edge
    try:
        print("[3] Checking Edge...")
        edge_cookies = browser_cookie3.edge(domain_name='.youtube.com')
        cookies_found.extend(list(edge_cookies))
        print(f"    Found cookies from Edge")
    except Exception as e:
        print(f"    Edge: {e}")

    if not cookies_found:
        print("\n[!] No YouTube cookies found!")
        print("    Make sure you're logged into YouTube in your browser.")
        return False

    # Filter for YouTube-specific cookies
    yt_cookies = [c for c in cookies_found if 'youtube.com' in c.domain]

    # Write to Netscape format
    output_file = "cookies.txt"
    with open(output_file, 'w') as f:
        f.write("# Netscape HTTP Cookie File\n")
        f.write("# https://curl.haxx.se/rfc/cookie_spec.html\n")
        f.write(f"# Exported: {datetime.now().isoformat()}\n")
        f.write("# This is a generated file! Do not edit.\n\n")

        seen = set()
        for cookie in yt_cookies:
            # Deduplicate
            key = (cookie.domain, cookie.name)
            if key in seen:
                continue
            seen.add(key)

            f.write(
                f"{cookie.domain}\t"
                f"{'TRUE' if cookie.domain.startswith('.') else 'FALSE'}\t"
                f"{cookie.path}\t"
                f"{'TRUE' if cookie.secure else 'FALSE'}\t"
                f"{int(cookie.expires) if cookie.expires else '0'}\t"
                f"{cookie.name}\t"
                f"{cookie.value}\n"
            )

    print(f"\n[OK] Exported {len(seen)} unique cookies to {output_file}")
    print(f"\nNext step: Upload to your server:")
    print(f"    scp {output_file} user@your-server:/opt/discordbot/")
    print(f"    ssh user@your-server 'sudo chown discordbot:discordbot /opt/discordbot/cookies.txt'")

    return True


if __name__ == "__main__":
    try:
        export_cookies()
    except KeyboardInterrupt:
        print("\nCancelled.")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
