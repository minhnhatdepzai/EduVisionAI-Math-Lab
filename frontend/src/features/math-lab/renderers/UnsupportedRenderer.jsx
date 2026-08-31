import styles from "./renderers.module.css";

/**
 * The abstention state, written for a teacher rather than for a developer.
 *
 * The old card printed the internal family slug and an English engine reason.
 * A teacher cannot act on either, so this asks for the one thing that actually
 * helps: the missing part of the question. Nothing here claims a result.
 */

const CLARIFICATIONS = {
  linear_identity: {
    title: "Hai vế của đề đang giống hệt nhau",
    body: "Sau khi rút gọn, hai vế bằng nhau với mọi giá trị của ẩn nên không có một đáp số riêng để vẽ.",
    hint: "Thầy cô kiểm tra lại đề, ví dụ đổi một hệ số hoặc một hằng số ở một vế.",
  },
  linear_contradiction: {
    title: "Đề này không có giá trị nào thỏa mãn",
    body: "Sau khi rút gọn, hai vế chênh nhau một hằng số nên không tồn tại giá trị của ẩn làm hai vế bằng nhau.",
    hint: "Thầy cô xem lại các số ở hai vế rồi nhập lại đề.",
  },
};

const DEFAULT_CLARIFICATION = {
  title: "Chưa đủ dữ kiện để dựng hình cho đề này",
  body: "Math Lab chỉ dựng hình khi đọc được đầy đủ các số liệu và điều cần tìm, để không hiển thị một hình sai nghĩa.",
  hint: "Thầy cô thử nhập lại đề đầy đủ hơn, hoặc chụp lại ảnh rõ nét và thẳng góc.",
};

export default function UnsupportedRenderer({ scene }) {
  const problemType = scene?.metadata?.problem_type || "";
  const clarification = CLARIFICATIONS[problemType] || DEFAULT_CLARIFICATION;
  return (
    <section className={`${styles.panel} ${styles.unsupportedPanel}`} role="status" aria-live="polite">
      <span className={styles.unsupportedIcon} aria-hidden="true">?</span>
      <div>
        <h3>{clarification.title}</h3>
        <p>{clarification.body}</p>
        <small>{clarification.hint}</small>
      </div>
    </section>
  );
}
