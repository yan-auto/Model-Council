/**
 * API 客户端 —— 与后端通信
 * 统一错误处理，fetch 失败不会白屏
 */
const API_BASE = import.meta.env.VITE_API_BASE || '';

function getToken() {
  return localStorage.getItem('council_token') || 'council-local';
}

export function authHeaders() {
  return { Authorization: `Bearer ${getToken()}` };
}

/** 安全 fetch 包装，网络错误返回 null，10秒超时 */
async function safeFetch(url, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);
  try {
    const res = await fetch(url, { ...options, signal: controller.signal });
    clearTimeout(timeout);
    if (res.status === 401) {
      console.warn('[API] 鉴权失败，请检查 token');
      return null;
    }
    if (!res.ok) {
      const text = await res.text().catch(() => '');
      console.warn(`[API] ${res.status}: ${text}`);
      return null;
    }
    return res;
  } catch (e) {
    clearTimeout(timeout);
    if (e.name === 'AbortError') {
      console.warn('[API] 请求超时');
      return null;
    }
    console.warn('[API] 网络错误:', e.message);
    return null;
  }
}

// ── REST ───────────────────────────────────────────

export async function listConversations(status) {
  const url = status ? `${API_BASE}/api/conversations?status=${status}` : `${API_BASE}/api/conversations`;
  const res = await safeFetch(url, { headers: authHeaders() });
  if (!res) return [];
  return res.json();
}

export async function getConversation(convId) {
  const res = await safeFetch(`${API_BASE}/api/conversations/${convId}`, { headers: authHeaders() });
  if (!res) return {};
  return res.json();
}

export async function createConversation(title) {
  const res = await safeFetch(`${API_BASE}/api/conversations`, {
    method: 'POST',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
  if (!res) return {};
  return res.json();
}

export async function archiveConversation(convId) {
  const res = await safeFetch(`${API_BASE}/api/conversations/${convId}`, {
    method: 'DELETE',
    headers: authHeaders(),
  });
  if (!res) return {};
  return res.json();
}

export async function listAgents() {
  const res = await safeFetch(`${API_BASE}/api/agents`, { headers: authHeaders() });
  if (!res) return { agents: [] };
  return res.json();
}

export async function clearAllConversations() {
  const convs = await listConversations();
  for (const c of convs) {
    await archiveConversation(c.id);
  }
}

// ── SSE via fetch + ReadableStream ──────────────────

/**
 * 流式聊天，POST 请求 + ReadableStream 解析 SSE
 * @returns {{ abort: () => void }}
 */
export async function streamChat(conversationId, content, { imageData, onToken, onDone, onError }) {
  const controller = new AbortController();

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: {
        ...authHeaders(),
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({ conversation_id: conversationId, content, image_data: imageData || null }),
      signal: controller.signal,
    });

    if (!res.ok) {
      const err = await res.text().catch(() => `HTTP ${res.status}`);
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
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('event: ')) continue;
        if (line.startsWith('data: ')) {
          try {
            const event = JSON.parse(line.slice(6));
            if (event.type === 'token' && event.data?.token) {
              onToken(event.data.token, event.agent_name);
            } else if (event.type === 'token' && event.data?.agent_switch) {
              onToken('', event.data.agent_switch);
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

// ── Provider / Model / Agent 管理 ──────────────────

export async function listProviders() {
  const res = await safeFetch(`${API_BASE}/api/providers`, { headers: authHeaders() });
  if (!res) return { providers: [] };
  return res.json();
}

export async function createProvider(data) {
  const res = await safeFetch(`${API_BASE}/api/providers`, {
    method: 'POST',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res) return {};
  return res.json();
}

export async function updateProvider(id, data) {
  const res = await safeFetch(`${API_BASE}/api/providers/${id}`, {
    method: 'PUT',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res) return {};
  return res.json();
}

export async function deleteProvider(id) {
  const res = await safeFetch(`${API_BASE}/api/providers/${id}`, {
    method: 'DELETE',
    headers: authHeaders(),
  });
  if (!res) return {};
  return res.json();
}

export async function validateProvider(id) {
  const res = await safeFetch(`${API_BASE}/api/providers/${id}/validate`, {
    method: 'POST',
    headers: authHeaders(),
  });
  if (!res) return { valid: false };
  return res.json();
}

export async function listAllModels() {
  const res = await safeFetch(`${API_BASE}/api/models`, { headers: authHeaders() });
  if (!res) return { models: [] };
  return res.json();
}

// ── Profile / Memory ──────────────────────────────────

export async function getProfile() {
  const res = await safeFetch(`${API_BASE}/api/profile`, { headers: authHeaders() });
  if (!res) return {};
  return res.json();
}

export async function updateProfile(data) {
  const res = await safeFetch(`${API_BASE}/api/profile`, {
    method: 'PUT',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res) return {};
  return res.json();
}

export async function getActions(status) {
  const url = status ? `${API_BASE}/api/actions?status=${status}` : `${API_BASE}/api/actions`;
  const res = await safeFetch(url, { headers: authHeaders() });
  if (!res) return { actions: [] };
  return res.json();
}

export async function completeAction(id) {
  const res = await safeFetch(`${API_BASE}/api/actions/${id}?status=done`, {
    method: 'PUT',
    headers: authHeaders(),
  });
  if (!res) return {};
  return res.json();
}

export async function skipAction(id) {
  const res = await safeFetch(`${API_BASE}/api/actions/${id}?status=skipped`, {
    method: 'PUT',
    headers: authHeaders(),
  });
  if (!res) return {};
  return res.json();
}

export async function deleteAction(id) {
  const res = await safeFetch(`${API_BASE}/api/actions/${id}`, {
    method: 'DELETE',
    headers: authHeaders(),
  });
  if (!res) return {};
  return res.json();
}

export async function getAgentMemory(agentName) {
  const res = await safeFetch(`${API_BASE}/api/agents/${agentName}/memory`, { headers: authHeaders() });
  if (!res) return { memories: [] };
  return res.json();
}

export async function createAgentAPI(data) {
  const res = await safeFetch(`${API_BASE}/api/agents`, {
    method: 'POST',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res) return {};
  return res.json();
}

export async function updateAgentAPI(id, data) {
  const res = await safeFetch(`${API_BASE}/api/agents/${id}`, {
    method: 'PUT',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res) return {};
  return res.json();
}

export async function deleteAgentAPI(id) {
  const res = await safeFetch(`${API_BASE}/api/agents/${id}`, {
    method: 'DELETE',
    headers: authHeaders(),
  });
  if (!res) return {};
  return res.json();
}

export async function updateAgentModel(agentId, modelId) {
  const res = await safeFetch(`${API_BASE}/api/agents/${agentId}/model`, {
    method: 'PUT',
    headers: { ...authHeaders(), 'Content-Type': 'application/json' },
    body: JSON.stringify({ model_id: modelId }),
  });
  if (!res) return {};
  return res.json();
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
