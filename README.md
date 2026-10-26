# Assetto Corsa Pedal & Telemetry Overlay (v2 Enhanced)

An advanced real-time telemetry overlay for **Assetto Corsa**, featuring real-time input graphs, pedal meters, a multifunction steering wheel display, an RPM shift ring, traction control visualization, and rev limiter warnings.

Compatible with vanilla Assetto Corsa and enhanced with features for **Custom Shaders Patch (CSP)**. Packaged as `telemetry_overlay_v2` so it can be installed alongside the original overlay without naming conflicts.

---

##  What's New in v2

* **RPM Arc Ring & Shift Indicator**:
  * Sweeps a 270° proportional arc around the wheel gauge (from bottom-left 225° clockwise to bottom-right 315°).
  * Color-coded RPM zones:
    * **0% – 75%**: Green (Safe operating range)
    * **75% – 85%**: Green › Yellow transition (Approaching shift point)
    * **85% – 100%**: Yellow › Red transition (Shift zone)
  * Segment resolution configurable from **12 to 96 segments** in the settings.
* **Rev Limiter / Shift Warning**:
  * Gear display snaps to **bright red** when engine RPM reaches **? 92% of max RPM** to clearly signal gear shifts.
* **Traction Control (TC) System**:
  * **Dual Detection Engine**:
    * **Wheel Slip (Drivetrain-Aware)**: Automatically reads `drivetrain.ini` (`RWD`, `AWD`, `AWD2`) to detect driven wheel over-rotation.
    * **Pedal Delta**: Measures cuts between physical driver input and sim-applied throttle.
  * **Visual TC Feedback**:
    * Dedicated glowing orange **TC badge** inside the wheel hub with variable halo intensity based on intervention severity.
    * Real-time throttle trace & pedal bar color shift (tints yellow/orange while TC cuts engine output).
* **Coexistence Package**:
  * Renamed internally to `telemetry_overlay_v2` to run simultaneously with or independently of the base `telemetry_overlay` app.

---

##  Core Features

* **Real-time Live Traces**:
  * Throttle
  * Brake
  * Clutch
  * Handbrake
  * Steering angle
  * Lateral G & Longitudinal G (with configurable denoising filter)
  * Force Feedback (FFB)
* **Pedal Input Bars**:
  * Vertical pedal travel indicators with color customization.
* **Multifunction Wheel Display**:
  * Current steering angle visualization.
  * Current gear (`R`, `N`, `1`, `2`, ...).
  * Digital vehicle speed (switchable between km/h and mph).
* **In-Game Settings UI**:
  * Interactive configuration menu accessible by clicking the left edge of the overlay window.

---

##  Installation

### Option 1: Drag & Drop with Content Manager (Recommended)
1. Drag and drop `telemetry_overlay_v2.zip` directly onto the Content Manager window.
2. Click the green hamburger menu in the top-right corner and select **Install**.
3. In Content Manager, navigate to **Settings > Assetto Corsa > Apps** and check the box next to **`telemetry_overlay_v2`**.
4. Launch an on-track session, open the right-side apps sidebar, and click on **Telemetry Overlay v2** to display the HUD.

### Option 2: Manual Installation
1. Extract `telemetry_overlay_v2.zip` into your Assetto Corsa root directory (typically `C:\Program Files (x86)\Steam\steamapps\common\assettocorsa\`).
2. Verify that the files are placed in:
   * `apps/python/telemetry_overlay_v2/`
   * `content/gui/icons/telemetry_overlay_v2_ON.png` & `_OFF.png`
3. Enable the app in Assetto Corsa options or Content Manager.

---

##  Rebuilding the Zip Package

To rebuild the release archive after making code modifications:

1. Open PowerShell in this project folder.
2. Run the build script:
   ```powershell
   .\create_zip_v2.ps1
   ```
3. A newly updated `telemetry_overlay_v2.zip` will be generated in the root folder, ready for distribution and installation.

---

##  Configuration

Settings can be adjusted directly in-game by clicking the left side of the telemetry window, or by editing:
```
apps/python/telemetry_overlay_v2/config.ini
```

### Wheel & RPM Settings
| Setting | Default | Description |
|---|---|---|
| `show_rpm_ring` | `True` | Enables the 270° RPM arc ring around the wheel |
| `rpm_ring_segments` | `48` | Number of segments rendered along the arc (12–96) |
| `wheel_show_gear` | `True` | Displays current gear in the center (turns red at ?92% max RPM) |
| `wheel_show_speed` | `True` | Displays vehicle speed below the gear |
| `metric` | `True` | `True` for km/h, `False` for mph |
