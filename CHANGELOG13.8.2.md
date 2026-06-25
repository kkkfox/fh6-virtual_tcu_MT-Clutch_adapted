# VirtualTCU 13.8.2 修改日志

基于上游 `fh6-virtual_tcu_evolution` v13.7.x 修改。

---

## 新增功能

### 变速箱类型自动检测（手离模式）

在手动含离合模式下，TCU 首次升档时自动检测变速箱类型，区分 **序列换挡** 与 **离合换挡**。

- **核心思路**：以"效率"为判定标准 — 检测阶段发无离合升档，如果此时换挡速度不慢于按离合的换挡速度，归入序列换挡（不按离合）；否则归入离合换挡。
- **实测数据（60Hz UDP 帧，16.7ms/帧）**：

  | 变速箱 | 按离合换挡 | 不按离合换挡 |
  |--------|:----------:|:------------:|
  | 赛用变速箱 | 1 帧 (10ms) | 1 帧 (10ms) |
  | 运动型变速箱 | — | 4-5 帧 (~70ms) |
  | 普通变速箱 | 5-6 帧 (60-67ms) | 15 帧 (165ms) |

- **判定阈值**：无离合升档时 `gear=11` 的帧数
  - `neutral_frames ≤ 5` → **序列换挡**（不按离合换挡速度不慢于按离合）
  - `neutral_frames ≥ 6` → **离合换挡**（不按离合明显慢，需要离合）
  - 2 秒超时未进入空档 → 放弃本次，下次升档重试
- **关键结论**：运动型变速箱（如 3363 的一类车）不按离合仅 4-5 帧，按离合也是 5-6 帧，不按离合反而不慢，归入序列换挡。普通变速箱不按离合高达 15 帧，和按离合的 5-6 帧差距悬殊（166ms vs 64ms），不可能被误判。
- **帧数基准**：FH6 UDP 遥测固定 ~60Hz，与游戏渲染帧率无关，判定不受 FPS 影响。
- **UI 显示**：
  - 悬浮窗：绿色 `SEQ` / 黄色 `CLT` / 灰色 `—`
  - Web UI 侧栏：换挡方式：序列换挡 / 离合换挡 / 未识别
- **效果**：
  - **序列换挡**：后续升档/降档不按离合，换挡仅需 40ms。
  - **离合换挡**：正常按离合换挡，时序由 `clutch_pre_ms` / `clutch_overlap_ms` / `clutch_release_ms` 控制。
- **检测结果持久化**到 `tcu_profiles.json`（`racing_transmission` 字段），同一调校只检测一次。
- **调校切换**：更换调校时自动继承旧调校的检测结果（同一辆车不会因调校 ID 变化而重新检测）。
- **已知限制**：倒档不参与检测，挂倒档仍需按离合。

### 降档补油 (Rev-Match Blip)

手离模式下降档时自动短踩油门匹配发动机转速，减少顿挫。

- 新增配置项：
  - `feat_rev_blip`: 降档补油开关，**当 `feat_clutch_assist` 开启时默认强制启用**。
  - `blip_key`: 补油按键，默认 `w`。
  - `blip_ms`: 补油时长，默认 `70ms`（范围 20-150ms）。
- 补油时序（普通变速箱）：离合按下 → 等 `clutch_pre_ms` → 降档键与油门同时按下 → 等 `blip_ms` → 先松油门 → 松降档键 → 等 `clutch_release_ms` → 松离合。
- 补油时序（赛用变速箱）：降档键与油门同时按下 → 等 `blip_ms` → 松油门 → 松降档键（无离合参与）。
- 设置界面已加入降档补油开关及参数调整。
- **UI 调整**：降档补油开关和补油时长滑块已从"功能开关"卡片移至「离合辅助」展开区（离合键输入框下方），方便集中管理离合相关参数。
- 降档补油逻辑改为独立读取 `feat_rev_blip`，F10 热键一键同步离合辅助和降档补油，之后可在 UI 中分别手动覆盖。
- 换挡方式显示仅在离合辅助开启时可见，关闭时自动隐藏对应 UI 行。

