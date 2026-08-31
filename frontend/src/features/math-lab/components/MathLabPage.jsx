import { useCallback, useEffect, useReducer, useState } from "react";
import PageHeader from "../../../components/layout/PageHeader.jsx";
import { Badge, Icon } from "../../../components/ui/index.js";
import { api } from "../../../services/api.js";
import { MATH_LAB_PRESETS, presetById } from "../fixtures/presets.js";
import { planLocally } from "../fixtures/localPlan.js";
import { hasSourceIntegrityMismatch, normalizeSemanticModel } from "../schemas/mathLabSchema.js";
import { mathWorldReducer } from "../state/mathWorldState.js";
import { usePlayback } from "../state/usePlayback.js";
import MathSceneRenderer from "../renderers/MathSceneRenderer.jsx";
import MathLabInputPanel from "./MathLabInputPanel.jsx";
import MathLabFeedback from "./MathLabFeedback.jsx";
import MathLabInspector from "./MathLabInspector.jsx";
import PlaybackControls from "./PlaybackControls.jsx";
import styles from "./mathLab.module.css";

const DEFAULT_PRESET = "grade5_motion";
const CAPABILITIES_UNAVAILABLE = {
  text_analysis: false,
  image_analysis: false,
  provider_configured: false,
  provider_available: false,
  message: "AI Vision chưa được cấu hình.",
};

function hasExactVisualization(scene) {
  return Boolean(scene?.visualizations?.some((item) => item.type !== "unsupported"));
}

function plannedOrigin(scene, exactOrigin) {
  return hasExactVisualization(scene) ? exactOrigin : "unsupported";
}

