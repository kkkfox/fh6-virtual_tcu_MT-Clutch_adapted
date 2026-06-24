"""Per-tune vehicle keys for profile storage and learning."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from virtual_tcu.telemetry.model import Telemetry

# (car_ordinal, car_class, pi, tune_id)
CarKey = tuple[int, int, int, int]
CarKeyBase = tuple[int, int, int]

# Tune-slot drift detection. A saved profile is tied to a specific gearbox; if
# the car's learned gear ratios stop matching the saved ones, the gearbox was
# changed and the learning belongs in a new tune slot. We compare the RAW
# rpm/(km/h) of each well-sampled gear against the saved baseline (raw, so the
# calibrator's outlier rejection can't freeze a big change out of view), across
# ALL gears — not just 1st — so a swap that only alters the final drive or the
# upper gears (e.g. a race box vs an offroad/rally box on the same engine) is
# caught too.
RATIO_DRIFT_THRESHOLD = 0.22  # relative gear-ratio change that counts as drift
# A saved gear is only trusted as a baseline if it had at least this many samples.
RATIO_DRIFT_BASELINE_MIN_SAMPLES = 5
# A gear (>=2) is "flagged" as drifted once this many consecutive good live
# samples deviate past the threshold. On a matching gearbox the streak never
# exceeds ~2, so 3 is a safe flag.
RATIO_DRIFT_GEAR_FLAG_SAMPLES = 3
# Split into a new tune slot once at least this many distinct gears are flagged.
# A real gearbox swap (e.g. race box vs rally box) changes every gear, so >=2
# flag quickly regardless of which gears you happen to use; isolated single-gear
# noise (or a deliberate one-gear tweak) never reaches two.
RATIO_DRIFT_GEARS_NEEDED = 2


def car_key_base(td: Telemetry) -> CarKeyBase:
    return (td.car_ordinal, td.car_class, td.pi)


def compute_tune_signature(td: Telemetry) -> int:
    """Stable fingerprint from engine/drivetrain fields (not gearing)."""
    max_rpm = int(td.engine_max_rpm) if td.engine_max_rpm > 0 else 0
    idle = int(td.idle_rpm) if td.idle_rpm > 0 else 0
    return (max_rpm << 16) | (idle << 6) | ((td.drivetrain & 0x3) << 3) | (td.num_cylinders & 0x7)


def make_car_key(base: CarKeyBase, tune_id: int) -> CarKey:
    return (base[0], base[1], base[2], tune_id)


def storage_key(car_key: tuple[int, ...]) -> str:
    if len(car_key) == 3:
        return f"{car_key[0]}_{car_key[1]}_{car_key[2]}"
    if len(car_key) == 4:
        return f"{car_key[0]}_{car_key[1]}_{car_key[2]}_{car_key[3]}"
    raise ValueError(f"invalid car_key length: {len(car_key)}")
