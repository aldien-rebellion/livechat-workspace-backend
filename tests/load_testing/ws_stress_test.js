import ws from 'k6/ws';
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '20s', target: 20 }, // Ramp-up to 20 sockets
    { duration: '40s', target: 50 }, // Ramp-up to 50 concurrent sockets
    { duration: '30s', target: 50 }, // Sustained load
    { duration: '10s', target: 0 },  // Ramp-down
  ],
  thresholds: {
    ws_session_duration: ['min>1000'],
    checks: ['rate>0.98'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const WS_BASE_URL = __ENV.WS_BASE_URL || 'ws://localhost:8000';

export function setup() {
  const uniqueId = Math.random().toString(36).substring(2, 8);
  const username = `k6_ws_${uniqueId}`;
  const password = 'Password123!';
  const email = `${username}@example.com`;

  // 1. Register
  http.post(
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

  // 3. Workspace & Channel
  const wsRes = http.post(
    `${BASE_URL}/api/v1/workspaces`,
    JSON.stringify({ name: `K6 WS Space ${uniqueId}` }),
    {
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    }
  );
  const workspaceId = wsRes.json('id');

  const chRes = http.get(
    `${BASE_URL}/api/v1/workspaces/${workspaceId}/channels`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  const channelId = chRes.json('0.id');

  return { token, channelId };
}

export default function (data) {
  const url = `${WS_BASE_URL}/api/v1/ws/channels/${data.channelId}?token=${data.token}`;

  const res = ws.connect(url, {}, function (socket) {
    socket.on('open', function () {
      // 1. Send initial presence ping
      socket.send(JSON.stringify({ event: 'presence:ping' }));

      // 2. Periodically send messages (burst simulation)
      socket.setInterval(function () {
        socket.send(
          JSON.stringify({
            event: 'message:send',
            data: {
              content: `Stress test message from VU ${__VU} at ${new Date().toISOString()}`,
            },
          })
        );
      }, 1000); // 1 msg per sec per VU -> 50 msgs/sec at 50 VUs

      // 3. Heartbeat ping every 15s
      socket.setInterval(function () {
        socket.send(JSON.stringify({ event: 'presence:ping' }));
      }, 15000);
    });

    socket.on('message', function (msg) {
      const packet = JSON.parse(msg);
      check(packet, {
        'valid event received': (p) =>
          ['presence:pong', 'message:ack', 'message:broadcast', 'typing:start', 'presence:update'].includes(
            p.event
          ),
      });
    });

    socket.on('error', function (e) {
      console.error(`Socket error: ${e.error()}`);
    });

    // Run connection for 25s
    socket.setTimeout(function () {
      socket.close();
    }, 25000);
  });

  check(res, { 'ws connected successfully': (r) => r && r.status === 101 });
  sleep(1);
}
