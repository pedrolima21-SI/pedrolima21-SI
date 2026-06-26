````python
#!/usr/bin/env python3
"""
README dynamic section updater // PL-SEC

This script updates only the block between:

<!-- PLSEC:START_LATEST_OPS -->
<!-- PLSEC:END_LATEST_OPS -->

It reads public repositories from GitHub and renders a controlled
SIGINT-style "Latest Operations" section.
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


README_PATH = Path("README.md")
START_MARKER = "<!-- PLSEC:START_LATEST_OPS -->"
END_MARKER = "<!-- PLSEC:END_LATEST_OPS -->"

USERNAME = os.getenv("GH_USERNAME", "pedrolima-sec")
PROFILE_REPO = os.getenv("PROFILE_REPO", USERNAME)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")


def github_api_get(url: str) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "pl-sec-readme-updater",
    }

    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    request = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def format_date(value: str | None) -> str:
    if not value:
        return "unknown"

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.strftime("%Y-%m-%d")
    except ValueError:
        return "unknown"


def clean_text(value: str | None, fallback: str = "Repository activity detected") -> str:
    if not value:
        return fallback

    value = value.replace("\n", " ").replace("|", "/").strip()

    if len(value) > 86:
        return value[:83].rstrip() + "..."

    return value


def get_repositories() -> list[dict[str, Any]]:
    url = (
        f"https://api.github.com/users/{USERNAME}/repos"
        "?type=owner&sort=updated&direction=desc&per_page=100"
    )

    repos = github_api_get(url)

    if not isinstance(repos, list):
        return []

    filtered: list[dict[str, Any]] = []

    for repo in repos:
        name = repo.get("name", "")

        if not name:
            continue

        if name.lower() == PROFILE_REPO.lower():
            continue

        if repo.get("fork") is True:
            continue

        if repo.get("archived") is True:
            continue

        filtered.append(repo)

    filtered.sort(
        key=lambda item: item.get("pushed_at") or item.get("updated_at") or "",
        reverse=True,
    )

    return filtered[:5]


def render_latest_operations(repos: list[dict[str, Any]]) -> str:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if not repos:
        return textwrap.dedent(
            f"""
            ```txt
            ┌─ LATEST OPERATIONS ──────────────────────────────────────────────────────┐
            │                                                                          │
            │  Status       : No public repository signal found                         │
            │  Generated at : {generated_at:<56}│
            │                                                                          │
            │  Publish or update public repositories to populate this section.          │
            │                                                                          │
            └──────────────────────────────────────────────────────────────────────────┘
            ```
            """
        ).strip()

    lines = [
        "```txt",
        "┌─ LATEST OPERATIONS ──────────────────────────────────────────────────────┐",
        "│                                                                          │",
        f"│  Signal Source : github.com/{USERNAME:<49}│",
        f"│  Generated at  : {generated_at:<49}│",
        "│  Mode          : controlled dynamic layer                                 │",
        "│                                                                          │",
        "└──────────────────────────────────────────────────────────────────────────┘",
        "```",
        "",
        "<table>",
        "  <tr>",
        "    <th align=\"left\">Operation</th>",
        "    <th align=\"left\">Stack</th>",
        "    <th align=\"left\">Last Signal</th>",
        "    <th align=\"left\">Objective</th>",
        "  </tr>",
    ]

    for index, repo in enumerate(repos, start=1):
        name = clean_text(repo.get("name"), "Unnamed repository")
        url = repo.get("html_url", "#")
        language = clean_text(repo.get("language"), "Mixed")
        pushed_at = format_date(repo.get("pushed_at") or repo.get("updated_at"))
        description = clean_text(repo.get("description"))

        lines.extend(
            [
                "  <tr>",
                f"    <td><strong>DOSSIER-{index:02d}</strong><br/><a href=\"{url}\">{name}</a></td>",
                f"    <td>{language}</td>",
                f"    <td>{pushed_at}</td>",
                f"    <td>{description}</td>",
                "  </tr>",
            ]
        )

    lines.append("</table>")

    return "\n".join(lines)


def replace_section(readme: str, new_content: str) -> str:
    if START_MARKER not in readme or END_MARKER not in readme:
        raise RuntimeError(
            "Markers not found in README.md. "
            "Add PLSEC:START_LATEST_OPS and PLSEC:END_LATEST_OPS first."
        )

    before = readme.split(START_MARKER)[0]
    after = readme.split(END_MARKER)[1]

    return f"{before}{START_MARKER}\n{new_content}\n{END_MARKER}{after}"


def main() -> int:
    if not README_PATH.exists():
        print("README.md not found.", file=sys.stderr)
        return 1

    readme = README_PATH.read_text(encoding="utf-8")
    repos = get_repositories()
    section = render_latest_operations(repos)
    updated = replace_section(readme, section)

    if updated == readme:
        print("README.md already up to date.")
        return 0

    README_PATH.write_text(updated, encoding="utf-8")
    print("README.md updated successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
````

