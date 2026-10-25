// HA Notify service.
// Shows native TV notification banners (title + text) and accepts notifications over HTTP on the LAN.
//   GET  /health                           -> {ok: true}
//   POST /notify {title, message, timeout} -> webapis.postPlainNotification
// Images are not supported: the TV's notification APIs available to third-party apps only render text.
var http = require('http');

var PORT = 8099;
var server = null;

function log(msg) {
  console.log('[HANotify] ' + msg);
}

function notify(title, message, timeout) {
  try {
    webapis.postPlainNotification(String(title), String(message), Number(timeout) || 10);
    return null;
  } catch (e) {
    log('postPlainNotification failed: ' + e);
    return String(e);
  }
}

function readJson(req, cb) {
  var body = '';
  req.on('data', function (c) { body += c; if (body.length > 65536) req.destroy(); });
  req.on('end', function () {
    try { cb(null, JSON.parse(body || '{}')); } catch (e) { cb('bad json'); }
  });
}

function reply(res, code, obj) {
  res.writeHead(code, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(obj));
}

function startServer() {
  if (server) return;
  server = http.createServer(function (req, res) {
    if (req.method === 'GET' && req.url === '/health') {
      reply(res, 200, { ok: true });
      return;
    }
    if (req.method === 'POST' && req.url === '/notify') {
      readJson(req, function (err, data) {
        if (err) { reply(res, 400, { ok: false, error: err }); return; }
        var e = notify(data.title || 'Home Assistant', data.message || '', data.timeout);
        reply(res, e ? 500 : 200, { ok: !e, error: e });
      });
      return;
    }
    res.writeHead(404); res.end();
  });
  server.on('error', function (e) { log('server error: ' + e); });
  server.listen(PORT, '0.0.0.0', function () { log('listening on ' + PORT); });
}

module.exports.onStart = function () {
  log('onStart');
  startServer();
};

module.exports.onRequest = function () {
  log('onRequest');
  startServer();
};

module.exports.onStop = function () {
  log('onStop');
  if (server) { server.close(); server = null; }
};