export default function MathLabPage() {
  const [presetId, setPresetId] = useState(DEFAULT_PRESET);
  const [fixtureRevision, setFixtureRevision] = useState(0);
  const [state, dispatch] = useReducer(mathWorldReducer, null);
  const [origin, setOrigin] = useState("loading");
  const [error, setError] = useState(null);
  const [analysisError, setAnalysisError] = useState(null);
  const [hidden, setHidden] = useState([]);
  const [speed, setSpeed] = useState(1);
  const [capabilities, setCapabilities] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [selectedQuestion, setSelectedQuestion] = useState(0);
  const [analysisBusy, setAnalysisBusy] = useState(false);
  const [planningBusy, setPlanningBusy] = useState(false);
  const [activeModel, setActiveModel] = useState(null);
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState(null);
  const [currentHistoryId, setCurrentHistoryId] = useState(null);

  useEffect(() => {
    let cancelled = false;
    if (api.auth.isDemoSession()) {
      setCapabilities({
        ...CAPABILITIES_UNAVAILABLE,
        message: "Chế độ Demo không dùng AI Vision.",
      });
      return undefined;
    }
    setHistoryLoading(true);
    api.mathLab.history()
      .then((result) => {
        if (!cancelled) setHistory(result.items || []);
      })
      .catch((loadError) => {
        if (!cancelled) setHistoryError(loadError.message);
      })
      .finally(() => {
        if (!cancelled) setHistoryLoading(false);
      });
    api.mathLab.capabilities()
      .then((result) => {
        if (!cancelled) setCapabilities(result);
      })
      .catch((capabilityError) => {
        if (!cancelled) {
          setCapabilities({ ...CAPABILITIES_UNAVAILABLE, message: capabilityError.message });
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const preset = presetById(presetId);
    if (!preset) return undefined;

    let cancelled = false;
    setOrigin("loading");
    setError(null);
    setAnalysisError(null);
    setHidden([]);
    setActiveModel(preset.model);
    dispatch({ type: "clear" });

    if (api.auth.isDemoSession()) {
      try {
        dispatch({ type: "load", scene: planLocally(preset) });
        setOrigin("local");
        setError("Chế độ Demo dùng fixture cục bộ và không gọi API giáo viên.");
      } catch (localError) {
        setOrigin("failed");
        setError(localError.message);
      }
      return () => {
        cancelled = true;
      };
    }

    (async () => {
      try {
        const response = await api.mathLab.plan(preset.model, preset.expects);
        if (cancelled) return;
        dispatch({ type: "load", scene: response.scene });
        setActiveModel(response.semantic_model);
        setOrigin(plannedOrigin(response.scene, "backend"));
      } catch (backendError) {
        if (cancelled) return;
        try {
          dispatch({ type: "load", scene: planLocally(preset) });
          setOrigin("local");
          setError(`Máy chủ chưa phản hồi: ${backendError.message}`);
        } catch (localError) {
          if (!cancelled) {
            setOrigin("failed");
            setError(localError.message);
          }
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [presetId, fixtureRevision]);

  const setProgress = useCallback((progress) => {
    dispatch({ type: "set_progress", progress });
  }, []);

  usePlayback({
    playing: state?.playback === "playing",
    progress: state?.progress ?? 0,
    speed,
    onProgress: setProgress,
  });

  async function saveRecent(sourceType, semanticModel) {
    try {
      const result = await api.mathLab.saveHistory(sourceType, semanticModel);
      const items = result.items || [];
      setHistory(items);
      setCurrentHistoryId(items[0]?.id || null);
      setHistoryError(null);
    } catch (saveError) {
      setHistoryError(`Chưa lưu được lịch sử: ${saveError.message}`);
    }
  }

  async function analyzeInput(sourceType, loader) {
    setAnalysisBusy(true);
    setPlanningBusy(true);
    setAnalysisError(null);
    setAnalysis(null);
    setSelectedQuestion(0);
    setActiveModel(null);
    setCurrentHistoryId(null);
    setHidden([]);
    setOrigin("loading");
    setError(null);
    dispatch({ type: "clear" });
    try {
      const document = await loader();
      if (!document.questions?.length) throw new Error("Không tìm thấy câu hỏi trong đầu vào.");
      setAnalysis(document);
      setSelectedQuestion(0);
      const semanticModel = normalizeSemanticModel(document.questions[0].semantic_model);
      const response = await api.mathLab.plan(semanticModel);
      dispatch({ type: "load", scene: response.scene });
      dispatch({ type: "play" });
      setActiveModel(response.semantic_model);
      setHidden([]);
      setOrigin(plannedOrigin(response.scene, "ai"));
      await saveRecent(sourceType, response.semantic_model);
    } catch (inputError) {
      dispatch({ type: "clear" });
      setAnalysis(null);
      setActiveModel(null);
      setOrigin("failed");
      setError(inputError.message);
      setAnalysisError(inputError.message);
    } finally {
      setAnalysisBusy(false);
      setPlanningBusy(false);
    }
  }

  async function generateVisualization(semanticInput, sourceType = null) {
    setPlanningBusy(true);
    setAnalysisError(null);
    setActiveModel(null);
    setHidden([]);
    setOrigin("loading");
    setError(null);
    dispatch({ type: "clear" });
    try {
      const semanticModel = normalizeSemanticModel(semanticInput);
      const response = await api.mathLab.plan(semanticModel);
      dispatch({ type: "load", scene: response.scene });
      dispatch({ type: "play" });
      setActiveModel(response.semantic_model);
      setHidden([]);
      setOrigin(plannedOrigin(response.scene, "ai"));
      if (sourceType) await saveRecent(sourceType, response.semantic_model);
    } catch (planningError) {
      dispatch({ type: "clear" });
      setActiveModel(null);
      setOrigin("failed");
      setError(planningError.message);
      setAnalysisError(planningError.message);
    } finally {
      setPlanningBusy(false);
    }
  }

  function selectPreset(id) {
    setAnalysis(null);
    setSelectedQuestion(0);
    setActiveModel(null);
    setCurrentHistoryId(null);
    setPresetId(id);
    setFixtureRevision((value) => value + 1);
  }

  async function visualizeQuestion(index) {
    const question = analysis?.questions?.[index];
    if (!question) return;
    setSelectedQuestion(index);
    await generateVisualization(question.semantic_model, analysis.source_type);
  }

  async function selectHistory(entry) {
    setAnalysis(null);
    setSelectedQuestion(0);
    setCurrentHistoryId(entry.id);
    await generateVisualization(entry.semantic_model);
  }

  const preset = presetById(presetId);
  const displayGrade = activeModel?.grade || preset?.grade;
  const modelSource = activeModel?.source_text || preset?.model?.source_text || "";
  const originalSource = analysis?.source_type === "text"
    ? analysis.extracted_text
    : modelSource;
  const sourceIntegrityMismatch = hasSourceIntegrityMismatch(modelSource, state?.scene);
  const sourceLabel = analysis?.source_type === "text"
    ? "Đề người dùng nhập · nguyên văn"
    : analysis?.source_type === "image"
      ? "Văn bản đọc từ ảnh"
      : "Đề mẫu gốc";
  const sourceBadge = analysis?.source_type === "image" ? "Bản OCR" : "Không chỉnh sửa";
  const sourceNote = analysis?.source_type === "image"
    ? "Đây là văn bản OCR cần đối chiếu với ảnh; công thức bên dưới không thay thế ảnh gốc."
    : "Công thức và hình bên dưới chỉ diễn giải đề này; chúng không thay thế đề gốc.";

  return (
    <div className={styles.page}>
      <PageHeader
        title="Math Vision Lab"
        subtitle="Biến một bài toán thành mô hình học sinh nhìn thấy được"
        actions={
          <div className={styles.headerBadges}>
            {displayGrade ? <Badge tone="neutral">Lớp {displayGrade}</Badge> : null}
            <OriginBadge origin={origin} />
          </div>
        }
      />

      {origin === "local" ? (
        <p className={styles.originNotice}>
          <Icon name="bolt" size={14} />
          Fixture này được dựng ngay trong trình duyệt. {error || "Renderer vẫn là renderer thật."}
        </p>
      ) : null}

      <div className={styles.layout}>
        <MathLabInputPanel
          activePreset={presetId}
          onSelectPreset={selectPreset}
          capabilities={capabilities}
          busy={analysisBusy}
          error={analysisError}
          onAnalyzeText={(text, gradeHint) => analyzeInput("text", () => api.mathLab.analyzeText(text, gradeHint))}
          onAnalyzeImage={(file, gradeHint) => analyzeInput("image", () => api.mathLab.analyzeImage(file, gradeHint))}
          history={history}
          historyLoading={historyLoading}
          historyError={historyError}
          onSelectHistory={selectHistory}
        />

        <main className={styles.canvas}>
          {state?.scene ? (
            <>
              {analysis?.questions?.length ? (
                <div className={styles.analysisToolbar}>
                  <div className={styles.questionNavigator} aria-label="Chọn câu đã nhận diện">
                    {analysis.questions.map((question, index) => (
                      <button
                        key={question.id}
                        type="button"
                        className={index === selectedQuestion ? styles.questionChipActive : styles.questionChip}
                        disabled={planningBusy}
                        onClick={() => visualizeQuestion(index)}
                      >
                        Câu {question.question_number}
                      </button>
                    ))}
                  </div>
                </div>
              ) : null}
              <section className={styles.sourceCard} aria-label={sourceLabel}>
                <div className={styles.sourceHeading}>
                  <strong>{sourceLabel}</strong>
                  <Badge tone={analysis?.source_type === "image" ? "warning" : "success"}>{sourceBadge}</Badge>
                </div>
                <pre className={styles.problemText}>{originalSource}</pre>
                <small>{sourceNote}</small>
              </section>
              {sourceIntegrityMismatch ? (
                <div className={styles.integrityError} role="alert">
                  <strong>Đã chặn mô phỏng vì đề gốc không khớp</strong>
                  <span>Hệ thống không được tự sửa đề. Hãy phân tích lại thay vì dựng một công thức khác.</span>
                </div>
              ) : (
                <MathSceneRenderer
                  scene={state.scene}
                  world={state.world}
                  progress={state.progress}
                  hidden={hidden}
                />
              )}
            </>
          ) : origin === "failed" ? (
            <div className={styles.canvasError} role="alert">
              <strong>Không dựng được cảnh</strong>
              <span>{error}</span>
            </div>
          ) : (
            <p className={styles.canvasLoading}>Đang dựng cảnh…</p>
          )}
        </main>

        <MathLabInspector
          scene={state?.scene}
          world={state?.world}
          progress={state?.progress ?? 0}
          hidden={hidden}
          onToggle={(type) => setHidden((current) => (
            current.includes(type)
              ? current.filter((item) => item !== type)
              : [...current, type]
          ))}
        />
      </div>

      <PlaybackControls
        playing={state?.playback === "playing"}
        progress={state?.progress ?? 0}
        speed={speed}
        hasSteps={Boolean(state?.scene?.steps?.length)}
        onPlay={() => dispatch({ type: "play" })}
        onPause={() => dispatch({ type: "pause" })}
        onReset={() => dispatch({ type: "reset" })}
        onScrub={(progress) => dispatch({ type: "scrub", progress })}
        onSpeed={setSpeed}
        onPrevious={() => dispatch({ type: "previous" })}
        onNext={() => dispatch({ type: "next" })}
      />

      {api.auth.isDemoSession() ? null : (
        <MathLabFeedback
          model={activeModel}
          scene={state?.scene}
          historyId={currentHistoryId}
          onSubmit={api.mathLab.submitFeedback}
        />
      )}

      <PipelineStatus
        capabilities={capabilities}
        analysis={analysis}
        semanticModel={activeModel}
        state={state}
      />
    </div>
  );
}

function OriginBadge({ origin }) {
  if (origin === "ai") return <Badge tone="success" dot>Đã trực quan hóa</Badge>;
  if (origin === "backend") return <Badge tone="success" dot>Cảnh từ máy chủ</Badge>;
  if (origin === "unsupported") return <Badge tone="warning" dot>Chưa hỗ trợ dạng bài</Badge>;
  if (origin === "local") return <Badge tone="warning" dot>Local fixture</Badge>;
  if (origin === "failed") return <Badge tone="danger" dot>Lỗi</Badge>;
  return <Badge tone="neutral" dot>Đang dựng…</Badge>;
}

function PipelineStatus({ capabilities, analysis, semanticModel, state }) {
  const exactVisualization = hasExactVisualization(state?.scene);
  const checks = [
    { label: "AI Vision", value: capabilities?.provider_available ? "✓" : "×", ok: capabilities?.provider_available },
    { label: "Đã nhận đầu vào", value: analysis ? "✓" : "—", ok: Boolean(analysis) },
    { label: "Số câu", value: analysis ? String(analysis.questions.length) : "—", ok: Boolean(analysis?.questions?.length) },
    { label: "Mô hình toán", value: analysis && semanticModel ? "✓" : "—", ok: Boolean(analysis && semanticModel) },
    { label: "Cảnh trực quan", value: exactVisualization ? "✓" : "—", ok: exactVisualization },
    { label: "Bộ dựng hình", value: exactVisualization ? "✓" : "—", ok: exactVisualization },
  ];
  return (
    <div className={styles.testStatus} aria-label="Trạng thái pipeline Math Vision">
      {checks.map((check) => (
        <span key={check.label} className={check.ok ? styles.checkOk : styles.checkOff}>
          <b>{check.label}</b> {check.value}
        </span>
      ))}
    </div>
  );
}
