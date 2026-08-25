import html
import json
import os
import urllib.request
from PIL import ImageFont

W, H = 480, 180
MAX_LINES = 3
USABLE = 428
DESC_SIZE = 13

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
font = ImageFont.truetype(FONT_PATH, DESC_SIZE)

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
    parts.append(f'  <rect width="{W}" height="{H}" fill="#1a1b27"/>')
    parts.append(f'  <rect width="{W}" height="{H}" rx="8" fill="none" stroke="#2f3352"/>')
    parts.append(
        f'  <text x="20" y="32" font-size="16" font-weight="700" '
        f'fill="#e1e4e8" xml:space="preserve">{esc(title)}</text>'
    )
    y = 62
    for ln in lines:
        if ln:
            parts.append(
                f'  <text x="20" y="{y}" font-size="{DESC_SIZE}" '
                f'fill="#9da7d3" xml:space="preserve">{esc(ln)}</text>'
            )
        y += 20
    parts.append(f'  <circle cx="20" cy="151" r="4" fill="{r["color"]}"/>')
    parts.append(
        f'  <text x="32" y="156" font-size="13" fill="#9da7d3" '
        f'xml:space="preserve">{esc(r["lang"])}</text>'
    )
    parts.append(
        f'  <text x="418" y="158" font-size="18" text-anchor="end" '
        f'fill="#9da7d3" xml:space="preserve">★ {stars}</text>'
    )
    parts.append(
        f'  <g transform="translate(435,152) scale(0.85)" '
        f'fill="none" stroke="#9da7d3" stroke-width="2.2">'
    )
    parts.append('    <circle cx="-4.5" cy="-4.5" r="2.2"/>')
    parts.append('    <circle cx="4.5" cy="-4.5" r="2.2"/>')
    parts.append('    <circle cx="0" cy="4.5" r="2.2"/>')
    parts.append('    <path d="M -4.5,-2.3 L -4.5,1.5 M 4.5,-2.3 L 4.5,0.5 Q 4.5,2.5 2.5,2.5 L 0,2.5"/>')
    parts.append("  </g>")
    parts.append(
        f'  <text x="458" y="156" font-size="13" fill="#9da7d3" '
        f'text-anchor="end" xml:space="preserve">{forks}</text>'
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
