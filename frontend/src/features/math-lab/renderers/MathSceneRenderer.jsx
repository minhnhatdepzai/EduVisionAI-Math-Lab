import { Component } from "react";
import { visualizationRegistry } from "../visualizations/registry.js";
import FormulaPanel from "./FormulaPanel.jsx";
import styles from "./renderers.module.css";

/**
 * The one way a scene becomes pictures.
 *
 * The page never learns how a fraction or a triangle is drawn: it hands over a
 * scene and this walks `scene.visualizations`, looks each type up in the
 * registry and renders whatever is registered. Adding a visualization means
 * registering a renderer, not editing a switch here or in the page.
 *
 * Anything unregistered, and any renderer that throws, is contained — a lab
 * that goes blank tells a teacher nothing about which part broke.
 */

class RendererBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidUpdate(previousProps) {
    if (this.state.error && previousProps.resetKey !== this.props.resetKey) {
      this.setState({ error: null });
    }
  }

  render() {
    if (this.state.error) {
      return (
        <div className={styles.rendererError} role="alert">
          <strong>Không dựng được “{this.props.title}”</strong>
          <span>{this.state.error.message}</span>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function MathSceneRenderer({ scene, world, progress, hidden = [] }) {
  if (!scene) {
    return <p className={styles.unavailable}>Chưa có cảnh nào được dựng.</p>;
  }

  const visible = scene.visualizations.filter((item) => !hidden.includes(item.type));
  if (!visible.length) {
    return <p className={styles.unavailable}>Mọi hình biểu diễn đang được tắt.</p>;
  }

  // A motion scene explains itself with the formula that produced the answer.
  const motionVisualization = visible.find((item) => item.type === "motion_path");

  return (
    <div className={styles.sceneGrid}>
      {visible.map((visualization) => {
        const definition = visualizationRegistry.get(visualization.type);
        const Renderer = definition?.renderer;

        if (!Renderer) {
          return (
            <div key={visualization.id} className={styles.rendererMissing}>
              <strong>Chưa hỗ trợ hình biểu diễn: {visualization.type}</strong>
              <span>Cách biểu diễn này đã được đăng ký nhưng chưa dựng xong.</span>
            </div>
          );
        }

        return (
          <RendererBoundary
            key={visualization.id}
            title={visualization.type}
            resetKey={`${scene.id}:${visualization.id}`}
          >
            <Renderer
              scene={scene}
              world={world}
              progress={progress}
              visualization={visualization}
            />
          </RendererBoundary>
        );
      })}

      {motionVisualization ? (
        <RendererBoundary title="Công thức" resetKey={`${scene.id}:formula`}>
          <FormulaPanel world={world} progress={progress} visualization={motionVisualization} />
        </RendererBoundary>
      ) : null}
    </div>
  );
}
