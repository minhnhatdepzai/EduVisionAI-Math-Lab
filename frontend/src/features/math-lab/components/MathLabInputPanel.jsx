import { useEffect, useRef, useState } from "react";
import { Badge, Button, Icon } from "../../../components/ui/index.js";
import { MATH_LAB_PRESETS } from "../fixtures/presets.js";
import styles from "./mathLab.module.css";

/**
 * Where a problem comes into the lab.
 *
 * Four doors, and they are labelled honestly. Presets are fixtures, not model
 * output. The text and image doors are wired to the shape the vision pipeline
 * will fill, and until a provider exists they say so rather than pretending —
 * a lab that fakes its input teaches the teacher to distrust everything else
 * on the screen.
 */
const MODES = [
  { id: "presets", label: "Bài mẫu", icon: "notes" },
  { id: "text", label: "Nhập đề", icon: "edit" },
  { id: "image", label: "Tải ảnh", icon: "image" },
  { id: "history", label: "Gần đây", icon: "history" },
];

export default function MathLabInputPanel({
  activePreset,
  onSelectPreset,
  capabilities,
  busy = false,
  error = null,
  onAnalyzeText,
  onAnalyzeImage,
  history = [],
  historyLoading = false,
  historyError = null,
  onSelectHistory,
}) {
  const [mode, setMode] = useState("presets");
  const [text, setText] = useState("");
  const [image, setImage] = useState(null);
  const [gradeHint, setGradeHint] = useState("");
  const fileInput = useRef(null);

  useEffect(() => () => {
    if (image?.previewUrl) URL.revokeObjectURL(image.previewUrl);
  }, [image?.previewUrl]);

  const textReady = capabilities?.text_analysis === true;
  const imageReady = capabilities?.image_analysis === true;
  const providerMessage = capabilities?.message || "AI Vision chưa được cấu hình.";
  const parsedGrade = gradeHint ? Number(gradeHint) : null;

  return (
    <section className={styles.inputPanel} aria-label="Nguồn bài toán">
      <div className={styles.modeTabs} role="tablist">
        {MODES.map((item) => (
          <button
            key={item.id}
            type="button"
            role="tab"
            aria-selected={mode === item.id}
            className={mode === item.id ? styles.modeTabActive : styles.modeTab}
            onClick={() => setMode(item.id)}
          >
            <Icon name={item.icon} size={15} />
            {item.label}
          </button>
        ))}
      </div>

      {mode === "presets" ? (
        <ul className={styles.presetList}>
          {MATH_LAB_PRESETS.map((preset) => (
            <li key={preset.id}>
              <button
                type="button"
                className={preset.id === activePreset ? styles.presetActive : styles.preset}
                onClick={() => onSelectPreset(preset.id)}
              >
                <span className={styles.presetGrade}>Lớp {preset.grade}</span>
                <span className={styles.presetCopy}>
                  <strong>{preset.title}</strong>
                  <small>{preset.summary}</small>
                </span>
                {preset.experimental ? <Badge tone="warning">Thử nghiệm</Badge> : null}
              </button>
            </li>
          ))}
        </ul>
      ) : null}

      {mode === "text" ? (
        <div className={styles.inputForm}>
          <label className={styles.inputLabel} htmlFor="math-lab-text">Đề toán</label>
          <textarea
            id="math-lab-text"
            rows={6}
            value={text}
            placeholder="Nhập đề toán…"
            onChange={(event) => setText(event.target.value)}
          />
          <details className={styles.typingGuide}>
            <summary>Cách gõ công thức bằng bàn phím</summary>
            <div className={styles.typingExamples}>
              <span><code>x^3</code> hoặc <code>x mũ 3</code><small>lũy thừa</small></span>
              <span><code>căn bậc hai của (x+1)</code><small>căn bậc hai</small></span>
              <span><code>3 phần 5</code><small>phân số 3/5</small></span>
              <span><code>3 và 2 phần 5</code><small>hỗn số 3 2/5</small></span>
              <span><code>4*98 · 4x98 · 4×98 · 4 nhân 98</code><small>phép nhân</small></span>
              <span><code>92!</code> hoặc <code>giai thừa của 92</code><small>giai thừa</small></span>
              <span><code>nhân · chia · cộng · trừ · bằng</code><small>có thể gõ bằng chữ</small></span>
            </div>
            <p>Dùng từ <b>“và”</b> cho hỗn số. Ví dụ <code>3 2 phần 5</code> không rõ nghĩa nên hệ thống sẽ yêu cầu viết lại, không tự đoán.</p>
          </details>
          <GradeHint value={gradeHint} onChange={setGradeHint} />
          <Button
            variant="primary"
            icon="bolt"
            loading={busy}
            disabled={!textReady || !text.trim() || busy}
            onClick={() => onAnalyzeText(text, parsedGrade)}
          >
            Tự động mô phỏng
          </Button>
          {textReady ? null : (
            <p className={styles.notice}>
              <Icon name="lock" size={14} />
              {providerMessage}
            </p>
          )}
          {error ? <p className={styles.inputError} role="alert">{error}</p> : null}
        </div>
      ) : null}

      {mode === "image" ? (
        <div className={styles.inputForm}>
          <button
            type="button"
            className={styles.dropZone}
            onClick={() => fileInput.current?.click()}
          >
            {image ? (
              <img src={image.previewUrl} alt="Ảnh đề toán đã chọn" />
            ) : (
              <>
                <Icon name="image" size={26} />
                <strong>Tải ảnh đề</strong>
                <small>Ảnh chụp sách, bảng hoặc hình vẽ tay</small>
              </>
            )}
          </button>
          <input
            ref={fileInput}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className={styles.srOnly}
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) setImage({ file, previewUrl: URL.createObjectURL(file) });
            }}
          />
          <GradeHint value={gradeHint} onChange={setGradeHint} />
          <Button
            variant="primary"
            icon="bolt"
            loading={busy}
            disabled={!imageReady || !image?.file || busy}
            onClick={() => onAnalyzeImage(image.file, parsedGrade)}
          >
            Đọc ảnh và tự động mô phỏng
          </Button>
          {imageReady ? null : (
            <p className={styles.notice}>
              <Icon name="lock" size={14} />
              {providerMessage}
            </p>
          )}
          {error ? <p className={styles.inputError} role="alert">{error}</p> : null}
        </div>
      ) : null}

      {mode === "history" ? (
        <div className={styles.historyPanel}>
          <div className={styles.historyHeading}>
            <strong>5 bài gần nhất</strong>
            <small>Tạm lưu 30 ngày · bài mới thay bài cũ nhất</small>
          </div>
          {historyLoading ? <p className={styles.notice}>Đang tải lịch sử…</p> : null}
          {historyError ? <p className={styles.inputError} role="alert">{historyError}</p> : null}
          {!historyLoading && history.length === 0 ? (
            <p className={styles.notice}>Chưa có bài nào được trực quan hóa.</p>
          ) : null}
          {history.length ? (
            <ol className={styles.historyList}>
              {history.map((entry) => (
                <li key={entry.id}>
                  <button
                    type="button"
                    className={styles.historyItem}
                    disabled={busy}
                    onClick={() => onSelectHistory(entry)}
                  >
                    <span className={styles.historyMeta}>
                      <Badge tone="neutral">Lớp {entry.grade}</Badge>
                      <time dateTime={entry.created_at}>{formatHistoryTime(entry.created_at)}</time>
                    </span>
                    <strong>{entry.source_text || entry.problem_type}</strong>
                    <small>{entry.problem_type.replaceAll("_", " ")}</small>
                  </button>
                </li>
              ))}
            </ol>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

function formatHistoryTime(value) {
  try {
    return new Intl.DateTimeFormat("vi-VN", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(value));
  } catch {
    return "Gần đây";
  }
}

function GradeHint({ value, onChange }) {
  return (
    <label className={styles.inputLabel}>
      Lớp (không bắt buộc)
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">Để AI nhận diện</option>
        {Array.from({ length: 9 }, (_, index) => index + 1).map((grade) => (
          <option key={grade} value={grade}>Lớp {grade}</option>
        ))}
      </select>
    </label>
  );
}
