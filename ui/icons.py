"""Small inline SVG icons, drawn here so every icon lines up the same way (no emoji fonts)."""

from html import escape

PATHS = {
    "cup": '<path d="M5 9h10v4a4 4 0 0 1-4 4H9a4 4 0 0 1-4-4V9z"/><path d="M15 10h1.5a2 2 0 0 1 0 4H15"/><path d="M8 4v2M11 4v2"/>',
    "car": '<path d="M3.5 15v-3.2L5.4 7.5h13.2l1.9 4.3V15z"/><path d="M3.5 12h17"/><circle cx="7.5" cy="16.5" r="1.3"/><circle cx="16.5" cy="16.5" r="1.3"/>',
    "cap": '<path d="M3 9l9-4 9 4-9 4z"/><path d="M7 11.2v4c1.6 1.6 8.4 1.6 10 0v-4"/><path d="M21 9v5"/>',
    "shield": '<path d="M12 2.5l8 3.2v5.6c0 4.8-3.4 8.6-8 10.2-4.6-1.6-8-5.4-8-10.2V5.7z"/>',
    "bolt": '<path d="M13.5 2.5L5 13.5h6l-1 8 8.5-11h-6z"/>',
}
WORLD_ICON = {"cafe": "cup", "dealer": "car", "uni": "cap"}


def svg(name: str, label: str = "") -> str:
    """Return one icon as an SVG string. Its size and colour come from the stylesheet (the cda-* classes)."""
    title = f"<title>{escape(label)}</title>" if label else ""
    hidden = "" if label else 'aria-hidden="true" '
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" class="cda-ic cda-ic-{name}" '
            f'{hidden}role="img">{title}{PATHS[name]}</svg>')


def logo(world_id: str) -> str:
    """Return the rounded square with the business's icon in it."""
    return f'<span class="cda-logo">{svg(WORLD_ICON[world_id])}</span>'


def heading(world_id: str, name: str, line: str) -> str:
    """Return a logo with a bold name and a smaller line under it; the texts are escaped."""
    return (f'<div class="cda-head">{logo(world_id)}<span class="cda-headtext"><b>{escape(name)}</b>'
            f'<span class="cda-sub">{escape(line)}</span></span></div>')


def status_heading(world_id: str, name: str, status: str) -> str:
    """Return a logo with a bold name and a status line with a green dot; the texts are escaped."""
    return (f'<div class="cda-head">{logo(world_id)}<span class="cda-headtext"><b>{escape(name)}</b>'
            f'<span class="cda-sub"><i class="cda-dot"></i>{escape(status)}</span></span></div>')


def cost(amount: int) -> str:
    """Return a compute cost: the number and a bolt."""
    return f'<div class="cda-cost">{int(amount)}{svg("bolt")}</div>'


def brand(name: str) -> str:
    """Return the shield and the game's name for the top bar."""
    return f'<div class="cda-brand">{svg("shield")}<b>{escape(name)}</b></div>'
