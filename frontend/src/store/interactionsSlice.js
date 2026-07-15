import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../api/api';

// One session_id per browser tab/session -- lets the backend know which
// draft interaction "actually the name was Dr. John" should apply to.
const SESSION_ID = crypto.randomUUID();

export const sendChatMessage = createAsyncThunk(
  'interactions/sendChatMessage',
  async ({ message }) => {
    const res = await api.post('/api/chat', { session_id: SESSION_ID, message });
    return res.data;
  }
);

const emptyForm = {
  hcp_name: null,
  interaction_type: null,
  date: null,
  time: null,
  attendees: [],
  topics_discussed: null,
  materials_shared: [],
  samples_distributed: [],
  sentiment: null,
  outcomes: null,
  follow_up_actions: null,
  ai_suggested_followups: [],
};

const interactionsSlice = createSlice({
  name: 'interactions',
  initialState: {
    chatLog: [],
    lastToolCalls: [],
    formState: emptyForm,
    status: 'idle',
    error: null,
  },
  reducers: {
    pushUserMessage(state, action) {
      state.chatLog.push({ role: 'user', text: action.payload });
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendChatMessage.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.chatLog.push({ role: 'agent', text: action.payload.reply });
        state.lastToolCalls = action.payload.tool_calls || [];
        if (action.payload.form_state) {
          state.formState = { ...emptyForm, ...action.payload.form_state };
        }
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message;
      });
  },
});

export const { pushUserMessage } = interactionsSlice.actions;
export default interactionsSlice.reducer;
