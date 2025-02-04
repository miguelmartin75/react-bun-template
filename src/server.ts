import {
  type Serve,
  serve,
  type ServerWebSocket,
  type WebSocketServeOptions,
} from 'bun'
import { Database } from "bun:sqlite";
import { watch } from 'fs'

import homepage from './index.html'

const liveReload = createLiveReload()
const db = new Database("dataset.sqlite3");
db.exec("PRAGMA journal_mode = WAL;");  // WAL mode, see: https://bun.sh/docs/api/sqlite#wal-mode

const serveOptions: Serve = {
  port: 8080,
  static: {
    '/': homepage,
  },
  development: true,
  fetch: (req: Request): Promise<Response> | Response => {
    // TODO: checkme
    if (server.upgrade(req)) {
      // @ts-expect-error
      return
    }

    const { url } = req;
    const { pathname } = new URL(url);

    if (pathname === "/samples") {
      using query = db.query("SELECT * FROM Sample;");
      var samples = query.all();
      return Response.json(samples);
    }

    return new Response("404", { status: 404 });
  },
  websocket: liveReload.ws,
}

const server = serve(serveOptions)

const watcherLog = console.log.bind('[watcher]')
watch(import.meta.dir, { recursive: true }, async (event, filename) => {
  watcherLog(`Detected ${event} in ${filename}`)
  if (filename?.endsWith('.tsx') || filename?.endsWith('.ts')) {
    watcherLog(`-> Reload`)
    try {
      server.reload({
        ...serveOptions,
        static: {
          // outputs an error but it works
          '/': await import('./index.html'),
        },
      })
    } catch (error) {
      if (!`${error}`.includes(`'static' expects a`)) {
        console.error(error)
      }
    }
    liveReload.reload()
  }
})

console.log(`Server is running at http://${server.hostname}:${server.port}`)

function createLiveReload() {
  const wsClients = new Set<ServerWebSocket>()
  return {
    ws: {
      open(ws) {
        wsClients.add(ws)
      },
      message() {},
      close(ws) {
        wsClients.delete(ws)
      },
    } satisfies WebSocketServeOptions['websocket'],
    reload: () => {
      wsClients.forEach((client) => client.send('RELOAD'))
    },
  }
}

