import { Button, Icon } from "../../../components/ui/index.js";
import { PLAYBACK_SPEEDS } from "../state/usePlayback.js";
import styles from "./mathLab.module.css";

/**
 * Transport for the whole lab, not for one panel.
 *
 * The scrubber writes the same `progress` playback does, so dragging it is
 * simply playing by hand — every representation follows it exactly as it
 * follows the play button.
 */
export default function PlaybackControls({
  playing, progress, speed, onPlay, onPause, onReset, onScrub, onSpeed,
  onPrevious, onNext, hasSteps,
}) {
  return (
    <div className={styles.playback}>
      <div className={styles.playbackButtons}>
        {hasSteps ? (
          <Button size="sm" variant="ghost" icon="chevronLeft" onClick={onPrevious}>Bước trước</Button>
        ) : null}

        {playing ? (
          <Button size="sm" variant="primary" icon="pause" onClick={onPause}>Tạm dừng</Button>
        ) : (
          <Button size="sm" variant="primary" icon="play" onClick={onPlay}>Chạy</Button>
        )}

        <Button size="sm" variant="ghost" icon="refresh" onClick={onReset}>Về đầu</Button>

        {hasSteps ? (
          <Button size="sm" variant="ghost" icon="chevronRight" onClick={onNext}>Bước sau</Button>
        ) : null}
      </div>

      <label className={styles.scrubber}>
        <span className={styles.srOnly}>Tiến độ</span>
        <input
          type="range"
          min="0"
          max="1000"
          value={Math.round(progress * 1000)}
          onChange={(event) => onScrub(Number(event.target.value) / 1000)}
        />
        <b>{Math.round(progress * 100)}%</b>
      </label>

      <div className={styles.speeds} role="group" aria-label="Tốc độ trình diễn">
        <Icon name="bolt" size={14} />
        {PLAYBACK_SPEEDS.map((value) => (
          <button
            key={value}
            type="button"
            className={value === speed ? styles.speedActive : styles.speed}
            onClick={() => onSpeed(value)}
          >
            {value}×
          </button>
        ))}
      </div>
    </div>
  );
}
