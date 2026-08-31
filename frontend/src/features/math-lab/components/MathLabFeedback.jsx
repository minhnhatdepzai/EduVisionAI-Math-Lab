import { useEffect, useState } from "react";
import { Button, Icon } from "../../../components/ui/index.js";
import styles from "./mathLab.module.css";

const RATINGS = [
  { id: "correct", label: "Đúng và dễ hiểu" },
  { id: "partly_correct", label: "Đúng một phần" },
  { id: "incorrect", label: "Chưa đúng" },
];

const CATEGORIES = [
  ["visualization", "Hình mô phỏng"],
  ["ocr", "Đọc ảnh / ký hiệu"],
  ["classification", "Nhận dạng dạng bài"],
  ["calculation", "Phép tính / đáp án"],
  ["pedagogy", "Cách giải thích"],
  ["other", "Khác"],
];

export default function MathLabFeedback({ model, scene, historyId, onSubmit }) {
  const [open, setOpen] = useState(false);
  const [rating, setRating] = useState("");
  const [category, setCategory] = useState("visualization");
  const [comment, setComment] = useState("");
  const [correction, setCorrection] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [receipt, setReceipt] = useState(null);

  useEffect(() => {
    setOpen(false);
    setRating("");
    setCategory("visualization");
    setComment("");
    setCorrection("");
    setError(null);
    setReceipt(null);
  }, [model?.id, model?.source_text, scene?.id]);

  if (!model || !scene) return null;

  async function submit(event) {
    event.preventDefault();
    if (!rating) {
      setError("Hãy chọn mức đánh giá.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const result = await onSubmit({
        history_id: historyId || null,
        rating,
        category,
        comment: comment.trim() || null,
        expected_correction: correction.trim() || null,
        semantic_model: model,
        scene,
      });
      setReceipt(result);
      setOpen(false);
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className={styles.feedback} aria-label="Góp ý cải thiện Math Lab">
      <div className={styles.feedbackIntro}>
        <span className={styles.feedbackIcon}><Icon name="edit" size={18} /></span>
        <div>
          <strong>Mô phỏng này có giúp học sinh nhìn ra cách làm không?</strong>
          <small>Góp ý được lưu để duyệt; AI không tự học trực tiếp từ phản hồi chưa kiểm chứng.</small>
        </div>
        <Button variant="secondary" size="sm" icon="edit" onClick={() => setOpen((value) => !value)}>
          {open ? "Đóng" : "Góp ý cải thiện AI"}
        </Button>
      </div>

      {receipt ? <p className={styles.feedbackSuccess}><Icon name="check" size={16} /> {receipt.message}</p> : null}

      {open ? (
        <form className={styles.feedbackForm} onSubmit={submit}>
          <fieldset>
            <legend>Đánh giá kết quả</legend>
            <div className={styles.ratingChoices}>
              {RATINGS.map((item) => (
                <label key={item.id} className={rating === item.id ? styles.ratingActive : styles.ratingChoice}>
                  <input
                    type="radio"
                    name="math-lab-rating"
                    value={item.id}
                    checked={rating === item.id}
                    onChange={(event) => setRating(event.target.value)}
                  />
                  {item.label}
                </label>
              ))}
            </div>
          </fieldset>

          <label>
            Phần cần cải thiện
            <select value={category} onChange={(event) => setCategory(event.target.value)}>
              {CATEGORIES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </label>
          <label>
            Góp ý của giáo viên
            <textarea
              rows={3}
              maxLength={4000}
              value={comment}
              placeholder="Ví dụ: thanh phân số phải chia thành 8 phần bằng nhau…"
              onChange={(event) => setComment(event.target.value)}
            />
          </label>
          <label>
            Kết quả hoặc cách mô phỏng đúng (nếu có)
            <textarea
              rows={3}
              maxLength={4000}
              value={correction}
              placeholder="Mô tả điều AI cần làm đúng ở lần sau…"
              onChange={(event) => setCorrection(event.target.value)}
            />
          </label>
          {error ? <p className={styles.inputError} role="alert">{error}</p> : null}
          <div className={styles.feedbackActions}>
            <Button type="submit" variant="primary" icon="check" loading={busy}>Gửi góp ý</Button>
          </div>
        </form>
      ) : null}
    </section>
  );
}
