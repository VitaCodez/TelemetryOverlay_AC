import ac, acsys

import os
import sys
import platform

# Import Assetto Corsa shared memory library.
# It has a dependency on ctypes, which is not included in AC python version.
# Point to correct ctypes module based on platform architecture.
# First, get directory of the app, then add correct folder to sys.path.
app_dir = os.path.dirname(__file__)

if platform.architecture()[0] == "64bit":
    sysdir = os.path.join(app_dir, 'dll', 'stdlib64')
else:
    sysdir = os.path.join(app_dir, 'dll', 'stdlib')
# Python looks in sys.path for modules to load, insert new dir first in line.
sys.path.insert(0, sysdir)
os.environ['PATH'] = os.environ['PATH'] + ";."

from _telemetry_overlay.lib.sim_info import info


class TelemetryData:
    car_id = 0
    replay_time_multiplier = 0
    throttle = 0
    brake = 0
    clutch = 0
    handbrake = 0
    steering = 0
    steering_norm = 0.5
    ffb = 0
    gx_values = []
    gz_values = []
    max_x = 2.8
    max_z = 2.8
    gear_str = 'N'
    speed_kph = 0
    speed_mph = 0
    rpm = 0
    max_rpm = 8000
    tc_active = False
    tc_slip_amount = 0.0   # 0.0–1.0 – how much driven wheels are over-slipping (normalised)
    tc_cut_amount = 0.0    # 0.0–1.0 – how much the pedal delta indicates a TC cut

    # Drivetrain detection – populated once per car from drivetrain.ini.
    # 'RWD', 'FWD', 'AWD', 'AWD2', or None (unknown / packed .acd)
    drivetrain = None
    _last_car_model = None  # track car changes to re-detect when the car switches

    @staticmethod
    def _detect_drivetrain(car_model):
        """Read [TRACTION] TYPE from the car's drivetrain.ini.

        AC apps run with cwd = AC installation root, so the car data folder
        is at Content/cars/<carModel>/data/drivetrain.ini.  The file may also
        be packed into data.acd (encrypted/archived); if it cannot be read we
        return None so the caller falls back to the pedal-delta method only.
        """
        if not car_model:
            return None
        try:
            path = os.path.join(os.getcwd(), 'content', 'cars', car_model, 'data', 'drivetrain.ini')
            if not os.path.isfile(path):
                return None
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line.upper().startswith('TYPE='):
                        value = line.split('=', 1)[1].strip().upper()
                        if value in ('RWD', 'FWD', 'AWD', 'AWD2'):
                            return value
        except Exception:
            pass
        return None

    def __init__(self, IS_CSP, config):
        self.IS_CSP = IS_CSP
        self.config = config
        self.update_globals()
        self.update_telemetry()
    
    def update_globals(self):
        """Update the data required for telemetry"""
        self.car_id = ac.getFocusedCar()
        self.replay_time_multiplier = info.graphics.replayTimeMultiplier

        # Update max RPM from shared memory (static data, doesn't change per frame)
        try:
            max_rpm = info.static.maxRpm
            if max_rpm and max_rpm > 0:
                self.max_rpm = max_rpm
        except:
            pass

        # Detect drivetrain once per car (re-detect on car switch)
        try:
            car_model = str(info.static.carModel).replace('\x00', '').strip()
            if car_model and car_model != self._last_car_model:
                self._last_car_model = car_model
                self.drivetrain = self._detect_drivetrain(car_model)
        except Exception:
            pass
    
    def update_telemetry(self):
        """Update telemetry data"""
        self.throttle = ac.getCarState(self.car_id, acsys.CS.Gas)
        self.brake = ac.getCarState(self.car_id, acsys.CS.Brake)
        self.clutch = 1 - ac.getCarState(self.car_id, acsys.CS.Clutch)
        self.ffb = ac.getCarState(self.car_id, acsys.CS.LastFF)
        self.steering = ac.getCarState(self.car_id, acsys.CS.Steer)
        self.steering_norm = min(
            max(
                0.5 + (self.steering / self.config.steering_sensitivity) * -1,
                0.0
            ),
            1.0
        )

        if self.IS_CSP:
            self.handbrake = ac.ext_getHandbrake(self.car_id)
        
        g = ac.getCarState(self.car_id, acsys.CS.AccG)
        while len(self.gx_values) >= self.config.denoise_g: self.gx_values.pop(0)
        while len(self.gz_values) >= self.config.denoise_g: self.gz_values.pop(0)
        self.gx_values.append(min(max(g[0] * -1, self.max_x * -1.1), self.max_x * 1.1))
        self.gz_values.append(min(max(g[2] * -1, self.max_z * -1.1), self.max_z * 1.1))

        gear = ac.getCarState(self.car_id, acsys.CS.Gear)
        if gear == 0:
            self.gear_str = 'R'
        elif gear == 1:
            self.gear_str = 'N'
        else:
            self.gear_str = str(gear - 1)

        self.speed_kph = ac.getCarState(self.car_id, acsys.CS.SpeedKMH)
        self.speed_mph = ac.getCarState(self.car_id, acsys.CS.SpeedMPH)

        # RPM
        self.rpm = ac.getCarState(self.car_id, acsys.CS.RPM)

        # ── Traction Control detection ──────────────────────────────────────
        # Method A – Wheel slip: checks the *driven* wheels for over-rotation.
        #   wheelSlip indices: [FL=0, FR=1, RL=2, RR=3]. Values ≈ 1.0 at no-slip.
        #   Which wheels to check depends on drivetrain:
        #     RWD       → rear only  [2, 3]
        #     AWD/AWD2  → worst of all four
        #     FWD       → skipped (front-driven slip is tricky and TC is rare;
        #                  pedal-delta method B is sufficient for FWD)
        #     Unknown   → skipped (can't be sure, avoid nonsense)
        # Method B – Pedal delta: reliable on all drivetrains.
        # tc_active fires when EITHER applicable method detects intervention.
        try:
            is_moving = self.speed_kph > 5.0
            is_on_gas = self.throttle  > 0.05

            # ── Method A: wheel slip (drivetrain-aware) ─────────────────────
            tc_active_slip = False
            self.tc_slip_amount = 0.0

            if self.drivetrain in ('RWD', 'AWD', 'AWD2'):
                wheel_slip = list(info.physics.wheelSlip)  # [FL, FR, RL, RR]

                if self.drivetrain == 'RWD':
                    driven_slip = max(wheel_slip[2], wheel_slip[3])   # rear wheels only
                else:  # AWD / AWD2
                    driven_slip = max(wheel_slip)                      # worst of all four

                # Threshold: 1.5 = 50% over no-slip baseline.
                # Normalised intensity: 0.0 at threshold → 1.0 at 2× threshold.
                SLIP_THRESHOLD = 1.5
                tc_active_slip = is_moving and is_on_gas and driven_slip > SLIP_THRESHOLD
                if tc_active_slip:
                    self.tc_slip_amount = max(0.0, min(1.0,
                        (driven_slip - SLIP_THRESHOLD) / SLIP_THRESHOLD))

            # ── Method B: pedal delta (all drivetrains) ─────────────────────
            raw_gas = info.physics.gas          # raw driver pedal input
            tc_cut  = raw_gas - self.throttle   # >0 → AC cut effective throttle
            tc_active_pedal = is_moving and is_on_gas and tc_cut > 0.03
            self.tc_cut_amount = max(0.0, min(1.0, tc_cut)) if tc_active_pedal else 0.0

            # TC active if either applicable method fires
            self.tc_active = tc_active_slip or tc_active_pedal

        except Exception:
            self.tc_active      = False
            self.tc_slip_amount = 0.0
            self.tc_cut_amount  = 0.0
        
    def get_gx(self):
        if not len(self.gx_values):
            return 0.5
        
        avg_x = sum(self.gx_values) / len(self.gx_values)
        if abs(avg_x) > self.max_x: self.max_x = abs(avg_x)

        return 0.5 + avg_x / (self.max_x * 2)
    
    def get_gz(self):
        if not len(self.gz_values):
            return 0.5
        
        avg_z = sum(self.gz_values) / len(self.gz_values)
        if abs(avg_z) > self.max_z: self.max_z = abs(avg_z)

        return 0.5 + avg_z / (self.max_z * 2)
