#!/usr/bin/env python3
"""
check_unreal_mcp.py -- confirms Unreal Engine 5.8's built-in MCP server is
live and answering.

Run this from a NORMAL terminal while the Unreal Editor is open -- not from
inside Unreal's Python console. Unreal ticks its MCP server on the game
thread, so a request issued from within the editor process deadlocks against
itself and times out.

    python scripts/check_unreal_mcp.py [--port 8000]
"""
import argparse
import json
import sys
import urllib.error
import urllib.request


def rpc(url, session, payload):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Origin": "http://127.0.0.1",
    }
    if session:
        headers["Mcp-Session-Id"] = session
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.status, resp.headers.get("Mcp-Session-Id"), resp.read().decode(
            "utf-8", "replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--path", default="/mcp")
    args = ap.parse_args()
    url = "http://127.0.0.1:%d%s" % (args.port, args.path)

    print("probing %s" % url)
    try:
        status, session, body = rpc(url, None, {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "modkit-check", "version": "1.0"},
            },
        })
    except urllib.error.URLError as exc:
        print("FAIL: no answer (%s)" % exc)
        print("  * Is the Unreal Editor open?")
        print("  * Enable Edit > Plugins > Unreal MCP, then restart.")
        print("  * Or run ModelContextProtocol.StartServer in the console.")
        return 1

    print("HTTP %s" % status)
    print("session: %s" % session)
    data = json.loads(body)
    result = data.get("result", {})
    print("protocol: %s" % result.get("protocolVersion"))
    print("capabilities: %s" % json.dumps(result.get("capabilities", {})))
    print("\nOK -- Unreal MCP is live. Point your agent at %s" % url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
