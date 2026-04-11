import { useState, useRef, useEffect } from "react";
import axios from "axios";

const API = axios.create({ baseURL: "http://localhost:8000" });

const css = `
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=JetBrains+Mono:wght@300;400;500&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0a0a0f; color: #e8e4d9; font-family: 'JetBrains Mono', monospace; min-height: 100vh; }
  .app { display: flex; flex-direction: column; min-height: 100vh; }

  /* ── COLLEGE HEADER ─────────────────────────────────────────── */
  .college-header {
    background: linear-gradient(135deg, #0d1b3e 0%, #1a2d5a 40%, #0d1b3e 100%);
    border-bottom: 3px solid #c9a84c;
    position: relative;
    overflow: hidden;
  }
  .college-header::before {
    content: '';
    position: absolute;
    inset: 0;
    background: repeating-linear-gradient(
      45deg, transparent, transparent 40px,
      rgba(201,168,76,0.03) 40px, rgba(201,168,76,0.03) 41px
    );
    pointer-events: none;
  }
  .college-header-inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 32px;
    gap: 16px;
    position: relative;
    z-index: 1;
  }
  .college-logo-box {
    width: 84px; height: 84px;
    flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(201,168,76,0.35);
    border-radius: 6px;
    overflow: hidden;
    padding: 4px;
  }
  .college-logo-box img { width: 100%; height: 100%; object-fit: contain; }
  .logo-fallback {
    font-family: 'Playfair Display', serif;
    font-size: 10px; color: #c9a84c; text-align: center;
    font-weight: 700; letter-spacing: 0.5px; line-height: 1.4; padding: 6px;
  }
  .college-center { flex: 1; text-align: center; }
  .college-name {
    font-family: 'Playfair Display', serif;
    font-size: 18px; font-weight: 900; color: #ffffff;
    letter-spacing: 1.5px; line-height: 1.2;
    text-shadow: 0 2px 10px rgba(0,0,0,0.6);
  }
  .college-sub {
    font-size: 10px; color: #a8b8d8;
    letter-spacing: 0.8px; margin-top: 3px; font-style: italic;
  }
  .college-dept {
    font-size: 11.5px; color: #c9a84c;
    letter-spacing: 1px; margin-top: 5px; font-weight: 600;
  }
  .college-divider {
    width: 80px; height: 1px;
    background: linear-gradient(to right, transparent, #c9a84c, transparent);
    margin: 7px auto;
  }
  .college-project {
    font-family: 'Playfair Display', serif;
    font-size: 13px; font-weight: 700; color: #c9a84c;
    letter-spacing: 1px; text-transform: uppercase;
    text-shadow: 0 0 24px rgba(201,168,76,0.45);
    line-height: 1.35;
  }

  /* ── NAV ─────────────────────────────────────────────────────── */
  .nav { display: flex; align-items: center; gap: 8px; padding: 14px 40px; border-bottom: 1px solid #1e1e2e; background: #12121a; position: sticky; top: 0; z-index: 100; }
  .nav-logo { font-family: 'Playfair Display', serif; font-size: 20px; font-weight: 900; color: #c9a84c; letter-spacing: 1px; margin-right: 32px; }
  .nav-logo span { color: #e8e4d9; font-weight: 400; }
  .nav-tab { background: none; border: 1px solid transparent; color: #6b6880; font-family: 'JetBrains Mono', monospace; font-size: 12px; padding: 8px 18px; cursor: pointer; letter-spacing: 1px; text-transform: uppercase; transition: all 0.2s; }
  .nav-tab:hover { color: #e8e4d9; border-color: #1e1e2e; }
  .nav-tab.active { color: #c9a84c; border-color: #c9a84c; background: #c9a84c22; }
  .nav-status { margin-left: auto; font-size: 11px; color: #4caf7d; display: flex; align-items: center; gap: 6px; }
  .dot { width: 7px; height: 7px; border-radius: 50%; background: #4caf7d; animation: pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

  /* ── MAIN ─────────────────────────────────────────────────────── */
  .main { flex: 1; padding: 40px; max-width: 1000px; margin: 0 auto; width: 100%; }
  .section-title { font-family: 'Playfair Display', serif; font-size: 28px; font-weight: 700; color: #e8e4d9; margin-bottom: 6px; }
  .section-sub { font-size: 12px; color: #6b6880; margin-bottom: 32px; letter-spacing: 1px; }
  .input-group { margin-bottom: 16px; }
  .label { font-size: 11px; color: #6b6880; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 6px; display: block; }
  .input, .textarea, .select { width: 100%; background: #12121a; border: 1px solid #1e1e2e; color: #e8e4d9; font-family: 'JetBrains Mono', monospace; font-size: 13px; padding: 12px 16px; outline: none; transition: border-color 0.2s; }
  .input:focus, .textarea:focus, .select:focus { border-color: #c9a84c; }
  .textarea { resize: vertical; min-height: 100px; }
  .select option { background: #12121a; }
  .btn { background: #c9a84c; color: #0a0a0f; border: none; font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 500; letter-spacing: 2px; text-transform: uppercase; padding: 14px 32px; cursor: pointer; transition: all 0.2s; }
  .btn:hover { opacity: 0.85; }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; }
  .card { border: 1px solid #1e1e2e; background: #12121a; padding: 20px; margin-bottom: 12px; }
  .card-title { font-family: 'Playfair Display', serif; font-size: 15px; margin-bottom: 6px; }
  .card-meta { font-size: 11px; color: #6b6880; margin-bottom: 10px; }
  .card-body { font-size: 12px; line-height: 1.7; color: #b0acbf; }
  .score-bar { margin-top: 10px; }
  .score-label { display: flex; justify-content: space-between; font-size: 11px; color: #6b6880; margin-bottom: 4px; }
  .score-track { height: 3px; background: #1e1e2e; }
  .score-fill { height: 3px; background: #c9a84c; transition: width 0.6s ease; }
  .prediction-box { border: 1px solid #c9a84c; background: #c9a84c22; padding: 24px; margin-bottom: 24px; }
  .prediction-label { font-size: 11px; color: #c9a84c; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px; }
  .prediction-value { font-family: 'Playfair Display', serif; font-size: 32px; font-weight: 700; }
  .prediction-conf { font-size: 12px; color: #6b6880; margin-top: 4px; }
  .ai-response { border-left: 2px solid #c9a84c; padding: 20px 24px; background: #12121a; font-size: 13px; line-height: 1.9; color: #e8e4d9; margin-top: 24px; }
  .ai-response h3 { font-family: 'Playfair Display', serif; font-size: 15px; color: #c9a84c; margin: 16px 0 8px 0; }
  .ai-response h4 { font-size: 13px; color: #e8e4d9; margin: 12px 0 6px 0; font-weight: 600; }
  .ai-response strong { color: #e8e4d9; font-weight: 600; }
  .ai-response ul { padding-left: 16px; margin: 6px 0; }
  .ai-response li { margin-bottom: 4px; }
  .ai-response hr { border: none; border-top: 1px solid #1e1e2e; margin: 16px 0; }
  .ai-response em { color: #6b6880; font-style: italic; }
  .ai-label { font-size: 11px; color: #c9a84c; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 12px; margin-top: 24px; }
  .chat-window { border: 1px solid #1e1e2e; background: #12121a; height: 460px; overflow-y: auto; padding: 20px; margin-bottom: 16px; display: flex; flex-direction: column; gap: 16px; }
  .msg { display: flex; gap: 12px; }
  .msg.user { flex-direction: row-reverse; }
  .msg-avatar { width: 32px; height: 32px; border: 1px solid #1e1e2e; display: flex; align-items: center; justify-content: center; font-size: 12px; color: #c9a84c; flex-shrink: 0; }
  .msg-bubble { max-width: 75%; font-size: 13px; line-height: 1.7; padding: 12px 16px; border: 1px solid #1e1e2e; background: #0a0a0f; }
  .msg-bubble strong { color: #e8e4d9; font-weight: 600; }
  .msg-bubble h3 { font-family: 'Playfair Display', serif; font-size: 14px; color: #c9a84c; margin: 10px 0 6px 0; }
  .msg-bubble h4 { font-size: 13px; color: #e8e4d9; margin: 8px 0 4px 0; }
  .msg-bubble ul { padding-left: 16px; margin: 4px 0; }
  .msg-bubble li { margin-bottom: 3px; }
  .msg-bubble hr { border: none; border-top: 1px solid #1e1e2e; margin: 10px 0; }
  .msg.user .msg-bubble { background: #c9a84c22; border-color: #c9a84c; }
  .chat-input-row { display: flex; gap: 8px; }
  .chat-input { flex: 1; background: #12121a; border: 1px solid #1e1e2e; color: #e8e4d9; font-family: 'JetBrains Mono', monospace; font-size: 13px; padding: 12px 16px; outline: none; }
  .chat-input:focus { border-color: #c9a84c; }
  .drop-zone { border: 2px dashed #1e1e2e; padding: 48px; text-align: center; cursor: pointer; transition: all 0.2s; margin-bottom: 20px; }
  .drop-zone:hover, .drop-zone.active { border-color: #c9a84c; background: #c9a84c22; }
  .drop-icon { font-size: 36px; margin-bottom: 12px; }
  .drop-text { font-size: 12px; color: #6b6880; }
  .quick-prompts { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }
  .quick-btn { background: none; border: 1px solid #1e1e2e; color: #6b6880; font-family: 'JetBrains Mono', monospace; font-size: 11px; padding: 6px 14px; cursor: pointer; transition: all 0.2s; }
  .quick-btn:hover { border-color: #c9a84c; color: #c9a84c; }
  .loading { display: flex; align-items: center; gap: 8px; font-size: 12px; color: #6b6880; padding: 20px 0; }
  .spinner { width: 16px; height: 16px; border: 2px solid #1e1e2e; border-top-color: #c9a84c; border-radius: 50%; animation: spin 0.7s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .badge { display: inline-block; font-size: 10px; padding: 2px 8px; border: 1px solid; letter-spacing: 1px; text-transform: uppercase; }
  .badge-green { border-color: #4caf7d; color: #4caf7d; }
  .badge-gold { border-color: #c9a84c; color: #c9a84c; }
  .fallback-note { font-size: 11px; color: #6b6880; padding: 8px 12px; border-left: 2px solid #6b6880; margin-bottom: 16px; }
`;

