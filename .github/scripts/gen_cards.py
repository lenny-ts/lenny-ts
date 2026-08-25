import html
import json
import os
import urllib.request
from PIL import ImageFont

W, H = 480, 180
MAX_LINES = 3
USABLE = 428
DESC_SIZE = 13

BG = "#0d1117"
BORDER = "#30363d"
ACCENT = "#2f81f7"
MUTED = "#8b949e"

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
font = ImageFont.truetype(FONT_PATH, DESC_SIZE)
meta_font = ImageFont.truetype(FONT_PATH, 13)

REPO_ICON = (
    "M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 "
    "0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 "
    "1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 "
    "1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 "
    ".25-.25h3.5a.25.25 0 0 1 .25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087"
    "a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z"
)
STAR_ICON = (
    "M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 "
    ".416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 "
    "12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75"
    ".75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Zm0 "
    "2.445L6.615 5.5a.75.75 0 0 1-.564.41l-3.097.45 2.24 2.184a.75.75 0 "
    "0 1 .216.664l-.528 3.084 2.769-1.456a.75.75 0 0 1 .698 0l2.77 "
    "1.456-.53-3.084a.75.75 0 0 1 .216-.664l2.24-2.183-3.096-.45a.75.75 "
    "0 0 1-.564-.41L8 2.694Z"
)
FORK_ICON = (
    "M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75v-.878"
    "a2.25 2.25 0 1 1 1.5 0v.878a2.25 2.25 0 0 1-2.25 2.25h-1.5v2.128"
    "a2.251 2.251 0 1 1-1.5 0V8.5h-1.5A2.25 2.25 0 0 1 3.5 6.25v-.878"
    "a2.25 2.25 0 1 1 1.5 0ZM5 3.25a.75.75 0 1 0-1.5 0 .75.75 0 0 0 "
    "1.5 0Zm6.75.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm-3 8.75a.75."
    "75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Z"
)

REPO_OWNER = "lenny-ts"

REPOS = [
    {
        "name": "league_profile_tool",
        "desc": "Hextech-inspired tool for League of Legends profile customization. Built with Tauri v2 & React. Features real-time LCU sync, custom status management, and automated updates.",
        "lang": "TypeScript",
        "color": "#3178c6",
    },
    {
        "name": "caddy-analyzer",
        "desc": "Fast, zero-dependency access log analyzer, security threat inspector, and TUI dashboard for Caddy v2. Real-time traffic stats, bot detection, and geo-IP lookups.",
        "lang": "Go",
        "color": "#00ADD8",
    },
    {
        "name": "tdl",
        "owner": "iyear",
        "desc": "A Telegram toolkit written in Golang. Migrate chats, export messages, and manage sessions from the CLI. Supports concurrent downloads and bulk operations.",
        "lang": "Go",
        "color": "#00ADD8",
    },
    {
        "name": "homebutler",
        "owner": "Higangssh",
        "desc": "Manage your homelab from chat. Single binary, zero dependencies.",
        "lang": "Go",
        "color": "#00ADD8",
    },
    {
        "name": "velachess",
        "owner": "velachess",
        "desc": "Turn your games into better chess. Syncs chess.com and Lichess games, builds your opening book from your own play, and turns mistakes into spaced-repetition drills.",
        "lang": "TypeScript",
        "color": "#3178c6",
    },
]


def repo_slug(r):
    return f'{r.get("owner", REPO_OWNER)}/{r["name"]}'


def card_title(r):
    return r["name"] if r.get("owner", REPO_OWNER) == REPO_OWNER else repo_slug(r)


def fetch_repo_data(r):
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"https://api.github.com/repos/{repo_slug(r)}"
    req = urllib.request.Request(url, headers=headers)
    try:
        data = json.loads(urllib.request.urlopen(req).read())
        stars = data.get("stargazers_count", 0)
        forks = data.get("forks_count", 0)
        return stars, forks
    except Exception as e:
        print(f"  WARN: could not fetch {repo_slug(r)}: {e}")
        return 0, 0


