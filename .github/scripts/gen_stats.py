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


def fetch_activity(username):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required to fetch activity for the rank.")
    query = """
        query($login: String!) {
          user(login: $login) {
            contributionsCollection {
              totalCommitContributions
              totalPullRequestReviewContributions
            }
            pullRequests { totalCount }
            issues { totalCount }
          }
        }
    """
    request = Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"login": username}}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "profile-stats-generator",
        },
    )
    with urlopen(request, timeout=30) as response:
        result = json.load(response)
    if result.get("errors"):
        raise RuntimeError(f"GitHub activity query failed: {result['errors']}")
    user = result["data"]["user"]
    return {
        "commits": user["contributionsCollection"]["totalCommitContributions"],
        "reviews": user["contributionsCollection"]["totalPullRequestReviewContributions"],
        "prs": user["pullRequests"]["totalCount"],
        "issues": user["issues"]["totalCount"],
    }


def calculate_rank(activity, stars, followers):
    # Port of GitHub Readme Stats' calculateRank.js (include_all_commits=false).
    # https://github.com/anuraghazra/github-readme-stats/blob/master/src/calculateRank.js
    # Copyright (c) 2020 Anurag Hazra; MIT license in licenses/github-readme-stats.txt.
    def exponential_cdf(value):
        return 1 - 2 ** -value

    def log_normal_cdf(value):
        return value / (1 + value)

    score = (
        2 * exponential_cdf(activity["commits"] / 250)
        + 3 * exponential_cdf(activity["prs"] / 50)
        + exponential_cdf(activity["issues"] / 25)
        + exponential_cdf(activity["reviews"] / 2)
        + 4 * log_normal_cdf(stars / 50)
        + log_normal_cdf(followers / 10)
    ) / 12
    percentile = (1 - score) * 100
    for threshold, level in zip(
        [1, 12.5, 25, 37.5, 50, 62.5, 75, 87.5, 100],
        ["S", "A+", "A", "A-", "B+", "B", "B-", "C+", "C"],
    ):
        if percentile <= threshold:
            return level, percentile
    raise ValueError("Rank outside the expected range.")


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


def render_stats(user, repos, activity):
    stars = sum(repo["stargazers_count"] for repo in repos)
    level, percentile = calculate_rank(activity, stars, user["followers"])
    values = [
        ("Public repositories", user["public_repos"]),
        ("Stars earned", stars),
        ("Repository forks", sum(repo["forks_count"] for repo in repos)),
        ("Followers", user["followers"]),
    ]
    rows = []
    for index, (label, value) in enumerate(values):
        y = 75 + index * 35
        rows.append(
            f'  <text class="label" x="24" y="{y}" font-size="14">{label}</text>\n'
            f'  <text class="value" x="265" y="{y}" text-anchor="end" '
            f'font-size="16" font-weight="600">{value:,}</text>'
        )
    rows.append(
        '  <circle class="track" cx="370" cy="119" r="49" />\n'
        '  <circle class="background" cx="370" cy="119" r="43" />\n'
        '  <text class="heading" x="370" y="130" text-anchor="middle" '
        f'font-size="32" font-weight="700">{level}</text>\n'
        '  <text class="label" x="370" y="188" text-anchor="middle" '
        'font-size="12">GitHub rank</text>\n'
        '  <text class="label" x="24" y="212" font-size="10">'
        "Rank: GitHub Readme Stats formula; commits/reviews: past year.</text>\n"
        '  <text class="label" x="24" y="228" font-size="10">'
        "Stars and forks exclude forked repositories.</text>"
    )
    description = ". ".join(f"{label}: {value:,}" for label, value in values)
    description += (
        f". Rank: {level} (formula percentile: {percentile:.1f}). "
        f"Rank inputs: {activity['commits']} commits and {activity['reviews']} reviews "
        f"in the past year, {activity['prs']} pull requests and "
        f"{activity['issues']} issues in total. "
        "An activity indicator, not a code quality assessment."
    )
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

    activity = fetch_activity(username)
    # Fetch all data before writing either file: API errors leave the old cards intact.
    stats_svg = render_stats(user, repos, activity)
    languages_svg = render_languages(languages)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "github-stats.svg").write_text(stats_svg, encoding="utf-8")
    (OUTPUT / "top-languages.svg").write_text(languages_svg, encoding="utf-8")
    print(f"Generated cards for {username}: {len(repos)} non-fork repositories.")


if __name__ == "__main__":
    main()