// ══════════════════════════════════════════════════════════════════════════
// COLLEGE HEADER
// ── HOW TO ADD YOUR LOGOS ─────────────────────────────────────────────────
//  Option A (recommended): Place logo files in your React public/ folder
//    e.g. public/srm_logo.png  and  public/srmvec_logo.png
//    Then set: const SRM_LOGO = "/srm_logo.png"
//
//  Option B: Import directly from src/assets/
//    import srmLogo    from "./assets/srm_logo.png"
//    import srmvecLogo from "./assets/srmvec_logo.png"
//    Then set: const SRM_LOGO = srmLogo
//
//  The component uses onError fallback so it shows text if image fails.
// ─────────────────────────────────────────────────────────────────────────
const SRM_LOGO    = "/Srm_vec_logo.jpg";     // ← change to your SRM logo path
const SRMVEC_LOGO = "/1773799676160.png";  // ← change to your SRMVEC logo path

function CollegeHeader() {
  const [srmErr,    setSrmErr]    = useState(false);
  const [srmvecErr, setSrmvecErr] = useState(false);

  return (
    <div className="college-header">
      <div className="college-header-inner">

        {/* LEFT LOGO */}
        <div className="college-logo-box">
          {!srmErr ? (
            <img src={SRM_LOGO} alt="SRM Logo" onError={() => setSrmErr(true)} />
          ) : (
            <div className="logo-fallback">SRM<br />GROUP</div>
          )}
        </div>

        {/* CENTER TEXT */}
        <div className="college-center">
          <div className="college-name">SRM VALLIAMMAI ENGINEERING COLLEGE</div>
          <div className="college-sub">(A Member of SRM Group of Institutions)</div>
          <div className="college-dept">
            Department of Artificial Intelligence and Data Science
          </div>
          <div className="college-divider" />
          <div className="college-project">
            JusticeAI: An Intelligent Legal Research &amp; Case Outcome
            Prediction System for the Indian Judiciary
          </div>
        </div>

        {/* RIGHT LOGO */}
        <div className="college-logo-box">
          {!srmvecErr ? (
            <img src={SRMVEC_LOGO} alt="SRMVEC Logo" onError={() => setSrmvecErr(true)} />
          ) : (
            <div className="logo-fallback">SRM<br />VALLIAMMAI</div>
          )}
        </div>

      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════
function renderMarkdown(text) {
  if (!text) return "";
  return text
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/^#### \*\*(.*?)\*\*/gm, "<h4>$1</h4>")
    .replace(/^### \*\*(.*?)\*\*/gm,  "<h3>$1</h3>")
    .replace(/^#### (.*?)$/gm,        "<h4>$1</h4>")
    .replace(/^### (.*?)$/gm,         "<h3>$1</h3>")
    .replace(/\*\*(.*?)\*\*/g,        "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g,            "<em>$1</em>")
    .replace(/^---$/gm,               "<hr/>")
    .replace(/^- (.*?)$/gm,           "<li>$1</li>")
    .replace(/(<li>.*<\/li>)/gs,      "<ul>$1</ul>")
    .replace(/\n{2,}/g,               "<br/><br/>")
    .replace(/\n/g,                   "<br/>");
}

function getOutcomeColor(outcome) {
  const map = {
    "Bail Granted":     "#4caf7d",
    "Bail Rejected":    "#e05c5c",
    "Appeal Allowed":   "#7dd3fc",
    "Appeal Dismissed": "#c9a84c",
    "Acquitted":        "#4caf7d",
    "Convicted":        "#e05c5c",
  };
  return map[outcome] || "#6b6880";
}

function getSimColor(score) {
  if (score >= 0.75) return "#4caf7d";
  if (score >= 0.65) return "#c9a84c";
  return "#e05c5c";
}

function buildKanoonURL(title, court, year) {
  const q = encodeURIComponent([title, court, year].filter(Boolean).join(" "));
  return `https://indiankanoon.org/search/?formInput=${q}`;
}

// ══════════════════════════════════════════════════════════════════════════
// CASE MODAL
// ══════════════════════════════════════════════════════════════════════════
function CaseModal({ c, onClose }) {
  const [copied, setCopied] = useState(false);

  const pct        = Math.round((c.similarity_score || 0) * 100);
  const simCol     = getSimColor(c.similarity_score || 0);
  const outCol     = getOutcomeColor(c.outcome);
  const kanoonHref = buildKanoonURL(c.title, c.court, c.year);

  const ipcList = c.ipc_sections
    ? (Array.isArray(c.ipc_sections)
        ? c.ipc_sections
        : String(c.ipc_sections).split(",").map(s => s.trim()).filter(Boolean))
    : [];

  const copyText = () => {
    const citation = `${c.title} | ${c.court} | ${c.year} | Outcome: ${c.outcome}`;
    navigator.clipboard?.writeText(citation).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  useEffect(() => {
    const h = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [onClose]);

  return (
    <div
      style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.88)",
               display: "flex", justifyContent: "center", alignItems: "center",
               zIndex: 999, padding: 20 }}
      onClick={onClose}
    >
      <div
        style={{ background: "#12121a", border: "1px solid #c9a84c",
                 width: "100%", maxWidth: 720, maxHeight: "90vh",
                 display: "flex", flexDirection: "column", overflow: "hidden" }}
        onClick={e => e.stopPropagation()}
      >
        {/* HEADER */}
        <div style={{ padding: "22px 26px 16px", borderBottom: "1px solid #1e1e2e", flexShrink: 0 }}>
          <div style={{ fontFamily: "'Playfair Display', serif", fontSize: 19,
                        fontWeight: 700, color: "#e8e4d9", marginBottom: 10, lineHeight: 1.4 }}>
            {c.title || c.case_id || "Case Details"}
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 8 }}>
            {c.court    && <span style={{ fontSize: 10, color: "#6b6880", background: "#1e1e2e", padding: "3px 10px", letterSpacing: 1 }}>🏛 {c.court}</span>}
            {c.year     && <span style={{ fontSize: 10, color: "#6b6880", background: "#1e1e2e", padding: "3px 10px", letterSpacing: 1 }}>📅 {c.year}</span>}
            {c.case_type && <span style={{ fontSize: 10, color: "#6b6880", background: "#1e1e2e", padding: "3px 10px", letterSpacing: 1 }}>{c.case_type}</span>}
            {c.outcome  && (
              <span style={{ fontSize: 10, fontWeight: 600, padding: "3px 12px", letterSpacing: 1,
                             textTransform: "uppercase", border: `1px solid ${outCol}`, color: outCol }}>
                {c.outcome}
              </span>
            )}
          </div>
        </div>

        {/* BODY */}
        <div style={{ padding: "20px 26px", overflowY: "auto", flex: 1,
                      display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Similarity */}
          <div>
            <div style={{ fontSize: 10, color: "#c9a84c", letterSpacing: 2,
                          textTransform: "uppercase", marginBottom: 10 }}>
              Relevance Score
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
              <div>
                <div style={{ fontFamily: "'Playfair Display', serif", fontSize: 30,
                              fontWeight: 700, color: simCol, lineHeight: 1 }}>
                  {pct}%
                </div>
                <div style={{ fontSize: 9, color: "#6b6880", letterSpacing: 1, marginTop: 4 }}>SIMILARITY</div>
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ height: 4, background: "#1e1e2e" }}>
                  <div style={{ height: 4, width: `${pct}%`, background: simCol, transition: "width 0.6s ease" }} />
                </div>
                <div style={{ fontSize: 10, color: "#6b6880", marginTop: 6, letterSpacing: 1 }}>
                  {pct >= 75 ? "High relevance — strong precedent match"
                   : pct >= 65 ? "Moderate relevance — review carefully"
                   : "Low relevance — consider refining query"}
                </div>
              </div>
            </div>
          </div>

          {/* Case details grid */}
          <div>
            <div style={{ fontSize: 10, color: "#c9a84c", letterSpacing: 2,
                          textTransform: "uppercase", marginBottom: 10 }}>
              Case Details
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              {[
                ["Case ID",   c.case_id],
                ["Court",     c.court],
                ["Year",      c.year],
                ["Case Type", c.case_type],
                ["Outcome",   c.outcome],
                ["Match",     `${pct}%`],
              ].map(([k, v]) => v ? (
                <div key={k} style={{ background: "#0a0a0f", border: "1px solid #1e1e2e", padding: "10px 12px" }}>
                  <div style={{ fontSize: 9, color: "#6b6880", letterSpacing: 1,
                                textTransform: "uppercase", marginBottom: 4 }}>{k}</div>
                  <div style={{ fontSize: 12, color: "#e8e4d9" }}>{v}</div>
                </div>
              ) : null)}
            </div>
          </div>

          {/* IPC Sections */}
          {ipcList.length > 0 && (
            <div>
              <div style={{ fontSize: 10, color: "#c9a84c", letterSpacing: 2,
                            textTransform: "uppercase", marginBottom: 10 }}>
                IPC / Relevant Sections
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {ipcList.map((sec, i) => (
                  <span key={i} style={{ fontSize: 10, color: "#7dd3fc",
                                         border: "1px solid #1e3a5f", background: "#0c1f35",
                                         padding: "3px 10px", letterSpacing: 1 }}>
                    § {sec}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Full text */}
          {(c.full_text || c.summary) && (
            <div>
              <div style={{ fontSize: 10, color: "#c9a84c", letterSpacing: 2,
                            textTransform: "uppercase", marginBottom: 10 }}>
                {c.full_text ? "Judgment Excerpt" : "Case Summary"}
              </div>
              <div style={{ background: "#0a0a0f", border: "1px solid #1e1e2e",
                            borderLeft: "2px solid #c9a84c", padding: "14px 16px",
                            fontSize: 12, lineHeight: 1.8, color: "#b0acbf",
                            maxHeight: 200, overflowY: "auto", whiteSpace: "pre-wrap" }}>
                {c.full_text || c.summary}
              </div>
            </div>
          )}
        </div>

        {/* FOOTER */}
        <div style={{ padding: "16px 26px", borderTop: "1px solid #1e1e2e",
                      display: "flex", gap: 10, flexWrap: "wrap",
                      alignItems: "center", flexShrink: 0 }}>
          <a href={kanoonHref} target="_blank" rel="noopener noreferrer"
            style={{ background: "#c9a84c", color: "#0a0a0f", border: "none",
                     fontFamily: "'JetBrains Mono', monospace", fontSize: 11,
                     fontWeight: 500, letterSpacing: 1, textTransform: "uppercase",
                     padding: "10px 20px", cursor: "pointer", textDecoration: "none",
                     display: "inline-flex", alignItems: "center", gap: 6 }}>
            🔗 View on Indian Kanoon
          </a>
          <button onClick={copyText}
            style={{ background: "none", color: copied ? "#4caf7d" : "#6b6880",
                     border: `1px solid ${copied ? "#4caf7d" : "#1e1e2e"}`,
                     fontFamily: "'JetBrains Mono', monospace", fontSize: 11,
                     letterSpacing: 1, textTransform: "uppercase",
                     padding: "10px 20px", cursor: "pointer", transition: "all 0.2s" }}>
            {copied ? "✓ Copied!" : "📋 Copy Citation"}
          </button>
          <button onClick={onClose}
            style={{ marginLeft: "auto", background: "none", color: "#6b6880",
                     border: "1px solid #1e1e2e", fontFamily: "'JetBrains Mono', monospace",
                     fontSize: 11, letterSpacing: 1, textTransform: "uppercase",
                     padding: "10px 20px", cursor: "pointer", transition: "all 0.2s" }}>
            ✕ Close
          </button>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════
// ANALYSIS TAB
// ══════════════════════════════════════════════════════════════════════════
function AnalyseTab() {
  const [query,        setQuery]        = useState("");
  const [caseType,     setCaseType]     = useState("Criminal");
  const [court,        setCourt]        = useState("Supreme Court of India");
  const [year,         setYear]         = useState(2021);
  const [result,       setResult]       = useState(null);
  const [loading,      setLoading]      = useState(false);
  const [error,        setError]        = useState("");
  const [selectedCase, setSelectedCase] = useState(null);

  const analyse = async () => {
    if (!query.trim()) return;
    setLoading(true); setError(""); setResult(null);
    try {
      const res = await API.post("/legal/analyze", { query, case_type: caseType, court, year });
      setResult(res.data);
    } catch (e) {
      setError("Backend error: " + (e.response?.data?.detail || e.message));
    }
    setLoading(false);
  };

  return (
    <div>
      <div className="section-title">Legal Analysis</div>
      <div className="section-sub">SEMANTIC SEARCH + OUTCOME PREDICTION + AI EXPLANATION</div>

      <div className="input-group">
        <label className="label">Describe your case or legal query</label>
        <textarea className="textarea" value={query} onChange={e => setQuery(e.target.value)}
          placeholder="e.g. bail murder IPC 302 accused High Court..." />
      </div>

      <div className="row" style={{ marginBottom: 16 }}>
        <div className="input-group">
          <label className="label">Case Type</label>
          <select className="select" value={caseType} onChange={e => setCaseType(e.target.value)}>
            <option>Criminal</option><option>Civil</option>
            <option>Family</option><option>Constitutional</option>
          </select>
        </div>
        <div className="input-group">
          <label className="label">Court</label>
          <select className="select" value={court} onChange={e => setCourt(e.target.value)}>
            <option>Supreme Court of India</option>
            <option>High Court</option>
            <option>Sessions Court</option>
            <option>District Court</option>
          </select>
        </div>
      </div>

      <div className="input-group" style={{ marginBottom: 20 }}>
        <label className="label">Year — {year}</label>
        <input type="range" min="2000" max="2024" value={year}
          onChange={e => setYear(parseInt(e.target.value))}
          style={{ width: "100%", accentColor: "#c9a84c" }} />
      </div>

      <button className="btn" onClick={analyse} disabled={loading || !query.trim()}>
        {loading ? "Analysing..." : "→ Run Analysis"}
      </button>

      {loading && (
        <div className="loading">
          <div className="spinner" /><span>Processing through all modules...</span>
        </div>
      )}
      {error && <div style={{ color: "#e05c5c", fontSize: 12, marginTop: 16 }}>{error}</div>}

      {result && (
        <div style={{ marginTop: 32 }}>
          <div className="prediction-box">
            <div className="prediction-label">Predicted Outcome</div>
            <div className="prediction-value">{result.prediction?.prediction}</div>
            <div className="prediction-conf">
              Confidence: {Math.round((result.prediction?.confidence || 0) * 100)}% ·{" "}
              {result.fallback_used
                ? <span className="badge" style={{ borderColor: "#6b6880", color: "#6b6880" }}>General Knowledge</span>
                : <span className="badge badge-green">Case Match Found</span>}
            </div>
          </div>

          {result.similar_cases?.length > 0 && (
            <div>
              <div style={{ fontSize: 11, color: "#c9a84c", letterSpacing: 2,
                            textTransform: "uppercase", marginBottom: 12 }}>
                Similar Cases — {result.similar_cases.length} found · click any card to view full details
              </div>
              {result.similar_cases.map((c, i) => (
                <div className="card" key={i} onClick={() => setSelectedCase(c)}
                  style={{ cursor: "pointer",
                           borderColor: selectedCase === c ? "#c9a84c" : "#1e1e2e",
                           transition: "border-color 0.2s" }}>
                  <div className="card-title">{c.title?.split("&")[0].trim()}</div>
                  <div className="card-meta">
                    {c.court} · {c.year}
                    {c.outcome && (
                      <span style={{ marginLeft: 10, fontSize: 10,
                                     border: `1px solid ${getOutcomeColor(c.outcome)}`,
                                     color: getOutcomeColor(c.outcome),
                                     padding: "1px 8px", letterSpacing: 1, textTransform: "uppercase" }}>
                        {c.outcome}
                      </span>
                    )}
                  </div>
                  <div className="card-body">{c.summary}</div>
                  <div className="score-bar">
                    <div className="score-label">
                      <span>Relevance</span>
                      <span className="badge badge-gold">{Math.round(c.similarity_score * 100)}%</span>
                    </div>
                    <div className="score-track">
                      <div className="score-fill" style={{ width: `${Math.round(c.similarity_score * 100)}%` }} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="ai-label">AI Legal Analysis</div>
          <div className="ai-response"
            dangerouslySetInnerHTML={{ __html: renderMarkdown(result.ai_explanation) }} />
        </div>
      )}

      {selectedCase && <CaseModal c={selectedCase} onClose={() => setSelectedCase(null)} />}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════
// CHAT TAB
// ══════════════════════════════════════════════════════════════════════════
function ChatTab() {
  const [messages, setMessages] = useState([
    { role: "ai", text: "Vanakkam. I am JusticeAI — your Indian legal assistant. Ask me about IPC sections, bail procedures, case outcomes, or any legal matter." }
  ]);
  const [input,   setInput]   = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  const QUICK = [
    "What is IPC Section 302?",
    "Explain bail under CrPC 437",
    "Rights of accused in India",
    "What is anticipatory bail?",
  ];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async (text) => {
    const msg = text || input.trim();
    if (!msg) return;
    setMessages(prev => [...prev, { role: "user", text: msg }]);
    setInput(""); setLoading(true);
    try {
      const res = await API.post("/chat/chatbot/ask", { message: msg });
      setMessages(prev => [...prev, { role: "ai", text: res.data.reply }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: "ai", text: "Error: " + (e.response?.data?.detail || e.message) }]);
    }
    setLoading(false);
  };

  return (
    <div>
      <div className="section-title">Legal Assistant</div>
      <div className="section-sub">RAG-POWERED CHATBOT · INDIAN LAW KNOWLEDGE</div>
      <div className="quick-prompts">
        {QUICK.map((q, i) => <button key={i} className="quick-btn" onClick={() => send(q)}>{q}</button>)}
      </div>
      <div className="chat-window">
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            <div className="msg-avatar">{m.role === "user" ? "U" : "⚖"}</div>
            {m.role === "ai"
              ? <div className="msg-bubble" dangerouslySetInnerHTML={{ __html: renderMarkdown(m.text) }} />
              : <div className="msg-bubble">{m.text}</div>}
          </div>
        ))}
        {loading && (
          <div className="msg">
            <div className="msg-avatar">⚖</div>
            <div className="msg-bubble">
              <div className="loading" style={{ padding: 0 }}>
                <div className="spinner" /><span>Thinking...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="chat-input-row">
        <input className="chat-input" value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && !e.shiftKey && send()}
          placeholder="Ask a legal question... (Enter to send)" />
        <button className="btn" onClick={() => send()} disabled={loading || !input.trim()}>Send</button>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════
// OCR TAB
// ══════════════════════════════════════════════════════════════════════════
function OCRTab() {
  const [file,    setFile]    = useState(null);
  const [result,  setResult]  = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState("");
  const [drag,    setDrag]    = useState(false);
  const fileRef = useRef(null);

  const analyse = async () => {
    if (!file) return;
    setLoading(true); setError(""); setResult(null);
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await API.post("/legal/analyze-document", form,
        { headers: { "Content-Type": "multipart/form-data" } });
      setResult(res.data);
    } catch (e) {
      setError("Error: " + (e.response?.data?.detail || e.message));
    }
    setLoading(false);
  };

  const onDrop = (e) => {
    e.preventDefault(); setDrag(false);
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  };

  return (
    <div>
      <div className="section-title">Document Analysis</div>
      <div className="section-sub">OCR EXTRACTION + FULL PIPELINE ANALYSIS</div>
      <div className={`drop-zone ${drag ? "active" : ""}`}
        onDragOver={e => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={onDrop}
        onClick={() => fileRef.current?.click()}>
        <div className="drop-icon">📄</div>
        <div className="drop-text">
          {file ? <span style={{ color: "#c9a84c" }}>{file.name}</span>
                : "Drop PDF or image here, or click to browse"}
        </div>
        <div className="drop-text" style={{ marginTop: 6 }}>Supports: PDF, PNG, JPG, TIFF</div>
        <input ref={fileRef} type="file" accept=".pdf,.png,.jpg,.jpeg,.tiff,.bmp"
          style={{ display: "none" }} onChange={e => setFile(e.target.files[0])} />
      </div>
      <button className="btn" onClick={analyse} disabled={!file || loading}>
        {loading ? "Processing..." : "→ Analyse Document"}
      </button>
      {loading && (
        <div className="loading"><div className="spinner" /><span>Running OCR and full pipeline...</span></div>
      )}
      {error && <div style={{ color: "#e05c5c", fontSize: 12, marginTop: 16 }}>{error}</div>}
      {result && (
        <div style={{ marginTop: 32 }}>
          <div style={{ fontSize: 11, color: "#6b6880", marginBottom: 20 }}>
            {result.filename} · {result.word_count} words extracted
          </div>
          {result.prediction && (
            <div className="prediction-box">
              <div className="prediction-label">Predicted Outcome</div>
              <div className="prediction-value">{result.prediction?.prediction}</div>
              <div className="prediction-conf">
                Confidence: {Math.round((result.prediction?.confidence || 0) * 100)}%
              </div>
            </div>
          )}
          {result.extracted_text && (
            <div>
              <div className="ai-label">Extracted Text</div>
              <div className="ai-response" style={{ maxHeight: 200, overflow: "auto", fontSize: 12, whiteSpace: "pre-wrap" }}>
                {result.extracted_text}
              </div>
            </div>
          )}
          {result.ai_explanation && (
            <div>
              <div className="ai-label">AI Legal Analysis</div>
              <div className="ai-response"
                dangerouslySetInnerHTML={{ __html: renderMarkdown(result.ai_explanation) }} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════════════
// ROOT
// ══════════════════════════════════════════════════════════════════════════
const TABS = [
  { id: "analyse", label: "Analysis"  },
  { id: "chat",    label: "Assistant" },
  { id: "ocr",     label: "Documents" },
];

export default function App() {
  const [tab, setTab] = useState("analyse");

  return (
    <>
      <style>{css}</style>
      <div className="app">

        {/* ── COLLEGE HEADER ── */}
        <CollegeHeader />

        {/* ── NAV BAR ── */}
        <nav className="nav">
          <div className="nav-logo">Justice<span>AI</span></div>
          {TABS.map(t => (
            <button key={t.id}
              className={`nav-tab ${tab === t.id ? "active" : ""}`}
              onClick={() => setTab(t.id)}>
              {t.label}
            </button>
          ))}
          <div className="nav-status">
            <div className="dot" />
            <span>Backend connected</span>
          </div>
        </nav>

        {/* ── MAIN CONTENT ── */}
        <main className="main">
          {tab === "analyse" && <AnalyseTab />}
          {tab === "chat"    && <ChatTab    />}
          {tab === "ocr"     && <OCRTab     />}
        </main>

      </div>
    </>
  );
}