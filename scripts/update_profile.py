
import os
import re
import json
import html
from pathlib import Path
from urllib.request import Request, urlopen

USERNAME = "ismail808"
README = Path("README.md")

START = "<!-- PROJECTS:START -->"
END = "<!-- PROJECTS:END -->"

API_URL = (
    f"https://api.github.com/users/{USERNAME}/repos"
    "?per_page=100&sort=pushed&direction=desc"
)

token = os.getenv("GITHUB_TOKEN", "")


def github_request(url):
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "GitHub-Profile-Updater",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url, headers=headers)

    with urlopen(request, timeout=30) as response:
        return json.load(response)


def get_repositories():
    repositories = []
    page = 1

    while True:
        separator = "&" if "?" in API_URL else "?"
        url = f"{API_URL}{separator}page={page}"

        batch = github_request(url)

        if not batch:
            break

        repositories.extend(batch)

        if len(batch) < 100:
            break

        page += 1

    return [
        repo for repo in repositories
        if not repo.get("private", False)
        and not repo.get("fork", False)
        and not repo.get("archived", False)
        and repo["name"].lower() != USERNAME.lower()
    ]


def safe_text(value):
    value = str(value or "")
    value = " ".join(value.split())
    value = html.escape(value, quote=False)
    return value.replace("|", "&#124;")


def build_projects(repositories):
    if not repositories:
        return (
            "No public projects available yet. "
            "Check back soon!"
        )

    lines = [
        "| Project | Description | Language | Stars |",
        "|:--------|:------------|:---------|------:|",
    ]

    for repo in repositories:
        name = safe_text(repo["name"])
        description = safe_text(
            repo.get("description") or
            "Software development project"
        )
        language = safe_text(
            repo.get("language") or "—"
        )

        stars = repo.get("stargazers_count", 0)
        url = repo["html_url"]

        row = (
            f"| [{name}]({url}) "
            f"| {description} "
            f"| {language} "
            f"| ⭐ {stars} |"
        )

        lines.append(row)

    lines.extend([
        "",
        f"**Total Public Projects:** {len(repositories)}",
        "",
        f"[Explore All Repositories]"
        f"(https://github.com/{USERNAME}?tab=repositories)",
    ])

    return "\n".join(lines)


def update_readme():
    if not README.exists():
        raise FileNotFoundError("README.md not found")

    content = README.read_text(encoding="utf-8")

    if content.count(START) != 1 or content.count(END) != 1:
        raise ValueError(
            "README must contain exactly one pair "
            "of PROJECTS markers"
        )

    repositories = get_repositories()

    repositories.sort(
        key=lambda repo: repo.get("pushed_at") or "",
        reverse=True,
    )

    projects = build_projects(repositories)

    pattern = (
        re.escape(START)
        + r".*?"
        + re.escape(END)
    )

    replacement = (
        START + "\n"
        + projects + "\n"
        + END
    )

    updated = re.sub(
        pattern,
        lambda _: replacement,
        content,
        count=1,
        flags=re.DOTALL,
    )

    if updated != content:
        README.write_text(
            updated,
            encoding="utf-8",
        )
        print("README updated successfully!")
    else:
        print("README already up to date.")

    print(f"Public repositories: {len(repositories)}")


if __name__ == "__main__":
    update_readme()
