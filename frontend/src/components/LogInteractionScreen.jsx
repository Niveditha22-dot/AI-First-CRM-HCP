import React from 'react';
import FormPanel from './FormPanel';
import ChatInterface from './ChatInterface';

// Split-screen layout matching the assignment's instructional video:
// left = read-only form (AI-populated only), right = AI Assistant chat.
export default function LogInteractionScreen() {
  return (
    <div style={styles.page}>
      <div style={styles.splitContainer}>
        <FormPanel />
        <ChatInterface />
      </div>
    </div>
  );
}

const styles = {
  page: { minHeight: '100vh', display: 'flex', justifyContent: 'center', alignItems: 'flex-start', paddingTop: 40, paddingBottom: 40 },
  splitContainer: { display: 'flex', gap: 20, width: '90%', maxWidth: 1100 },
};
