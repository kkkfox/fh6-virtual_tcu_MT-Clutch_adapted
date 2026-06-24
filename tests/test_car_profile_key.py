"""Per-tune profile keys and ratio-drift slot splitting."""

from tests.conftest import CAR_KEY, CAR_KEY_BASE, make_telemetry
from virtual_tcu.config.store import ConfigStore  # noqa: E402
from virtual_tcu.input.interface import OutputInterface  # noqa: E402
from virtual_tcu.logic.tcu import TCULogic  # noqa: E402
from virtual_tcu.storage.profiles import ProfileStore  # noqa: E402
from virtual_tcu.telemetry.car_key import storage_key  # noqa: E402
from virtual_tcu.telemetry.logger import TelemetryLogger  # noqa: E402


class _Out(OutputInterface):
    @property
    def key_up(self) -> str:
        return "e"

    @property
    def key_down(self) -> str:
        return "q"

    def is_self_press(self, key: str) -> bool:
        return False

    def shift_to(self, from_gear: int, target_gear: int):
        pass

    def shutdown(self):
        pass


def test_profile_store_legacy_three_part_key(tmp_path):
    prof = ProfileStore(path=str(tmp_path / "prof.json"))
    prof.data["100_5_800"] = {"gear_ratios": {"1": 100.0}, "gear_counts": {"1": 10}}
    prof.save()

    got = prof.get(CAR_KEY)
    assert got is not None
    assert got["gear_ratios"]["1"] == 100.0


def test_profile_store_four_part_storage_key(tmp_path):
    prof = ProfileStore(path=str(tmp_path / "prof.json"))
    prof.set(CAR_KEY, {"gear_ratios": {"1": 90.0}})

    assert storage_key(CAR_KEY) in prof.data
    assert prof.get(CAR_KEY)["gear_ratios"]["1"] == 90.0


def test_ratio_drift_splits_tune_slot(tmp_path, monkeypatch):
    import virtual_tcu.logic.tcu as tcu_mod

    clock = {"now": 1000.0}
    monkeypatch.setattr(tcu_mod.time, "time", lambda: clock["now"])

    cfg = ConfigStore(path=str(tmp_path / "cfg.json"))
    prof = ProfileStore(path=str(tmp_path / "prof.json"))
    tcu = TCULogic(_Out(), prof, cfg, TelemetryLogger())
    tcu._current_car_key = CAR_KEY
    # Baseline tune. A new gearbox changes every gear, so 2nd and 3rd both drift.
    tcu._profile_baseline_ratios[CAR_KEY] = {1: 100.0, 2: 40.0, 3: 25.0}
    tcu._tune_id_by_base[CAR_KEY_BASE] = CAR_KEY[3]

    # New box ~30% shorter: 2nd reads ~52 (1872 rpm @ 36 km/h), 3rd ~33.
    g2 = make_telemetry(gear=2, speed_ms=10.0, current_rpm=1872.0, accel_raw=255, torque_nm=400.0)
    g3 = make_telemetry(gear=3, speed_ms=10.0, current_rpm=1188.0, accel_raw=255, torque_nm=400.0)
    g2.profile_tune_id = CAR_KEY[3]
    g3.profile_tune_id = CAR_KEY[3]

    # One gear drifting is not enough (single-gear tweaks are ignored).
    for _ in range(tcu_mod.RATIO_DRIFT_GEAR_FLAG_SAMPLES + 1):
        tcu._check_tune_ratio_drift(g2)
    assert tcu._tune_id_by_base[CAR_KEY_BASE] == CAR_KEY[3], "single drifted gear must not split"

    # A second drifted gear pushes it over the line → new slot.
    for _ in range(tcu_mod.RATIO_DRIFT_GEAR_FLAG_SAMPLES + 1):
        tcu._check_tune_ratio_drift(g3)

    new_id = tcu._tune_id_by_base[CAR_KEY_BASE]
    assert new_id != CAR_KEY[3]
    assert tcu._current_car_key[3] == new_id
    assert tcu._profile_baseline_ratios.get(tcu._current_car_key) is None


def test_ratio_drift_no_split_when_matching(tmp_path, monkeypatch):
    import virtual_tcu.logic.tcu as tcu_mod

    monkeypatch.setattr(tcu_mod.time, "time", lambda: 1000.0)
    cfg = ConfigStore(path=str(tmp_path / "cfg.json"))
    prof = ProfileStore(path=str(tmp_path / "prof.json"))
    tcu = TCULogic(_Out(), prof, cfg, TelemetryLogger())
    tcu._current_car_key = CAR_KEY
    tcu._profile_baseline_ratios[CAR_KEY] = {1: 100.0, 2: 40.0, 3: 25.0}
    tcu._tune_id_by_base[CAR_KEY_BASE] = CAR_KEY[3]

    # Raw ratios match the saved 2nd/3rd exactly → never splits, however long.
    g2 = make_telemetry(gear=2, speed_ms=10.0, current_rpm=1440.0, accel_raw=255, torque_nm=400.0)
    g3 = make_telemetry(gear=3, speed_ms=10.0, current_rpm=900.0, accel_raw=255, torque_nm=400.0)
    g2.profile_tune_id = CAR_KEY[3]
    g3.profile_tune_id = CAR_KEY[3]
    for _ in range(20):
        tcu._check_tune_ratio_drift(g2)
        tcu._check_tune_ratio_drift(g3)
    assert tcu._tune_id_by_base[CAR_KEY_BASE] == CAR_KEY[3]
