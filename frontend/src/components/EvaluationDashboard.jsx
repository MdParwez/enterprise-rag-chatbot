import React from "react";
import { useDispatch, useSelector } from "react-redux";
import { runRagasEvaluation } from "../store/evaluationSlice.js";

const METRIC_LABELS = {
  faithfulness: "Faithfulness",
  answer_relevancy: "Answer Relevancy",
  context_precision: "Context Precision",
  context_recall: "Context Recall",
};

export default function EvaluationDashboard() {
  const dispatch = useDispatch();
  const { result, status, error } = useSelector((s) => s.evaluation);
  const loading = status === "running";

  return (
    <div className="evaluation-view">
      <header className="panel-header">
        <h1>Evaluation</h1>
        <p>Run RAGAS metrics against the eval/test_dataset.json question set.</p>
      </header>

      <button className="run-eval-btn" onClick={() => dispatch(runRagasEvaluation())} disabled={loading}>
        {loading ? "Running RAGAS…" : "Run Evaluation"}
      </button>

      {error && <p className="status-hint error">{error}</p>}

      {result && (
        <>
          <div className="metric-grid">
            {Object.entries(result.scores).map(([key, value]) => (
              <div key={key} className="metric-card">
                <span className="metric-label">{METRIC_LABELS[key] || key}</span>
                <span className="metric-value">{(value * 100).toFixed(1)}%</span>
                <div className="score-bar"><div className="score-bar-fill" style={{ width: `${value * 100}%` }} /></div>
              </div>
            ))}
          </div>
          <p className="eval-meta">{result.n_items} question(s) evaluated</p>
        </>
      )}
    </div>
  );
}