### F10 离合辅助热键 + 悬浮窗状态显示

- 新增 `F10` 全局热键，快速开关离合辅助，终端输出 `[Clutch] ON/OFF`。
- 开关同步 `feat_clutch_assist` 和 `vjoy_use_clutch`，避免状态不一致。
- 悬浮窗（Electron HUD）顶部新增红色/灰色 `CLUTCH ON/OFF` 小标签。
- 设置界面热键列表新增 `F10 切换离合`。

---

## 配置默认值调整

| 配置项 | 原值 | 新值 | 说明 |
|--------|------|------|------|
| `feat_clutch_assist` | `false` | `true` | 默认启用手离模式 |
| `feat_relearn_blip` | `false` | `true` | 默认启用 F7 断油学习 |
| `clutch_key` | `shift` | `shift` | 保持不变；`/` 等符号键在 FH6 中无法通过 `keybd_event` 注入 |
| `clutch_pre_ms` | `20` | `5` | 缩短离合预压时间 |
| `udp_port` | `5555` | `5300` | 遥测端口 |

---

## Bug 修复

- 修复 `aiohttp` 高版本下 `content_type="text/html; charset=utf-8"` 导致 `ValueError`，改为分离 `content_type` 和 `charset` 参数。
- 修复 `_split_tune_profile` 创建新调校槽位时变速箱检测结果丢失的问题，现在新槽位继承旧槽位的 `racing_transmission` 值。
- 修复离合键 `/` 在 FH6 中不生效的问题：`keyboard` 库的 `keybd_event` API 对符号键注入不可靠，改回 `shift`。
- 修复 `_detect_transmission_frame` inconclusive 死循环：运动型变速箱不按离合 4-5 帧卡在判定区间导致反复重试，改为单阈值 `≤5` 判定。
- 修复中文输入法拦截换挡键导致自动升档永久卡死的问题：IME 吞掉注入的 E/Q 键后，TCU 的升档超时逻辑将"游戏无响应"误解为"到达最高档位"，`upshift_cap` 降为 1 档并 sticky 锁定。修复：新增 `UPSHIFT_CAP_MIN_FLOOR=2`（cap 永不降到 2 档以下）和 `UPSHIFT_CAP_CONFIRM_FROM_GEAR=3`（3 档以下不计入 sticky 确认计数），防止 IME/失焦等瞬时干扰导致永久死锁。
- 修复 F7 重学不清除变速箱类型检测结果的问题：`reset_crossover_learning` 补充了 `_racing_transmission.pop()`。
- 修复同车切换调校后变速箱类型不重新检测的问题：`_sync_profile_tune_id` 检测到 `tune_signature` 变化时自动清除旧的检测结果。
- 修复冲线后结算画面疯狂降档的问题：FH6 在比赛结束后 UDP 冻结最后一帧数据（`is_race_on=1`, `speed≈0`, `gear` 保持冲线挡位），TCU 误判为静止高档位触发 `STANDSTILL` 降档死循环。修复：新增遥测冻结检测，连续 3 秒数据无变化即停止换挡，回到自由漫游后自动恢复。
- 修复特定车辆永久无法识别变速箱类型的问题：F7 重学时磁盘 profile 中的 `racing_transmission` 未被清除，`_load_profiles` 恢复后 `_shift_to` 跳过检测。修复：F7 清除列表补上 `racing_transmission`；`_sync_profile_tune_id` 新增 `_prev_base` 守卫，跨车切换不误清除。

---

## 修改文件清单

