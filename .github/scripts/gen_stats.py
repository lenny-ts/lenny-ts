"""Generate GitHub profile cards using the API and Python's standard library."""

import json
import os
from collections import Counter
from html import escape
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "assets" / "stats"


def api(path):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "profile-stats-generator",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"https://api.github.com{path}", headers=headers)
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def card(title, description, content):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="460" height="240" viewBox="0 0 460 240" role="img" aria-labelledby="title description">
  <title id="title">{escape(title)}</title>
  <desc id="description">{escape(description)}</desc>
  <style>
    .background {{ fill: #ffffff; stroke: #d1d9e0; }}
    .heading {{ fill: #8250df; }}
    .label {{ fill: #59636e; }}
    .value {{ fill: #1f2328; }}
    .track {{ fill: #eaeef2; }}
    text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    @media (prefers-color-scheme: dark) {{
      .background {{ fill: #0d1117; stroke: #3d444d; }}
      .heading {{ fill: #bc8cff; }}
      .label {{ fill: #9198a1; }}
      .value {{ fill: #f0f6fc; }}
      .track {{ fill: #212830; }}
    }}
  </style>
  <rect class="background" x="0.5" y="0.5" width="459" height="239" rx="10" />
  <text class="heading" x="24" y="35" font-size="18" font-weight="600">{escape(title)}</text>
{content}
</svg>
'''


def render_stats(user, repos):
    values = [
        ("Public repositories", user["public_repos"]),
        ("Stars earned", sum(repo["stargazers_count"] for repo in repos)),
        ("Repository forks", sum(repo["forks_count"] for repo in repos)),
        ("Followers", user["followers"]),
    ]
    rows = []
    for index, (label, value) in enumerate(values):
        y = 75 + index * 35
        rows.append(
            f'  <text class="label" x="24" y="{y}" font-size="14">{label}</text>\n'
            f'  <text class="value" x="432" y="{y}" text-anchor="end" '
            f'font-size="16" font-weight="600">{value:,}</text>'
        )
    rows.append(
        '  <text class="label" x="24" y="218" font-size="11">'
        "Stars and forks exclude forked repositories.</text>"
    )
    description = ". ".join(f"{label}: {value:,}" for label, value in values)
    return card("GitHub statistics", description, "\n".join(rows))


def render_languages(languages):
    top = languages.most_common(5)
    total = sum(languages.values())
    colors = ["#8250df", "#2f81f7", "#3fb950", "#d29922", "#db6d28"]
    rows = []
    for index, ((language, size), color) in enumerate(zip(top, colors)):
        percent = size / total * 100
        y = 65 + index * 29
        rows.append(
            f'  <text class="value" x="24" y="{y}" font-size="13">{escape(language)}</text>\n'
            f'  <text class="label" x="432" y="{y}" text-anchor="end" font-size="12">'
            f'{percent:.1f}%</text>\n'
            f'  <rect class="track" x="24" y="{y + 6}" width="408" height="5" rx="2.5" />\n'
            f'  <rect x="24" y="{y + 6}" width="{408 * percent / 100:.2f}" '
            f'height="5" rx="2.5" fill="{color}" />'
        )
    if not top:
        rows.append(
            '  <text class="label" x="24" y="90" font-size="14">'
            "No public language data available.</text>"
        )
    rows.append(
        '  <text class="label" x="24" y="228" font-size="11">'
        "By code size across public, non-fork repositories.</text>"
    )
    description = ". ".join(
        f"{language}: {size / total * 100:.1f}%" for language, size in top
    )
    return card("Most used languages", description or "No language data", "\n".join(rows))


def main():
    username = os.environ.get("PROFILE_USERNAME", "lenny-ts")
    user_path = f"/users/{quote(username, safe='')}"
    user = api(user_path)
    repos = []
    page = 1
    while True:
        batch = api(f"{user_path}/repos?type=owner&per_page=100&page={page}")
        repos.extend(repo for repo in batch if not repo["fork"])
        if len(batch) < 100:
            break
        page += 1

    languages = Counter()
    for repo in repos:
        languages.update(api(f"/repos/{repo['full_name']}/languages"))

    # Fetch all data before writing either file: API errors leave the old cards intact.
    stats_svg = render_stats(user, repos)
    languages_svg = render_languages(languages)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "github-stats.svg").write_text(stats_svg, encoding="utf-8")
    (OUTPUT / "top-languages.svg").write_text(languages_svg, encoding="utf-8")
    print(f"Generated cards for {username}: {len(repos)} non-fork repositories.")


if __name__ == "__main__":
    main()
