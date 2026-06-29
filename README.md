# Ted's View Assist

A ground-up [View Assist](https://github.com/dinki/view_assist_integration) frontend, designed to look and work consistently across nightstand displays, handhelds, and wall-mounted tablets. Instead of customizing the stock views piecemeal, this provides a cohesive set of Home views, a single bottom navbar, a built-in wallpaper library, and Ted-styled assist overlays.

## Hard dependencies

These must be installed (HACS) for the views to render:

1. **View Assist Integration** — https://github.com/dinki/view_assist_integration
2. **UIX** — https://uix.lf.technology
3. **Daylight Calendar Card** — https://github.com/superdingo101/daylight-calendar-card
4. **Ted's Cards** — https://github.com/tedr91/Teds-Cards
5. **Ted's Cards Backend** — https://github.com/tedr91/Teds-Cards-Backend
6. **Custom Icons** — https://github.com/thomasloven/hass-custom_icons (provides the Fluent icon set the navbar uses)

### Required icon sets

The navbar is icon'd with **Fluent UI System Icons** (Iconify, prefix `fluent`). After installing **Custom Icons**, open its **Configure** panel, click **Download** to fetch Iconify, enable the **Fluent UI System Icons** set, and refresh your browser (F5). Everything else uses built-in `mdi:` icons.

> ⚠️ Custom Icons disables Home Assistant's built-in SVG sanitization (so icons can be full-color/animated) — only enable icon sets you trust. The curated Iconify Fluent set is safe.

## Installation

1. Install the dependencies above via HACS.
2. Add this repo as an HACS custom repository, or copy `dashboard/` + `views/` into your View Assist config directory.
3. Copy `wallpapers/` to `config/www/teds_view_assist/wallpapers/` (or your preferred path) and point Home views at them.
4. Import the blueprints under `custom_sentences/` and `scripts/` as desired.

## Home views

- **Clock** — the default home screen (matches View Assist's stock `/view-assist/clock`); at-a-glance time, date, weather, ideal for small landscape displays (Echo Show 5/8).
- **Home-Handheld** — vertical, phone-sized.
- **Home-WallPanel** — 10–15" landscape tablet, wall-mounted.
- **Home-WallPanel-Alt** — same tablets, vertical.

## Views

Alarms, Timers, Calendar, Weather, Thermostat, Music, Photos, Cameras, List, Map, Intent, Info, Alerts, Sports.

## Menu

A single Ted's Navbar Card snapped to the bottom of every view. (Status icon size, menu configuration, and menu timeout options are intentionally ignored for now.)

## Wallpapers

Built-in library under `wallpapers/{general,light,dark}`, seeded from Ted's Themes backgrounds.

## License

MIT — see [LICENSE](LICENSE).
