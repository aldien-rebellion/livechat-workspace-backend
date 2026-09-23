import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 20 }, // Ramp-up to 20 users
    { duration: '1m', target: 50 },  // Ramp-up to 50 users
    { duration: '30s', target: 100 }, // Peak 100 users
    { duration: '30s', target: 0 },   // Ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<300', 'p(99)<500'], // 95% of requests must complete below 300ms
    http_req_failed: ['rate<0.01'],                 // Less than 1% failed requests
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export function setup() {
  // Create test user and obtain JWT token for load testing
  const uniqueId = Math.random().toString(36).substring(2, 8);
  const username = `k6_user_${uniqueId}`;
  const password = 'Password123!';
  const email = `${username}@example.com`;

  // 1. Register
  const regRes = http.post(
    `${BASE_URL}/api/v1/auth/register`,
    JSON.stringify({ username, email, password }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  // 2. Login
  const loginRes = http.post(
    `${BASE_URL}/api/v1/auth/login`,
    JSON.stringify({ username, password }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  const token = loginRes.json('access_token');

  // 3. Create workspace
  const wsRes = http.post(
    `${BASE_URL}/api/v1/workspaces`,
    JSON.stringify({ name: `K6 Workspace ${uniqueId}` }),
    {
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    }
  );

  const workspaceId = wsRes.json('id');

  // 4. Get channel
  const chRes = http.get(
    `${BASE_URL}/api/v1/workspaces/${workspaceId}/channels`,
    { headers: { Authorization: `Bearer ${token}` } }
  );

  const channelId = chRes.json('0.id');

  return { token, workspaceId, channelId };
}

export default function (data) {
  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${data.token}`,
  };

  // 1. List user workspaces
  const listWs = http.get(`${BASE_URL}/api/v1/workspaces`, { headers });
  check(listWs, {
    'workspaces status 200': (r) => r.status === 200,
    'workspaces list not empty': (r) => r.json().length > 0,
  });

  // 2. List channels in workspace
  if (data.workspaceId) {
    const listCh = http.get(
      `${BASE_URL}/api/v1/workspaces/${data.workspaceId}/channels`,
      { headers }
    );
    check(listCh, {
      'channels status 200': (r) => r.status === 200,
    });
  }

  // 3. Get message history of channel
  if (data.channelId) {
    const listMsg = http.get(
      `${BASE_URL}/api/v1/channels/${data.channelId}/messages?limit=20`,
      { headers }
    );
    check(listMsg, {
      'messages status 200': (r) => r.status === 200,
    });
  }

  sleep(1);
}
