// Service Worker - LIMPEZA COMPLETA DE CACHE
console.log('[SW] Iniciando limpeza completa de cache...');

// Install Event - Limpar todos os caches
self.addEventListener('install', (event) => {
  console.log('[SW] Install - Limpando caches...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          console.log('[SW] Deletando cache:', cacheName);
          return caches.delete(cacheName);
        })
      );
    }).then(() => {
      console.log('[SW] Todos os caches limpos!');
      return self.skipWaiting();
    })
  );
});

// Activate Event - Forçar atualização
self.addEventListener('activate', (event) => {
  // console.log('[SW] Activate - Finalizando limpeza...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
         // console.log('[SW] Removendo cache restante:', cacheName);
          return caches.delete(cacheName);
        })
      );
    }).then(() => {
     // console.log('[SW] Cache completamente limpo!');
      return self.clients.claim();
    })
  );
});

// Fetch Event - SEM CACHE (bypass completo)
self.addEventListener('fetch', (event) => {
  // Passa todas as requisições direto para a rede
  // SEM qualquer tipo de cache
  // console.log('[SW] Fetch sem cache:', event.request.url);
  return;
});
 
// console.log('[SW] Service Worker de limpeza ativo!'); 