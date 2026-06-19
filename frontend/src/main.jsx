import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  Camera,
  CheckCircle2,
  Download,
  FileSpreadsheet,
  LogOut,
  Play,
  Plus,
  RefreshCcw,
  Shield,
  Square,
  Upload,
  UserCheck,
} from "lucide-react";
import { api, ApiError } from "./services/api";
import "./styles/app.css";

const initialSessionForm = {
  title: "",
  session_type: "exam",
  course_name: "",
  group_name: "",
  starts_at: "",
};

function App() {
  const [token, setToken] = useState(() => localStorage.getItem("auth_token") || "");
  const [currentAdmin, setCurrentAdmin] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const [sessionDetail, setSessionDetail] = useState(null);
  const [recognitionEvents, setRecognitionEvents] = useState([]);
  const [loginForm, setLoginForm] = useState({ username: "admin", password: "" });
  const [sessionForm, setSessionForm] = useState(initialSessionForm);
  const [message, setMessage] = useState("");
  const [recognitionResult, setRecognitionResult] = useState(null);
  const [identificationStatus, setIdentificationStatus] = useState(null);
  const [busy, setBusy] = useState(false);

  const authedApi = useMemo(() => api.withToken(token), [token]);

  useEffect(() => {
    if (!token) return;
    loadInitialData();
  }, [token]);

  useEffect(() => {
    if (!token || !selectedSession || !identificationStatus?.running) return;

    const intervalId = window.setInterval(() => {
      loadIdentificationStatus(selectedSession.id);
      openSession(selectedSession.id);
    }, 1500);

    return () => window.clearInterval(intervalId);
  }, [token, selectedSession?.id, identificationStatus?.running]);

  async function loadInitialData() {
    try {
      const [admin, sessionList] = await Promise.all([
        authedApi.get("/auth/me"),
        authedApi.get("/attendance/sessions"),
      ]);
      setCurrentAdmin(admin);
      setSessions(sessionList);
      if (sessionList.length > 0 && !selectedSession) {
        await openSession(sessionList[0].id);
      }
    } catch (error) {
      handleError(error);
      logout();
    }
  }

  async function login(event) {
    event.preventDefault();
    setBusy(true);
    setMessage("");

    try {
      const response = await api.post("/auth/login", loginForm);
      localStorage.setItem("auth_token", response.access_token);
      setToken(response.access_token);
    } catch (error) {
      handleError(error);
    } finally {
      setBusy(false);
    }
  }

  function logout() {
    localStorage.removeItem("auth_token");
    setToken("");
    setCurrentAdmin(null);
    setSessions([]);
    setSelectedSession(null);
    setSessionDetail(null);
    setRecognitionEvents([]);
    setRecognitionResult(null);
    setIdentificationStatus(null);
  }

  async function createSession(event) {
    event.preventDefault();
    setBusy(true);
    setMessage("");

    const payload = {
      ...sessionForm,
      starts_at: sessionForm.starts_at || null,
      course_name: sessionForm.course_name || null,
      group_name: sessionForm.group_name || null,
    };

    try {
      const created = await authedApi.post("/attendance/sessions", payload);
      setSessionForm(initialSessionForm);
      await refreshSessions(created.id);
      setMessage("Session creee.");
    } catch (error) {
      handleError(error);
    } finally {
      setBusy(false);
    }
  }

  async function refreshSessions(openSessionId = selectedSession?.id) {
    const sessionList = await authedApi.get("/attendance/sessions");
    setSessions(sessionList);
    if (openSessionId) {
      await openSession(openSessionId);
    }
  }

  async function openSession(sessionId) {
    const [detail, events] = await Promise.all([
      authedApi.get(`/attendance/sessions/${sessionId}`),
      authedApi.get(`/attendance/sessions/${sessionId}/events?limit=100`),
    ]);
    setSelectedSession(detail);
    setSessionDetail(detail);
    setRecognitionEvents(events);
    await loadIdentificationStatus(sessionId);
  }

  async function importSheet(event) {
    const file = event.target.files?.[0];
    if (!file || !selectedSession) return;

    setBusy(true);
    setMessage("");

    try {
      const formData = new FormData();
      formData.append("file", file);
      const result = await authedApi.upload(
        `/attendance/sessions/${selectedSession.id}/import`,
        formData,
      );
      await openSession(selectedSession.id);
      setMessage(`${result.imported_students} etudiants importes.`);
    } catch (error) {
      handleError(error);
    } finally {
      event.target.value = "";
      setBusy(false);
    }
  }

  async function startIdentification() {
    if (!selectedSession) return;
    setBusy(true);
    setMessage("");

    try {
      const status = await authedApi.post(
        `/attendance/sessions/${selectedSession.id}/identification/start`,
        {},
      );
      setIdentificationStatus(status);
      setRecognitionResult(status.last_result);
      await openSession(selectedSession.id);
      setMessage("Identification continue demarree.");
    } catch (error) {
      handleError(error);
    } finally {
      setBusy(false);
    }
  }

  async function stopIdentification() {
    if (!selectedSession) return;
    setBusy(true);
    setMessage("");

    try {
      const status = await authedApi.post(
        `/attendance/sessions/${selectedSession.id}/identification/stop`,
        {},
      );
      setIdentificationStatus(status);
      setRecognitionResult(status.last_result);
      await openSession(selectedSession.id);
      setMessage("Identification arretee.");
    } catch (error) {
      handleError(error);
    } finally {
      setBusy(false);
    }
  }

  async function loadIdentificationStatus(sessionId) {
    try {
      const status = await authedApi.get(`/attendance/sessions/${sessionId}/identification/status`);
      setIdentificationStatus(status);
      if (status.last_result) {
        setRecognitionResult(status.last_result);
      }
      if (status.last_error) {
        setMessage(status.last_error);
      }
    } catch {
      // Status polling should not interrupt the main workflow.
    }
  }

  async function exportSheet() {
    if (!selectedSession) return;
    setBusy(true);
    setMessage("");

    try {
      await authedApi.download(
        `/attendance/sessions/${selectedSession.id}/export`,
        `attendance_session_${selectedSession.id}.xlsx`,
      );
      setMessage("Export genere.");
    } catch (error) {
      handleError(error);
    } finally {
      setBusy(false);
    }
  }

  async function exportRecognitionEvents() {
    if (!selectedSession) return;
    setBusy(true);
    setMessage("");

    try {
      await authedApi.download(
        `/attendance/sessions/${selectedSession.id}/events/export`,
        `recognition_events_session_${selectedSession.id}.xlsx`,
      );
      setMessage("Journal exporte.");
    } catch (error) {
      handleError(error);
    } finally {
      setBusy(false);
    }
  }

  async function refreshRecognitionIndex() {
    setBusy(true);
    setMessage("");

    try {
      const result = await authedApi.post("/recognition/known-index/refresh", {});
      setMessage(`Index FaceNet rafraichi: ${result.known_embeddings_count} embeddings.`);
    } catch (error) {
      handleError(error);
    } finally {
      setBusy(false);
    }
  }

  function formatRecognitionMessage(result) {
    const score = result.score == null ? "" : ` Score ${Number(result.score).toFixed(3)}.`;
    const threshold =
      result.threshold == null ? "" : ` Seuil ${Number(result.threshold).toFixed(3)}.`;
    const student = result.display_name ? ` ${result.display_name}.` : "";
    return `${result.message}.${student}${score}${threshold}`;
  }

  function formatTime(value) {
    if (!value) return "";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  }

  const eventStats = useMemo(() => {
    const total = recognitionEvents.length;
    const recognized = recognitionEvents.filter((event) => event.recognized).length;
    const belowThreshold = recognitionEvents.filter((event) =>
      event.message.toLowerCase().includes("below threshold"),
    ).length;
    const multipleFaces = recognitionEvents.filter((event) => event.faces_count > 1).length;

    return {
      total,
      recognized,
      rejected: total - recognized,
      belowThreshold,
      multipleFaces,
    };
  }, [recognitionEvents]);

  function handleError(error) {
    if (error instanceof ApiError) {
      setMessage(error.message);
      return;
    }
    setMessage("Erreur inattendue.");
  }

  if (!token) {
    return (
      <main className="login-shell">
        <section className="login-panel">
          <div className="brand-mark">
            <Shield size={24} />
          </div>
          <h1>Smart Faculty Attendance</h1>
          <form onSubmit={login} className="login-form">
            <label>
              Identifiant
              <input
                value={loginForm.username}
                onChange={(event) => setLoginForm({ ...loginForm, username: event.target.value })}
                autoComplete="username"
              />
            </label>
            <label>
              Mot de passe
              <input
                type="password"
                value={loginForm.password}
                onChange={(event) => setLoginForm({ ...loginForm, password: event.target.value })}
                autoComplete="current-password"
              />
            </label>
            <button className="primary-action" disabled={busy}>
              Connexion
            </button>
          </form>
          {message && <p className="form-message">{message}</p>}
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-header">
          <div>
            <p className="eyebrow">Admin local</p>
            <h1>Presence faciale</h1>
          </div>
          <button className="icon-button" onClick={logout} title="Deconnexion">
            <LogOut size={18} />
          </button>
        </div>

        <form className="session-form" onSubmit={createSession}>
          <div className="section-title">
            <Plus size={16} />
            <span>Nouvelle session</span>
          </div>
          <input
            placeholder="Titre"
            value={sessionForm.title}
            onChange={(event) => setSessionForm({ ...sessionForm, title: event.target.value })}
            required
          />
          <div className="segmented">
            <button
              type="button"
              className={sessionForm.session_type === "exam" ? "active" : ""}
              onClick={() => setSessionForm({ ...sessionForm, session_type: "exam" })}
            >
              Examen
            </button>
            <button
              type="button"
              className={sessionForm.session_type === "course" ? "active" : ""}
              onClick={() => setSessionForm({ ...sessionForm, session_type: "course" })}
            >
              Cours
            </button>
          </div>
          <input
            placeholder="Matiere"
            value={sessionForm.course_name}
            onChange={(event) => setSessionForm({ ...sessionForm, course_name: event.target.value })}
          />
          <input
            placeholder="Groupe"
            value={sessionForm.group_name}
            onChange={(event) => setSessionForm({ ...sessionForm, group_name: event.target.value })}
          />
          <input
            type="datetime-local"
            value={sessionForm.starts_at}
            onChange={(event) => setSessionForm({ ...sessionForm, starts_at: event.target.value })}
          />
          <button className="primary-action" disabled={busy}>
            Creer
          </button>
        </form>

        <div className="session-list">
          <div className="section-title">
            <FileSpreadsheet size={16} />
            <span>Sessions</span>
          </div>
          {sessions.map((session) => (
            <button
              key={session.id}
              className={`session-item ${selectedSession?.id === session.id ? "selected" : ""}`}
              onClick={() => openSession(session.id)}
            >
              <span>{session.title}</span>
              <small>{session.course_name || session.session_type}</small>
            </button>
          ))}
        </div>
      </aside>

      <section className="content">
        <header className="topbar">
          <div>
            <p className="eyebrow">Connecte: {currentAdmin?.username || "admin"}</p>
            <h2>{selectedSession?.title || "Aucune session selectionnee"}</h2>
          </div>
          <button className="secondary-action" onClick={() => refreshSessions()} disabled={busy}>
            <RefreshCcw size={16} />
            Actualiser
          </button>
        </header>

        {message && <div className="status-banner">{message}</div>}

        {selectedSession ? (
          <>
            <div className="toolbar">
              <label className="file-action">
                <Upload size={16} />
                Import Excel
                <input type="file" accept=".xlsx,.xlsm" onChange={importSheet} />
              </label>
              {identificationStatus?.running ? (
                <button className="danger-action" onClick={stopIdentification} disabled={busy}>
                  <Square size={16} />
                  Arreter
                </button>
              ) : (
                <button className="secondary-action" onClick={startIdentification} disabled={busy}>
                  <Play size={16} />
                  Identifier
                </button>
              )}
              <button className="secondary-action" onClick={refreshRecognitionIndex} disabled={busy}>
                <UserCheck size={16} />
                Refresh FaceNet
              </button>
              <button className="secondary-action" onClick={exportSheet} disabled={busy}>
                <Download size={16} />
                Export
              </button>
            </div>

            {recognitionResult && (
              <div className={`recognition-panel ${recognitionResult.recognized ? "success" : "warning"}`}>
                <div>
                  <span>Visages</span>
                  <strong>{recognitionResult.faces_count}</strong>
                </div>
                <div>
                  <span>Etudiant</span>
                  <strong>{recognitionResult.display_name || "Non reconnu"}</strong>
                </div>
                <div>
                  <span>Score</span>
                  <strong>
                    {recognitionResult.score == null
                      ? "-"
                      : Number(recognitionResult.score).toFixed(3)}
                  </strong>
                </div>
                <div>
                  <span>Seuil</span>
                  <strong>
                    {recognitionResult.threshold == null
                      ? "-"
                      : Number(recognitionResult.threshold).toFixed(3)}
                  </strong>
                </div>
                <p>{recognitionResult.message}</p>
              </div>
            )}

            {identificationStatus?.running && (
              <div className="live-indicator">
                <Camera size={16} />
                Identification continue active
              </div>
            )}

            <div className="summary-grid">
              <Metric label="Total" value={sessionDetail?.records?.length || 0} />
              <Metric
                label="Presents"
                value={(sessionDetail?.records || []).filter((record) => record.status === "present").length}
              />
              <Metric
                label="Absents"
                value={(sessionDetail?.records || []).filter((record) => record.status !== "present").length}
              />
            </div>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>Nom</th>
                    <th>Prenom</th>
                    <th>Groupe</th>
                    <th>Statut</th>
                    <th>Score</th>
                  </tr>
                </thead>
                <tbody>
                  {(sessionDetail?.records || []).map((record) => (
                    <tr key={record.id}>
                      <td>{record.student_code}</td>
                      <td>{record.last_name}</td>
                      <td>{record.first_name}</td>
                      <td>{record.group_name || ""}</td>
                      <td>
                        <span className={`status-pill ${record.status}`}>
                          {record.status === "present" && <CheckCircle2 size={14} />}
                          {record.status}
                        </span>
                      </td>
                      <td>{record.recognition_score?.toFixed?.(3) || ""}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <section className="audit-section">
              <div className="audit-header">
                <div className="section-title">
                  <Activity size={16} />
                  <span>Journal d'identification</span>
                </div>
                <button className="secondary-action" onClick={exportRecognitionEvents} disabled={busy}>
                  <Download size={16} />
                  Export journal
                </button>
              </div>

              <div className="audit-metrics">
                <Metric label="Tentatives" value={eventStats.total} />
                <Metric label="Reconnues" value={eventStats.recognized} />
                <Metric label="Rejetees" value={eventStats.rejected} />
                <Metric label="Sous seuil" value={eventStats.belowThreshold} />
                <Metric label="Multi-visages" value={eventStats.multipleFaces} />
              </div>

              <div className="table-wrap audit-table">
                <table>
                  <thead>
                    <tr>
                      <th>Heure</th>
                      <th>Resultat</th>
                      <th>Etudiant</th>
                      <th>Score</th>
                      <th>Seuil</th>
                      <th>Visages</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recognitionEvents.length === 0 ? (
                      <tr>
                        <td colSpan="6" className="muted-cell">
                          Aucun evenement d'identification.
                        </td>
                      </tr>
                    ) : (
                      recognitionEvents.map((event) => (
                        <tr key={event.id}>
                          <td>{formatTime(event.created_at)}</td>
                          <td>
                            <span className={`event-pill ${event.recognized ? "recognized" : ""}`}>
                              {event.message}
                            </span>
                          </td>
                          <td>{event.student_code || "-"}</td>
                          <td>{event.score == null ? "-" : Number(event.score).toFixed(3)}</td>
                          <td>{event.threshold == null ? "-" : Number(event.threshold).toFixed(3)}</td>
                          <td>{event.faces_count}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        ) : (
          <div className="empty-state">Cree ou selectionne une session.</div>
        )}
      </section>
    </main>
  );
}

function Metric({ label, value }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
