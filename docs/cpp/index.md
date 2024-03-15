# PyTVPaint's C++ plugin

To communicate with TVPaint, we developed a TVPaint plugin using C++ and their SDK.

It's a [JSON-RPC](https://www.jsonrpc.org/) over [WebSocket](https://en.wikipedia.org/wiki/WebSocket) server that offers an endpoint to send George commands.

By default it listens on port `3000` but you can set the `TVP_WS_PORT` environment variable to set another port at startup.

Here is an example of JSON messages and responses:

```
--> {"jsonrpc": "2.0", "method": "execute_george", "params": ["tv_version"], "id": 0}
<-- {'id': 0, 'jsonrpc': '2.0', 'result': '"TVP Animation 11 Pro" 11.5.3 fr'}

--> {"jsonrpc": "2.0", "method": "unknown_method", "params": [], "id": 0}
<-- {'error': {'code': -32601, 'message': 'Method not found'}, 'id': 0, 'jsonrpc': '2.0'}
```

!!! Abstract

    The plugin was adapted from the open source [Ynput/Avalon TVPaint plugin](https://github.com/ynput/OpenPype/tree/develop/openpype/hosts/tvpaint/tvpaint_plugin/plugin_code).
