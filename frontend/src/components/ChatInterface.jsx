import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { sendChatMessage, pushUserMessage } from '../store/interactionsSlice';

export default function ChatInterface() {
  const dispatch = useDispatch();
  const { chatLog, lastToolCalls, status } = useSelector((s) => s.interactions);
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (!input.trim()) return;
    dispatch(pushUserMessage(input));
    dispatch(sendChatMessage({ message: input }));
    setInput('');
  };

  return (
    <div style={styles.panel}>
      <h2 style={styles.heading}>🤖 AI Assistant</h2>
      <p style={styles.hint}>Log interaction details here via chat</p>

      <div style={styles.chatWindow}>
        {chatLog.length === 0 && (
          <div style={styles.agentBubble}>
            Log interaction details here (e.g., "Met Dr. Smith, discussed product X efficacy,
            positive sentiment, shared brochures") or ask for help.
          </div>
        )}
        {chatLog.map((m, i) => (
          <div key={i} style={m.role === 'user' ? styles.userBubble : styles.agentBubble}>
            {m.text}
          </div>
        ))}
        {status === 'loading' && <div style={styles.agentBubble}>Agent is thinking…</div>}
      </div>

      <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
        <input
          style={styles.chatInput}
          placeholder="Describe interaction…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
        />
        <button style={styles.sendBtn} onClick={handleSend}>Log</button>
      </div>

      {lastToolCalls.length > 0 && (
        <div style={styles.toolTrace}>
          <strong>Tool calls this turn:</strong>
          <ul>
            {lastToolCalls.map((t, i) => (
              <li key={i}><code>{t.tool}</code>: {t.result}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

const styles = {
  panel: { flex: 1, background: '#fff', borderRadius: 16, padding: 24, fontFamily: 'Inter, sans-serif', display: 'flex', flexDirection: 'column' },
  heading: { margin: 0, fontSize: 18, fontWeight: 700, color: '#4f46e5' },
  hint: { color: '#6b7280', fontSize: 12, marginTop: 4, marginBottom: 16 },
  chatWindow: { flex: 1, minHeight: 260, maxHeight: 380, overflowY: 'auto', display: 'flex', flexDirection: 'column' },
  userBubble: { alignSelf: 'flex-end', background: '#4f46e5', color: '#fff', padding: '8px 12px', borderRadius: 12, marginBottom: 8, maxWidth: '85%' },
  agentBubble: { background: '#f3f4f6', color: '#111', padding: '10px 12px', borderRadius: 12, marginBottom: 8, maxWidth: '90%', fontSize: 14 },
  chatInput: { flex: 1, padding: 10, borderRadius: 8, border: '1px solid #ccc', fontFamily: 'Inter, sans-serif' },
  sendBtn: { padding: '10px 16px', borderRadius: 8, border: 'none', background: '#4f46e5', color: '#fff', fontWeight: 600, cursor: 'pointer' },
  toolTrace: { marginTop: 12, fontSize: 12, background: '#fffbe6', border: '1px solid #fde68a', borderRadius: 8, padding: 10, maxHeight: 140, overflowY: 'auto' },
};
