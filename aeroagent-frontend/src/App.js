import { useState, useRef, useEffect } from "react";
import "./App.css";

const API = "https://aeroagent-api.salmonsand-ae41dd1f.eastus.azurecontainerapps.io";

function generateSessionId() {
  return Math.random().toString(36).substring(2, 15);
}

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: "agent",
      text: "Hi! I'm AeroAgent. Tell me where you want to fly — for example: 'Find me the cheapest flight from New York to London on August 15th 2026'",
    },
  ]);
  const [input, setInput]       = useState("");
  const [loading, setLoading]   = useState(false);
  const [state, setState]       = useState("chatting");
  const [sessionId]             = useState(generateSessionId);
  const [summary, setSummary]   = useState(null);
  const bottomRef               = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const addMessage = (role, text) => {
    setMessages((prev) => [...prev, { role, text }]);
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const text = input.trim();
    setInput("");
    addMessage("user", text);
    setLoading(true);

    try {
      if (state === "selecting") {
        const res = await fetch(`${API}/select`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: sessionId, choice: text }),
        });
        const data = await res.json();
        addMessage("agent", data.reply);
        setState(data.state || "chatting");
        if (data.summary) setSummary(data.summary);
        if (data.state === "awaiting_approval") {
  	setTimeout(() => pollApproval(), 6000);
		}
      } else {
        const res = await fetch(`${API}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: sessionId, message: text }),
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

  const pollApproval = async () => {
    const interval = setInterval(async () => {
      try {
        const res  = await fetch(`${API}/approval-status?session_id=${sessionId}`);
        const data = await res.json();
        if (data.status === "complete") {
          clearInterval(interval);
          const bookRes  = await fetch(`${API}/booking?session_id=${sessionId}`);
          const bookData = await bookRes.json();
          addMessage("agent", `Booking confirmed!\nPNR: ${bookData.pnr}`);
          setState("complete");
        } else if (data.status === "expired") {
          clearInterval(interval);
          addMessage("agent", "Approval timed out. Booking cancelled.");
          setState("chatting");
        }
      } catch (e) {}
    }, 3000);
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
            <div className="summary-title">Booking summary — awaiting your approval</div>
            <div className="summary-row"><span>Flight</span><span>{summary.airline} {summary.flight_no}</span></div>
            <div className="summary-row"><span>Departs</span><span>{summary.departs}</span></div>
            <div className="summary-row"><span>Arrives</span><span>{summary.arrives}</span></div>
            <div className="summary-row"><span>Seat</span><span>{summary.seat}</span></div>
            <div className="summary-row total"><span>Total</span><span>{summary.total}</span></div>
            <div className="approval-note">
              ⏳ Waiting for approval — auto-approves in demo mode
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </main>

      <footer className="input-bar">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder={
            state === "selecting"
              ? "Type 1, 2 or 3 to select..."
              : "Type your message..."
          }
          disabled={loading || state === "complete"}
        />
        <button onClick={sendMessage} disabled={loading || state === "complete"}>
          {loading ? "..." : "Send"}
        </button>
      </footer>
    </div>
  );
}