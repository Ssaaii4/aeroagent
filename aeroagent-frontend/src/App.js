import { useState, useRef, useEffect } from "react";
import "./App.css";

const API = "https://aeroagent-api.salmonsand-ae41dd1f.eastus.azurecontainerapps.io";
const FRONTEND = "https://witty-flower-0e99f2c10.7.azurestaticapps.net";

function generateSessionId() {
  return Math.random().toString(36).substring(2, 15);
}

export default function App() {
  const [messages, setMessages]   = useState([{
    role: "agent",
    text: "Hi! I'm AeroAgent ✈\n\nTell me where you want to fly — for example:\n'Find me the cheapest flight from New York to London on August 15th 2026'"
  }]);
  const [input, setInput]         = useState("");
  const [loading, setLoading]     = useState(false);
  const [state, setState]         = useState("chatting");
  const [sessionId]               = useState(generateSessionId);
  const [summary, setSummary]     = useState(null);
  const [approvalId, setApprovalId] = useState(null);
  const [otp, setOtp]             = useState("");
  const [otpError, setOtpError]   = useState("");
  const bottomRef                 = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, state]);

  // Handle redirect back from approval page
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const approved = params.get("approved");
    const id = params.get("id");
    if (approved === "true" && id) {
      window.history.replaceState({}, "", "/");
      addMessage("agent", "✅ Booking approved via email! Completing your booking now...");
      setState("complete");
    } else if (approved === "false") {
      window.history.replaceState({}, "", "/");
      addMessage("agent", "❌ Approval rejected or expired. Please start again.");
      setState("chatting");
    }
  }, []);

  const addMessage = (role, text) => {
    setMessages(prev => [...prev, { role, text }]);
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const text = input.trim();
    setInput("");
    addMessage("user", text);
    setLoading(true);

    try {
      if (state === "selecting") {
        const res  = await fetch(`${API}/select`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: sessionId, choice: text })
        });
        const data = await res.json();
        addMessage("agent", data.reply);
        setState(data.state || "chatting");
        if (data.summary)     setSummary(data.summary);
        if (data.approval_id) setApprovalId(data.approval_id);
        if (data.state === "awaiting_approval") {
          setState("awaiting_approval");
        }
      } else {
        const res  = await fetch(`${API}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: sessionId, message: text })
        });
        const data = await res.json();
        addMessage("agent", data.reply);
        const newState = data.state || "chatting";
        setState(newState);
        if (newState === "selecting") {
          addMessage("agent", "Type 1, 2 or 3 to select your flight.");
        }
      }
    } catch (e) {
      addMessage("agent", "Something went wrong. Please try again.");
    }
    setLoading(false);
  };

  const submitOtp = async () => {
    if (!otp || otp.length !== 6) {
      setOtpError("Please enter the 6-digit OTP from your email.");
      return;
    }
    setOtpError("");
    setLoading(true);
    try {
      const res  = await fetch(`${API}/verify-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, otp })
      });
      const data = await res.json();
      if (data.success) {
        addMessage("agent", data.message);
        setState("complete");
      } else {
        setOtpError(data.message || "Invalid OTP. Please try again.");
      }
    } catch (e) {
      setOtpError("Something went wrong. Please try again.");
    }
    setLoading(false);
  };

  return (
    <div className="app">
      <header className="header">
        <div className="logo">✈ AeroAgent</div>
        <div className="tagline">Your autonomous flight booking assistant</div>
      </header>

      <main className="chat-window">
        {messages.map((m, i) => (
          <div key={i} className={`bubble ${m.role}`}>
            {m.role === "agent" && <div className="avatar">✈</div>}
            <div className="text">{m.text}</div>
          </div>
        ))}

        {loading && (
          <div className="bubble agent">
            <div className="avatar">✈</div>
            <div className="text typing">
              <span /><span /><span />
            </div>
          </div>
        )}

        {summary && state === "awaiting_approval" && (
          <div className="summary-card">
            <div className="summary-title">✈ Booking summary</div>
            <div className="summary-row"><span>Flight</span><span>{summary.airline} {summary.flight_no}</span></div>
            <div className="summary-row"><span>Departs</span><span>{summary.departs}</span></div>
            <div className="summary-row"><span>Arrives</span><span>{summary.arrives}</span></div>
            <div className="summary-row"><span>Seat</span><span>{summary.seat}</span></div>
            <div className="summary-row total"><span>Total</span><span>{summary.total}</span></div>

            <div className="verify-section">
              <div className="verify-title">📧 Check your email</div>
              <div className="verify-sub">
                Click the approval link in your email, or enter the 6-digit OTP below as a fallback.
              </div>
              <div className="otp-row">
                <input
                  className="otp-input"
                  type="text"
                  maxLength={6}
                  placeholder="Enter OTP"
                  value={otp}
                  onChange={e => setOtp(e.target.value.replace(/\D/g, ""))}
                  onKeyDown={e => e.key === "Enter" && submitOtp()}
                />
                <button className="otp-btn" onClick={submitOtp} disabled={loading}>
                  Verify
                </button>
              </div>
              {otpError && <div className="otp-error">{otpError}</div>}
              <div className="approval-note">
                ⏳ Approval expires in 5 minutes
              </div>
            </div>
          </div>
        )}

        {state === "complete" && (
          <div className="complete-card">
            <div className="complete-icon">✅</div>
            <div className="complete-title">Booking Confirmed!</div>
            <div className="complete-sub">Your flight has been booked successfully.</div>
          </div>
        )}

        <div ref={bottomRef} />
      </main>

      <footer className="input-bar">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && sendMessage()}
          placeholder={
            state === "selecting"
              ? "Type 1, 2 or 3..."
              : state === "awaiting_approval"
              ? "Waiting for email approval..."
              : state === "complete"
              ? "Booking complete!"
              : "Type your message..."
          }
          disabled={loading || state === "complete" || state === "awaiting_approval"}
        />
        <button onClick={sendMessage} disabled={loading || state === "complete" || state === "awaiting_approval"}>
          {loading ? "..." : "Send"}
        </button>
      </footer>
    </div>
  );
}