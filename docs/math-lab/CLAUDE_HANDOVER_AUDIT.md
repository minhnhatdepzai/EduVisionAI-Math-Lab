# Handover audit — Codex → Claude

## 1. Codex đã làm gì

**Backend** (`master_be/app/services/math_lab/`) — `MathSemanticModel` →
`VisualDecisionEngine` → `PedagogyPlanner` → `MathScene`, có canonical hoá đơn
vị (`units.py`), registry kiểm tra grade/domain, và `POST /api/v1/math-lab/plan`
chỉ cho `TeacherUser`. 12 test + golden fixture.

**Frontend** (`frontend/src/features/math-lab/`) — validator schema phản chiếu
Pydantic, `mathWorldReducer` (load/play/pause/reset/next/previous/set_value,
có replay khi lùi bước), registry visualization, `api.mathLab.plan()`.

## 2. Phần dùng được — giữ nguyên

- Schema + validator hai phía. Chặt, thông báo lỗi có `path`.
- `units.py` canonical hoá — cần cho renderer (km→m, km/h→m/s).
- Decision engine + pedagogy: quyết định hợp lý theo lớp và domain.
- `mathWorldReducer` replay đúng khi lùi bước.
- `/math-lab/plan` chạy được, đã có test.

## 3. Phần chưa hoàn chỉnh

- **`renderer: null` cho cả 12 visualization.** Foundation không vẽ gì.
- **Không có trang nào để mở.** Không route, không sidebar, không page.
- **Không có preset** để thử khi chưa có AI.

## 4. Phần cần sửa

- **`scene.world.values` chỉ chứa dữ kiện cho sẵn** (`distance`, `speed`,
  `start_time`). Không có `distanceTravelled` / `elapsedTime` / `currentTime`,
  nên Motion Path, Clock và Timeline không có gì để đọc chung.
  → Thêm tầng **dẫn xuất** ở frontend: một `progress` duy nhất trong world
  state, mọi renderer tính giá trị của mình từ đó. Không renderer nào giữ
  đồng hồ riêng.
- `mathWorldReducer` chưa có khái niệm `progress` liên tục (chỉ có bước rời
  rạc) → **mở rộng** reducer của Codex, không viết reducer thứ hai.
- `scene.steps` chỉ `show`/`highlight`, chưa đổi giá trị — hiện đúng cho
  Phase 1, renderer không phụ thuộc vào nó.

## 5. File Claude sẽ sửa / thêm

Sửa:

```
frontend/src/features/math-lab/state/mathWorldState.js   thêm progress
frontend/src/features/math-lab/visualizations/registry.js  nối renderer thật
frontend/src/features/math-lab/index.js
frontend/src/app/roles.js            route + mục sidebar cho giáo viên
frontend/src/modes/normal/NormalMode.jsx
```

Thêm:

```
frontend/src/features/math-lab/fixtures/presets.js
frontend/src/features/math-lab/derive/*.js       toán học dẫn xuất
frontend/src/features/math-lab/renderers/*.jsx   6 renderer + entry point
frontend/src/features/math-lab/components/*.jsx  page, input, canvas, inspector
```

Sau audit, `foundation.py` và schema scene được sửa hẹp để giữ `Evidence` của
ràng buộc tới tận renderer; decision engine, pedagogy, units và backend
registry vẫn được giữ nguyên.

## Trạng thái sau tiếp quản

- Teacher có route `#/math-lab` trong sidebar và mười preset có nhãn fixture.
- Bảy renderer thật dùng chung một `progress`; Clock, Timeline và Motion không
  có timer toán học riêng.
- `8 − 3` lấy hướng phép toán từ `problem_type` của scene ở cả backend và local
  mode, tránh biến phép trừ thành phép cộng khi qua API.
- Text/Image input hiện đúng trạng thái provider chưa cấu hình; không giả OCR.
