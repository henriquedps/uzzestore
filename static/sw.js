// Service Worker para UzzeStore PWA
const CACHE_NAME = 'uzzerstore-v1.0.0';
const CACHE_VERSION = '1.0.0';

// Recursos para cache offline
const urlsToCache = [
  '/mobile',
  '/static/manifest.json',
  '/static/css/admin.css',
  '/static/css/cadastro.css',
  '/static/css/cart.css',
  '/static/css/forms.css',
  '/static/css/login.css',
  '/static/css/product.css',
  '/static/css/products.css',
  '/static/js/img-fallback.js',
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;500;600;700&display=swap',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css'
];

// Recursos críticos que sempre devem estar disponíveis
const criticalResources = [
  '/mobile',
  '/static/js/img-fallback.js'
];

// Install Event - Cache recursos
self.addEventListener('install', (event) => {
  console.log('[SW] Install event');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Caching app shell');
        return cache.addAll(urlsToCache);
      })
      .then(() => {
        console.log('[SW] Cache complete');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[SW] Cache failed:', error);
      })
  );
});

// Activate Event - Limpar caches antigos
self.addEventListener('activate', (event) => {
  console.log('[SW] Activate event');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('[SW] Claiming clients');
      return self.clients.claim();
    })
  );
});

// Fetch Event - Estratégia de cache
self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);
  
  // Ignore non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Ignore chrome-extension requests
  if (url.protocol === 'chrome-extension:') {
    return;
  }
  
  // Handle different types of requests
  if (url.pathname.startsWith('/api/')) {
    // API requests - Network first, cache fallback
    event.respondWith(networkFirstStrategy(request));
  } else if (url.pathname.startsWith('/static/')) {
    // Static resources - Cache first, network fallback
    event.respondWith(cacheFirstStrategy(request));
  } else if (url.pathname.startsWith('/carrinho/') || url.pathname.startsWith('/admin/')) {
    // Dynamic content - Network only
    event.respondWith(networkOnlyStrategy(request));
  } else {
    // Pages - Stale while revalidate
    event.respondWith(staleWhileRevalidateStrategy(request));
  }
});

// Cache First Strategy - Para recursos estáticos
async function cacheFirstStrategy(request) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.error('[SW] Cache first failed:', error);
    return getOfflineFallback(request);
  }
}

// Network First Strategy - Para dados dinâmicos
async function networkFirstStrategy(request) {
  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    return getOfflineFallback(request);
  }
}

// Network Only Strategy - Para conteúdo que não deve ser cacheado
async function networkOnlyStrategy(request) {
  try {
    return await fetch(request);
  } catch (error) {
    return getOfflineFallback(request);
  }
}

// Stale While Revalidate Strategy - Para páginas
async function staleWhileRevalidateStrategy(request) {
  const cache = await caches.open(CACHE_NAME);
  const cachedResponse = await cache.match(request);
  
  const fetchPromise = fetch(request).then((networkResponse) => {
    if (networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  }).catch(() => cachedResponse);
  
  return cachedResponse || fetchPromise;
}

// Fallback para quando offline
function getOfflineFallback(request) {
  const url = new URL(request.url);
  
  if (request.destination === 'document') {
    // Página offline
    return caches.match('/mobile') || new Response(`
      <!DOCTYPE html>
      <html lang="pt-BR">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>UzzeStore - Offline</title>
        <style>
          body { 
            font-family: -apple-system, BlinkMacSystemFont, sans-serif; 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            justify-content: center; 
            min-height: 100vh; 
            margin: 0; 
            background: #f8f9fa; 
            color: #333; 
            text-align: center; 
            padding: 20px;
          }
          .offline-icon { 
            font-size: 4rem; 
            margin-bottom: 1rem; 
            color: #6c757d; 
          }
          h1 { 
            font-size: 1.5rem; 
            margin-bottom: 0.5rem; 
            color: #000; 
          }
          p { 
            color: #6c757d; 
            margin-bottom: 2rem; 
            max-width: 300px; 
          }
          button { 
            background: #000; 
            color: white; 
            border: none; 
            padding: 12px 24px; 
            border-radius: 6px; 
            cursor: pointer; 
            font-size: 1rem;
          }
          button:hover { 
            background: #333; 
          }
        </style>
      </head>
      <body>
        <div class="offline-icon">📱</div>
        <h1>Você está offline</h1>
        <p>Verifique sua conexão com a internet e tente novamente</p>
        <button onclick="location.reload()">Tentar novamente</button>
        
        <script>
          // Auto retry when online
          window.addEventListener('online', () => {
            location.reload();
          });
        </script>
      </body>
      </html>
    `, {
      headers: { 'Content-Type': 'text/html' }
    });
  }
  
  if (request.destination === 'image') {
    // Imagem offline placeholder
    return new Response(`
      <svg width="400" height="400" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#f8f9fa"/>
        <text x="50%" y="45%" text-anchor="middle" font-family="Arial" font-size="16" fill="#6c757d">📷</text>
        <text x="50%" y="60%" text-anchor="middle" font-family="Arial" font-size="14" fill="#6c757d">Imagem indisponível</text>
      </svg>
    `, {
      headers: { 'Content-Type': 'image/svg+xml' }
    });
  }
  
  // Response genérica de erro
  return new Response('Conteúdo indisponível offline', {
    status: 503,
    statusText: 'Service Unavailable',
    headers: { 'Content-Type': 'text/plain' }
  });
}

// Background Sync para ações offline
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync:', event.tag);
  
  if (event.tag === 'cart-sync') {
    event.waitUntil(syncCart());
  }
  
  if (event.tag === 'favorites-sync') {
    event.waitUntil(syncFavorites());
  }
});

// Sync carrinho quando voltar online
async function syncCart() {
  try {
    // Implementar sincronização do carrinho
    console.log('[SW] Syncing cart...');
  } catch (error) {
    console.error('[SW] Cart sync failed:', error);
  }
}

// Sync favoritos quando voltar online
async function syncFavorites() {
  try {
    // Implementar sincronização dos favoritos
    console.log('[SW] Syncing favorites...');
  } catch (error) {
    console.error('[SW] Favorites sync failed:', error);
  }
}

// Push Notifications
self.addEventListener('push', (event) => {
  console.log('[SW] Push received');
  
  const options = {
    body: event.data ? event.data.text() : 'Nova atualização disponível!',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/badge-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: '1'
    },
    actions: [
      {
        action: 'explore',
        title: 'Ver agora',
        icon: '/static/icons/action-explore.png'
      },
      {
        action: 'close',
        title: 'Fechar',
        icon: '/static/icons/action-close.png'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('UzzeStore', options)
  );
});

// Notification Click
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification click received');
  
  event.notification.close();
  
  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/mobile')
    );
  }
});

// Message handling para comunicação com o app
self.addEventListener('message', (event) => {
  console.log('[SW] Message received:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'GET_VERSION') {
    event.ports[0].postMessage({ version: CACHE_VERSION });
  }
  
  if (event.data && event.data.type === 'CACHE_URLS') {
    event.waitUntil(
      caches.open(CACHE_NAME).then((cache) => {
        return cache.addAll(event.data.payload);
      })
    );
  }
});

// Cleanup old caches periodically
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((cacheName) => {
            return cacheName.startsWith('uzzerstore-') && cacheName !== CACHE_NAME;
          })
          .map((cacheName) => {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          })
      );
    })
  );
});

console.log('[SW] Service Worker registered successfully!');