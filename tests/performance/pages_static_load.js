import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

const baseUrl = __ENV.BASE_URL || 'https://ph-infra-budget-finder.pages.dev';
const profile = __ENV.PROFILE || 'production';
const htmlDuration = new Trend('html_duration', true);
const dataDuration = new Trend('data_duration', true);

const profiles = {
  smoke: [
    { duration: '10s', target: 2 },
    { duration: '20s', target: 5 },
    { duration: '10s', target: 0 },
  ],
  production: [
    { duration: '15s', target: 10 },
    { duration: '30s', target: 25 },
    { duration: '45s', target: 50 },
    { duration: '15s', target: 0 },
  ],
  launch_100: [
    { duration: '8s', target: 50 },
    { duration: '8s', target: 100 },
    { duration: '8s', target: 0 },
  ],
};

export const options = {
  scenarios: {
    static_site: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: profiles[profile] || profiles.production,
      gracefulRampDown: '5s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
    http_req_duration: ['p(95)<2000'],
    html_duration: ['p(95)<1500'],
    data_duration: ['p(95)<2500'],
  },
  discardResponseBodies: true,
};

function request(path, tags) {
  const response = http.get(`${baseUrl}${path}`, { tags });
  check(response, {
    [`${path} returns 200`]: result => result.status === 200,
    [`${path} is not an HTML error page`]: result => !String(result.headers['Content-Type'] || '').includes('text/html') || path === '/',
  });
  return response;
}

export default function () {
  const responses = http.batch([
    ['GET', `${baseUrl}/`, null, { tags: { asset: 'html' } }],
    ['GET', `${baseUrl}/style.css`, null, { tags: { asset: 'css' } }],
    ['GET', `${baseUrl}/app.js`, null, { tags: { asset: 'js' } }],
    ['GET', `${baseUrl}/data/search-index.json`, null, { tags: { asset: 'data' } }],
    ['GET', `${baseUrl}/data/factuality_report.json`, null, { tags: { asset: 'report' } }],
  ]);
  const [html, css, js, data, report] = responses;
  htmlDuration.add(html.timings.duration);
  dataDuration.add(data.timings.duration);
  check(html, { 'home page returns 200': result => result.status === 200 });
  check(css, { 'stylesheet returns 200': result => result.status === 200 });
  check(js, { 'application script returns 200': result => result.status === 200 });
  check(data, { 'project data returns 200': result => result.status === 200 });
  check(report, { 'factuality report returns 200': result => result.status === 200 });
  sleep(3);
}

