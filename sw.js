/* Poker Trainer service worker.

   The version is read from the ?v= on the registration URL, so BUILD in
   index.html is the only thing that has to change to ship an update: a new
   BUILD means a new script URL, which means the browser installs a new
   worker, drops the old cache and reloads the open page. */

const VERSION = new URL(self.location).searchParams.get('v') || 'dev';
const CACHE = 'poker-trainer-' + VERSION;
const PAGE = './index.html';
const RANGES = './ranges.json';
const SHELL = ['./', PAGE, RANGES, './manifest.webmanifest', './icon-192.png'];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      // cache:'reload' stops the HTTP cache seeding the new version with the
      // copy it is already holding.
      .then(c => c.addAll(SHELL.map(u => new Request(u, {cache: 'reload'}))))
      .catch(() => {})
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('message', e => {
  if(e.data === 'skip-waiting') self.skipWaiting();
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if(req.method !== 'GET') return;
  const url = new URL(req.url);
  if(url.origin !== self.location.origin) return;

  const isPage = req.mode === 'navigate' ||
                 (req.headers.get('accept') || '').includes('text/html');
  const isRanges = url.pathname.endsWith('/ranges.json');

  if(isPage || isRanges){
    // The page and the range charts always come from the network, bypassing
    // the HTTP cache, so a deploy (or an edited chart) is never hidden behind
    // the max-age GitHub Pages puts on them. The cached copy is only there for
    // being offline.
    const key = isPage ? PAGE : RANGES;
    e.respondWith(
      fetch(new Request(req.url, {cache: 'no-store'}))
        .then(resp => {
          if(resp && resp.ok){
            const copy = resp.clone();
            caches.open(CACHE).then(c => c.put(key, copy)).catch(() => {});
          }
          return resp;
        })
        .catch(() => caches.match(key, {ignoreSearch: true})
          .then(hit => hit || caches.match(req, {ignoreSearch: true})))
    );
    return;
  }

  // Everything else is versioned with the cache, so serve it fast and
  // refresh it in the background.
  e.respondWith(
    caches.match(req, {ignoreSearch: true}).then(hit => {
      const net = fetch(req).then(resp => {
        if(resp && resp.ok && resp.type === 'basic'){
          const copy = resp.clone();
          caches.open(CACHE).then(c => c.put(req, copy)).catch(() => {});
        }
        return resp;
      }).catch(() => hit);
      return hit || net;
    })
  );
});
