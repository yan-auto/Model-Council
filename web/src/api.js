/**
 * API 客户端 —— 与后端通信
 */
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

function getToken() {
  return localStorage.getItem('council_token') || 'council-local';
}

function authHeaders() {
  return { Authorization: `Bearer ${getToken()}` };
}

// ── REST ───────────────────────────────────────────

export async function listConversations() {
  const res = await fetch(`${API_BASE}/api/conversations`, { headers: authHeaders() });
  return res.json();
}

export async function getConversation(convId) {
  const res = await fetch(`${API_BASE}/api/conversations/${convId}`, { headers: authHeaders() });
  return res.json();
}

export async function createConversation(title) {
  const res = await fetch(`${API_BASE}/api/conversations`, {
    method: 'POST',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
  return res.json();
}

export async function listAgents() {
  const res = await fetch(`${API_BASE}/api/agents`, { headers: authHeaders() });
  return res.json();
}

// ── SSE via fetch + ReadableStream ──────────────────

/**
 * 流式聊天，POST 请求 + ReadableStream 解析 SSE
 * @returns {{ abort: () => void }}
 */
export async function streamChat(conversationId, content, { onToken, onDone, onError }) {
  const controller = new AbortController();

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: {
        ...authHeaders(),
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({ conversation_id: conversationId, content }),
      signal: controller.signal,
    });

    if (!res.ok) {
      const err = await res.text();
      onError(new Error(err));
      return { abort: () => {} };
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // 最后不完整的行保留

      for (const line of lines) {
        if (line.startsWith('event: ')) continue; // 跳过 event 类型行
        if (line.startsWith('data: ')) {
          try {
            const event = JSON.parse(line.slice(6));
            if (event.type === 'token' && event.data?.token) {
              onToken(event.data.token);
            } else if (event.type === 'message_done') {
              onDone(event.data?.content || '');
            } else if (event.type === 'error') {
              onError(new Error(event.data?.error || '未知错误'));
            }
          } catch {
            // 非 JSON，跳过
          }
        }
      }
    }
  } catch (e) {
    if (e.name !== 'AbortError') {
      onError(e);
    }
  }

  return { abort: () => controller.abort() };
}

// ── WebSocket 讨论 ─────────────────────────────────

/**
 * 发起 WebSocket 讨论
 * config = { topic, agents, max_rounds, conversation_id }
 * @returns {WebSocket}
 */
export function createDiscussion(config, onEvent, onClose) {
  const token = getToken();
  const proto = API_BASE.startsWith('https') ? 'wss' : 'ws';
  const host = API_BASE.replace(/^https?:\/\//, '');
  const wsUrl = `${proto}://${host}/ws/discuss?token=${encodeURIComponent(token)}`;

  const ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    ws.send(JSON.stringify(config));
  };

  ws.onmessage = (e) => {
    try {
      onEvent(JSON.parse(e.data));
    } catch {
      // 非 JSON，忽略
    }
  };

  ws.onclose = () => {
    onClose && onClose();
  };

  ws.onerror = () => {
    onEvent({ type: 'error', data: { error: 'WebSocket 连接失败' } });
  };

  return ws;
}
