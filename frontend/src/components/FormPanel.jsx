import React from 'react';
import { useSelector } from 'react-redux';

// Every field here is a plain, disabled display -- the rep cannot type into
// any of them. Only the AI Assistant (ChatInterface) can change these values,
// via the log_interaction / edit_interaction tools.
export default function FormPanel() {
  const form = useSelector((s) => s.interactions.formState);

  const sentimentOptions = ['positive', 'neutral', 'negative'];

  return (
    <div style={styles.panel}>
      <h2 style={styles.heading}>Log HCP Interaction</h2>
      <p style={styles.hint}>Fields are filled and edited by the AI Assistant only →</p>

      <div style={styles.row}>
        <Field label="HCP Name" value={form.hcp_name} />
        <Field label="Interaction Type" value={form.interaction_type} />
      </div>
      <div style={styles.row}>
        <Field label="Date" value={form.date} />
        <Field label="Time" value={form.time} />
      </div>

      <label style={styles.label}>Attendees</label>
      <div style={styles.displayBox}>
        {form.attendees.length ? form.attendees.join(', ') : <Placeholder text="No attendees added" />}
      </div>

      <label style={styles.label}>Topics Discussed</label>
      <div style={{ ...styles.displayBox, minHeight: 60 }}>
        {form.topics_discussed || <Placeholder text="Enter key discussion points…" />}
      </div>

      <label style={styles.label}>Materials Shared</label>
      <div style={styles.displayBox}>
        {form.materials_shared.length ? form.materials_shared.join(', ') : <Placeholder text="No materials added" />}
      </div>

      <label style={styles.label}>Samples Distributed</label>
      <div style={styles.displayBox}>
        {form.samples_distributed.length
          ? form.samples_distributed.map((s, i) => (
              <div key={i}>{s.product} × {s.qty}</div>
            ))
          : <Placeholder text="No samples added" />}
      </div>

      <label style={styles.label}>Observed / Inferred HCP Sentiment</label>
      <div style={styles.sentimentRow}>
        {sentimentOptions.map((opt) => (
          <div key={opt} style={form.sentiment === opt ? styles.sentimentActive : styles.sentimentInactive}>
            <span style={styles.radioDot(form.sentiment === opt)} />
            {opt[0].toUpperCase() + opt.slice(1)}
          </div>
        ))}
      </div>

      <label style={styles.label}>Outcomes</label>
      <div style={{ ...styles.displayBox, minHeight: 50 }}>
        {form.outcomes || <Placeholder text="Key outcomes or agreements…" />}
      </div>

      <label style={styles.label}>Follow-up Actions</label>
      <div style={{ ...styles.displayBox, minHeight: 50 }}>
        {form.follow_up_actions || <Placeholder text="Enter next steps or tasks…" />}
      </div>

      {form.ai_suggested_followups.length > 0 && (
        <div style={styles.suggestBox}>
          <strong style={{ fontSize: 13 }}>AI Suggested Follow-ups:</strong>
          <ul style={{ margin: '6px 0 0 0', paddingLeft: 18 }}>
            {form.ai_suggested_followups.map((s, i) => (
              <li key={i} style={{ fontSize: 13, color: '#4f46e5' }}>{s}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function Field({ label, value }) {
  return (
    <div style={{ flex: 1 }}>
      <label style={styles.label}>{label}</label>
      <div style={styles.displayBox}>{value || <Placeholder text="—" />}</div>
    </div>
  );
}

function Placeholder({ text }) {
  return <span style={{ color: '#9ca3af' }}>{text}</span>;
}

const styles = {
  panel: { flex: 1, background: '#fff', borderRadius: 16, padding: 24, fontFamily: 'Inter, sans-serif' },
  heading: { margin: 0, fontSize: 20, fontWeight: 700 },
  hint: { color: '#6b7280', fontSize: 12, marginTop: 4, marginBottom: 16 },
  row: { display: 'flex', gap: 12 },
  label: { display: 'block', fontSize: 12, fontWeight: 600, color: '#374151', marginTop: 12, marginBottom: 4 },
  displayBox: {
    padding: '8px 10px', borderRadius: 6, border: '1px solid #e5e7eb',
    background: '#f9fafb', fontSize: 14, color: '#111827', minHeight: 20,
  },
  sentimentRow: { display: 'flex', gap: 16, marginTop: 4 },
  sentimentActive: { display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 600, color: '#111827' },
  sentimentInactive: { display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: '#9ca3af' },
  radioDot: (active) => ({
    width: 12, height: 12, borderRadius: '50%',
    border: `2px solid ${active ? '#4f46e5' : '#d1d5db'}`,
    background: active ? '#4f46e5' : 'transparent', display: 'inline-block',
  }),
  suggestBox: { marginTop: 16, padding: 12, background: '#eef2ff', borderRadius: 8 },
};