| 文件 | 改动 |
|------|------|
| `virtual_tcu/config/constants.py` | `feat_clutch_assist=true`, `clutch_pre_ms=5`, 新增 `feat_rev_blip`/`blip_key`/`blip_ms`/`hotkey_toggle_clutch`, `udp_port=5300`, `feat_relearn_blip=true`, `UPSHIFT_CAP_MIN_FLOOR`, `UPSHIFT_CAP_CONFIRM_FROM_GEAR` |
| `virtual_tcu/input/keyboard_output.py` | 新增 `shift_no_clutch()`, `_press_release_with_blip()`, `use_blip` 自动关联 `feat_clutch_assist` |
| `virtual_tcu/logic/tcu.py` | 换挡方式检测（单阈值 `≤5`）, `_shift_to()` 分流, profile 持久化, `_split_tune_profile` 继承检测结果, snapshot 推送 `clutch_assist_enabled` / `transmission_type`, `_resolve_pending_upshift` IME 干扰修复, F7 清除变速箱类型, 调校切换自动清除, 遥测冻结检测, profile 持久化 racing_transmission 修复, `_prev_base` 跨车守卫 |
| `virtual_tcu/app.py` | 新增 F10 热键, `clutch_assist_enabled()` / `toggle_clutch_assist()` |
| `virtual_tcu/web/server.py` | aiohttp charset 兼容修复 |
| `packages/shared/src/config/settings.ts` | `feat_rev_blip` 从 `FEATURE_TOGGLES` 移除（移至离合辅助区）, `HOTKEY_FIELDS` 新增 `hotkey_toggle_clutch` |
| `packages/shared/src/types/telemetry.ts` | 新增 `clutch_assist_enabled`, `transmission_type` |
| `packages/shared/src/locales/zh-CN.ts` | 新增 `revBlip`, `toggleClutch`, `transmission`/`transType*`, `blipMs` 翻译 |
| `packages/shared/src/locales/en.ts` | 同上英文翻译 |
| `apps/dashboard/src/components/SettingsPanel.vue` | 离合辅助区新增降档补油开关 + 补油时长滑块 |
| `apps/electron/src/hud-renderer/HudApp.ts` | 新增 `clutchAssistEnabled`, `transmissionType` ref/WS 读取 |
| `apps/electron/src/hud-renderer/HudChrome.vue` | 新增 SEQ/CLT/— 换挡方式标签 + CLUTCH ON/OFF 标签; 换挡方式在离合辅助关闭时隐藏 |
| `apps/electron/src/hud-renderer/templates/*.vue` | 传递 `clutchAssistEnabled`, `transmissionType` props |
| `packages/ui/src/layout/ModeSidebar.vue` | 侧栏新增换挡方式显示; 离合辅助关闭时隐藏 |
| `packages/ui/src/settings/SettingsAdvanced.vue` | 离合辅助区新增降档补油开关 + 补油时长滑块 |
| `tcu_config.json` | 新增 `feat_rev_blip: true` |
| `.npmrc` | 添加 npm 淘宝镜像源 |

---

## 使用说明

### 首次使用

1. Settings → Advanced → 确保 **Clutch Assist** 已开启（默认开启）
2. 游戏内 Difficulty → Transmission → **MANUAL (With Clutch)**
3. 游戏内离合键绑定为左 `Shift`
4. 第一次升档 TCU 自动检测换挡方式，终端输出 `[TransDetect] sequential/clutch` 检测结果
5. 检测结果写入 `tcu_profiles.json`，之后换同车同调校不重复检测
6. 按 `F10` 可随时开关离合辅助，浮动窗实时显示 `CLUTCH ON/OFF`

### 序列换挡

- 升档/降档：直接按 E/Q，不按离合
- 降档补油开启时：自动短踩 W 补油

### 离合换挡

- 升档/降档：离合与换挡键按配置时序注入
- 降档补油开启时：自动短踩 W 补油
- 离合时序参数可在 `tcu_config.json` 或 Web UI 中调整：
  - `clutch_pre_ms`：离合按下后等待多久再按换挡键
  - `clutch_overlap_ms`：离合与换挡键同时按住的时长
  - `clutch_release_ms`：换挡键松开后等多久再松离合

### 已知限制

- `/` 等符号键无法通过 `keyboard` 库注入到 FH6，离合键请用 `shift`、字母键或数字键
- 倒档（R）不参与变速箱类型检测，挂倒档仍需手动按离合
