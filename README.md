# Ted's View Assist

A ground-up [View Assist](https://github.com/dinki/view_assist_integration) frontend, designed to look and work consistently across nightstand displays, handhelds, and wall-mounted tablets. Instead of customizing the stock views piecemeal, this provides a cohesive set of Home views, a single bottom navbar, a built-in background library, and Ted-styled assist overlays.

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

Ted's View Assist installs itself through a small companion integration (**Ted's View Assist**), which downloads the dashboard, views, sentence blueprints, and backgrounds from this repo and registers them with View Assist.

1. Install and **configure** the [View Assist integration](https://github.com/dinki/view_assist_integration) first, along with the other dependencies above (all via HACS).
2. In HACS, add this repo as a **custom repository** with category **Integration** (`https://github.com/tedr91/Teds-View-Assist`), download **Ted's View Assist**, and restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration → Ted's View Assist**. (It defaults to this repo on `main`; point it at a fork in the integration's options if you like.)
4. First setup downloads and installs everything automatically. After that, an **Update** entity (`update.teds_view_assist`) appears whenever a new release is published — installing it reinstalls only the assets that changed.

Prefer to do it by hand? Copy `dashboard/` and `views/` into `config/view_assist/`, `backgrounds/` into `config/view_assist/images/backgrounds/`, and import the blueprints under `custom_sentences/`.

### Services

- `teds_view_assist_installer.install_all` — install/update all changed assets (`force: true` reinstalls everything).
- `teds_view_assist_installer.install_asset` — install one `asset_class` (`dashboard` / `views` / `blueprints` / `backgrounds`), optionally a single `name`.
- `teds_view_assist_installer.check_updates` — re-check the repo for a new release.

## Home views

- **Clock** — the default home screen (matches View Assist's stock `/view-assist/clock`); at-a-glance time, date, weather, ideal for small landscape displays (Echo Show 5/8).
- **Home-Handheld** — vertical, phone-sized.
- **Home-WallPanel** — 10–15" landscape tablet, wall-mounted.
- **Home-WallPanel-Alt** — same tablets, vertical.

## Views

Alarm, Timers, Calendar, Weather, Thermostat, Music, Photos, Camera, List, Locate, Intent, Info, Alert, Sports, Webpage, Infopic.

## Menu

A single Ted's Navbar Card snapped to the bottom of every view. It augments its curated buttons with this device's View Assist status icons and takes its thickness from the device's status icon size. (Menu configuration and menu timeout are intentionally ignored for now.)

## Backgrounds

Built-in library under `backgrounds/{general,light,dark}`, seeded from Ted's Themes backgrounds. The installer stages these into `config/view_assist/images/backgrounds/` — View Assist's default rotating-background path — so point a device's background rotation at the matching subfolder.

## License

MIT — see [LICENSE](LICENSE).