def wrap(text):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        cand = (cur + " " + w).strip()
        if font.getlength(cand) <= USABLE:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if len(lines) > MAX_LINES:
        lines = lines[:MAX_LINES]
        last = lines[-1]
        while font.getlength(last + "…") > USABLE and last:
            last = last[:-1]
        lines[-1] = last.rstrip() + "…"
    while len(lines) < MAX_LINES:
        lines.append("")
    return lines


def esc(t):
    return html.escape(t, quote=True)


def fmt_count(n):
    if n >= 1_000_000:
        v = f"{n / 1_000_000:.1f}".rstrip("0").rstrip(".")
        return f"{v}m"
    if n >= 1000:
        v = f"{n / 1000:.1f}".rstrip("0").rstrip(".")
        return f"{v}k"
    return str(n)


def icon(d, x, y_top, size=13, color=MUTED):
    s = size / 16
    return (
        f'  <g transform="translate({x:.2f},{y_top:.2f}) scale({s:.5f})" '
        f'fill="{color}"><path d="{d}"/></g>'
    )


def card(r, stars, forks):
    title = card_title(r)
    lines = wrap(r["desc"])
    parts = []
    parts.append(
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'xmlns="http://www.w3.org/2000/svg" '
        f"font-family=\"'DejaVu Sans', system-ui, -apple-system, 'Segoe UI', "
        f"Roboto, Helvetica, Arial, sans-serif\" role=\"img\" "
        f'aria-label="{esc(title)}">'
    )
    parts.append(f'  <rect width="{W}" height="{H}" fill="{BG}"/>')
    parts.append(
        f'  <rect width="{W}" height="{H}" rx="6" fill="none" stroke="{BORDER}"/>'
    )

    icon_x = 20
    title_x = icon_x + 16 + 7
    parts.append(icon(REPO_ICON, icon_x, 18.5, size=16, color=MUTED))
    parts.append(
        f'  <text x="{title_x}" y="32" font-size="14" font-weight="600" '
        f'fill="{ACCENT}" xml:space="preserve">{esc(title)}</text>'
    )

    y = 62
    for ln in lines:
        if ln:
            parts.append(
                f'  <text x="20" y="{y}" font-size="{DESC_SIZE}" '
                f'fill="{MUTED}" xml:space="preserve">{esc(ln)}</text>'
            )
        y += 20

    baseline = 156
    mid = baseline - 4.75
    x = 20.0
    parts.append(f'  <circle cx="{x + 5:.2f}" cy="{mid - 0.25:.2f}" r="5" fill="{r["color"]}"/>')
    x += 10 + 6
    parts.append(
        f'  <text x="{x:.2f}" y="{baseline}" font-size="13" fill="{MUTED}" '
        f'xml:space="preserve">{esc(r["lang"])}</text>'
    )
    x += meta_font.getlength(r["lang"]) + 16

    star_txt = fmt_count(stars)
    parts.append(icon(STAR_ICON, x, mid - 8.5, size=17))
    x += 17 + 5
    parts.append(
        f'  <text x="{x:.2f}" y="{baseline}" font-size="13" fill="{MUTED}" '
        f'xml:space="preserve">{star_txt}</text>'
    )
    x += meta_font.getlength(star_txt) + 16

    fork_txt = fmt_count(forks)
    parts.append(icon(FORK_ICON, x, mid - 8.5, size=17))
    x += 13 + 5
    parts.append(
        f'  <text x="{x:.2f}" y="{baseline}" font-size="13" fill="{MUTED}" '
        f'xml:space="preserve">{fork_txt}</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main():
    import cairosvg

    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    outdir = os.path.join(repo_root, "assets", "repos")
    os.makedirs(outdir, exist_ok=True)

    for r in REPOS:
        print(f"Fetching {repo_slug(r)}...")
        stars, forks = fetch_repo_data(r)
        print(f"  stars={stars}, forks={forks}")
        svg = card(r, stars, forks)
        svg_path = os.path.join(outdir, r["name"] + ".svg")
        png_path = os.path.join(outdir, r["name"] + ".png")
        with open(svg_path, "w") as f:
            f.write(svg)
        cairosvg.svg2png(bytestring=svg.encode(), write_to=png_path, output_width=960, output_height=360)
        print(f"  wrote {svg_path}, {png_path}")


if __name__ == "__main__":
    main()
