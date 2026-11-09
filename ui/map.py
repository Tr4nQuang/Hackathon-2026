"""The system core map as SVG: four rings of sectors around the core. This is the only HTML the app builds,
and every label is escaped."""

import math
from html import escape

SIZE = 360
CENTRE = SIZE / 2
GAP_DEGREES = 1.2  # a thin gap between neighbouring sectors
# Radii of the three rings, from the edge to the centre (tier 0, 1, 2), and the radius of the core disc.
RING_RADII = ((124, 172), (84, 122), (44, 82))
CORE_RADIUS = 42
RING_START = (-36, 0, -90)  # where the first sector of each ring starts, in degrees from the top
# Fill of each ring, a blue ramp: the closer to the centre, the darker, the more it is worth.
TIER_FILL = (("--t0", "#dce9f7"), ("--t1", "#afcbee"), ("--t2", "#5f93d6"), ("--t3", "#1f4f92"))
SENSITIVE_LABEL_X = 31  # the four sensitive sectors are small: labels sit beside the vertical divide, above or below the core
SENSITIVE_LABEL_Y = {-1: -46, 1: 58}
STATES = ("idle", "target", "asking", "safe", "served", "refused", "breached")
MARKS = {"breached": "✕ ", "served": "✓ ", "safe": "✓ ", "refused": "⊘ "}
FOCUS_COLOR = {"target": ("--bad", "#b4302a", 4), "asking": ("--accent", "#1a5da8", 3.5), "safe": ("--good", "#1b7653", 3)}
LABEL_SIZE, POINTS_SIZE = 10, 8.5
SURFACE = ("--surface", "#ffffff")


def _var(token: tuple) -> str:
    """Return a CSS colour that follows the theme variable and falls back to a fixed colour."""
    return f"var({token[0]},{token[1]})"


def _point(radius: float, degrees: float) -> tuple[float, float]:
    """Return the x, y position of a point at an angle measured clockwise from the top."""
    angle = math.radians(degrees - 90)
    return CENTRE + radius * math.cos(angle), CENTRE + radius * math.sin(angle)


def _arc_path(r_in: float, r_out: float, start: float, end: float) -> str:
    """Return the path of one ring sector between two angles."""
    large = 1 if end - start > 180 else 0
    x0, y0 = _point(r_out, start)
    x1, y1 = _point(r_out, end)
    x2, y2 = _point(r_in, end)
    x3, y3 = _point(r_in, start)
    return (f"M{x0:.2f} {y0:.2f}A{r_out} {r_out} 0 {large} 1 {x1:.2f} {y1:.2f}"
            f"L{x2:.2f} {y2:.2f}A{r_in} {r_in} 0 {large} 0 {x3:.2f} {y3:.2f}Z")


def _fill_and_ink(tier: int, state: str) -> tuple[str, str]:
    """Return the fill and the text colour of a sector for its state."""
    if state == "breached":
        return _var(("--breach", "#1e252c")), _var(("--breach-ink", "#f2766d"))
    if state == "refused":
        return "url(#hatch)", _var(("--warn", "#8f5e0e"))
    if state == "served":
        return _var(("--good-soft", "#dff1e8")), _var(("--ink", "#12202b"))
    return _var(TIER_FILL[tier]), ("#ffffff" if tier >= 2 else _var(("--ink", "#12202b")))


def _outline(tag: str, attrs: str, state: str) -> str:
    """Return the outline of a sector in focus: red and flashing for the attacked one, blue for the asked one, green when safe."""
    if state not in FOCUS_COLOR:
        return ""
    color, width = _var(FOCUS_COLOR[state][:2]), FOCUS_COLOR[state][2]
    animate = "" if state == "safe" else '<animate attributeName="opacity" values="1;0.25;1" dur="1.4s" repeatCount="indefinite"/>'
    return f'<{tag} {attrs} fill="none" stroke="{color}" stroke-width="{width}" data-outline="{state}">{animate}</{tag}>'


def _texts(lines: list[tuple[str, float, bool]], x: float, y: float, ink: str, halo: str = "") -> str:
    """Return centred text lines: the label first, then the points in a smaller size. A halo keeps white text readable off its sector."""
    top = y - (len(lines) - 1) * 6
    spans = "".join(f'<tspan x="{x:.1f}" y="{top + i * 12:.1f}" font-size="{size}" '
                    f'font-weight="{"600" if bold else "500"}">{escape(text)}</tspan>'
                    for i, (text, size, bold) in enumerate(lines))
    outline = f";paint-order:stroke;stroke:{halo};stroke-width:3px;stroke-linejoin:round" if halo else ""
    return f'<text text-anchor="middle" font-family="system-ui,sans-serif" style="fill:{ink}{outline}">{spans}</text>'


def _sector_group(sector: dict, tag: str, attrs: str, label_xy: tuple[float, float], state: str, core: bool = False) -> tuple[str, str]:
    """Return a sector as two SVG parts: its shape group (shape, outline) and its label text.

    tag and attrs describe the shape element. The labels are drawn after all shapes so no neighbour covers them.
    """
    fill, ink = _fill_and_ink(sector["tier"], state)
    points = f"\u2212{sector['pts']}" if state == "breached" else str(sector["pts"])
    if core:
        head = "\u2715 CORE" if state == "breached" else "\u2713 CORE" if state == "safe" else "CORE"
        lines = [(head, 11, True), (" ".join(sector["name"].split()[-2:]), POINTS_SIZE, False), (points, POINTS_SIZE, False)]
    else:
        lines = [(f"{MARKS.get(state, '')}{sector['label']}", LABEL_SIZE, True), (points, POINTS_SIZE, False)]
    title = escape(f"{sector['name']}, {sector['pts']} points, {state}")
    drawn = f'<{tag} {attrs} style="fill:{fill};stroke:{_var(SURFACE)}" stroke-width="2"/>'
    shape = (f'<g data-sector="{escape(str(sector["id"]), quote=True)}" data-state="{state}"><title>{title}</title>'
             f"{drawn}{_outline(tag, attrs, state)}</g>")
    return shape, _texts(lines, label_xy[0], label_xy[1], ink, fill if sector["tier"] == 2 and state in ("idle", "target", "asking", "safe") else "")


HATCH = ('<defs><pattern id="hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
         '<rect width="7" height="7" style="fill:var(--warn-soft,#faefd9)"/>'
         '<line x1="0" y1="0" x2="0" y2="7" style="stroke:var(--warn,#8f5e0e)" stroke-width="3"/></pattern></defs>')


def build_map_svg(world: dict, state: dict | None = None) -> str:
    """Return the system core map of a world as an SVG string.

    state maps a sector id to one of idle, target, asking, safe, served, refused or breached (missing means idle).
    """
    state = state or {}
    for value in state.values():
        if value not in STATES:
            raise ValueError(f"Unknown sector state: {value}")
    shapes, labels = "", ""
    for tier in range(3):
        sectors = [s for s in world["sectors"] if s["tier"] == tier]
        span = 360 / len(sectors) if sectors else 0
        r_in, r_out = RING_RADII[tier]
        for slot, sector in enumerate(sectors):
            start = RING_START[tier] + slot * span + GAP_DEGREES
            end = RING_START[tier] + (slot + 1) * span - GAP_DEGREES
            middle = _point((r_in + r_out) / 2, (start + end) / 2)
            if tier == 2 and len(sectors) == 4:
                middle = (CENTRE + math.copysign(SENSITIVE_LABEL_X, middle[0] - CENTRE), CENTRE + SENSITIVE_LABEL_Y[1 if middle[1] > CENTRE else -1] + 2)
            attrs = f'd="{_arc_path(r_in, r_out, start, end)}"'
            shape, label = _sector_group(sector, "path", attrs, (middle[0], middle[1] - 2), state.get(sector["id"], "idle"))
            shapes, labels = shapes + shape, labels + label
    core = next((s for s in world["sectors"] if s["tier"] == 3), None)
    if core:
        attrs = f'cx="{CENTRE}" cy="{CENTRE}" r="{CORE_RADIUS}"'
        shape, label = _sector_group(core, "circle", attrs, (CENTRE, CENTRE - 6), state.get(core["id"], "idle"), core=True)
        shapes, labels = shapes + shape, labels + label
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {SIZE}" role="img" '
            f'aria-label="System core map of {escape(world["name"])}" '
            f'style="width:100%;max-width:{SIZE + 20}px;height:auto;display:block;margin:0 auto">{HATCH}{shapes}{labels}</svg>')


LEGEND_ROWS = (("--t0", "#dce9f7", "Public · 10 pts each"), ("--t1", "#afcbee", "Internal · 25"),
               ("--t2", "#5f93d6", "Sensitive · 50"), ("--t3", "#1f4f92", "Core · 150, lose if breached"),
               ("--breach", "#1e252c", "Breached: points lost"), (None, None, "Customer turned away"))
ROW_HEIGHT = 20


def legend_svg() -> str:
    """Return the legend of the map: the four rings, a breached sector and a turned away customer."""
    cells = ""
    for index, (token, fallback, text) in enumerate(LEGEND_ROWS):
        x, y = (index % 2) * (SIZE / 2), (index // 2) * ROW_HEIGHT + 4
        fill = f"var({token},{fallback})" if token else "url(#hatch)"
        cells += (f'<rect x="{x:.0f}" y="{y}" width="12" height="12" rx="3" style="fill:{fill}"/>'
                  f'<text x="{x + 18:.0f}" y="{y + 10}" font-family="system-ui,sans-serif" font-size="11" '
                  f'style="fill:var(--muted,#56687a)">{escape(text)}</text>')
    height = math.ceil(len(LEGEND_ROWS) / 2) * ROW_HEIGHT + 4
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {SIZE} {height}" role="img" aria-label="Map legend" '
            f'style="width:100%;max-width:{SIZE + 20}px;height:auto;display:block;margin:0 auto">{HATCH}{cells}</svg>')


TIMELINE_COLOR = {"good": ("--good", "#1b7653"), "bad": ("--bad", "#b4302a"), "warn": ("--warn", "#8f5e0e")}
TIMELINE_WIDTH = 600


def timeline_svg(log: list[dict], position: int) -> str:
    """Return a thin strip with a tick for every judge verdict (green, red or amber) and the current position."""
    last = max(1, len(log) - 1)
    ticks = "".join(f'<rect x="{k / last * TIMELINE_WIDTH - 1.5:.1f}" y="2" width="3" height="10" rx="1.5" '
                    f'style="fill:{_var(TIMELINE_COLOR[entry["cls"]])}"/>'
                    for k, entry in enumerate(log) if entry["type"] == "judge")
    here = f'<rect x="{position / last * TIMELINE_WIDTH - 1:.1f}" y="0" width="2" height="14" style="fill:var(--ink,#12202b)"/>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {TIMELINE_WIDTH} 14" role="img" '
            f'aria-label="Replay timeline: red ticks are leaks, amber turned away customers, green blocked attacks and answered questions" '
            f'style="width:100%;height:14px;display:block"><rect x="0" y="6" width="{TIMELINE_WIDTH}" height="2" '
            f'style="fill:var(--line,#d2dbe3)"/>{ticks}{here}</svg>')
