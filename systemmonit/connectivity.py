"""Network connectivity diagnostics — DNS / TCP / HTTP latency checks."""

from __future__ import annotations

import socket
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Dict, List, Optional, Tuple

ProgressCb = Optional[Callable[[Dict[str, Any]], None]]

# Curated targets similar to consumer network diagnostic products
TARGETS: List[Dict[str, Any]] = [
    {"id": "resolve_baidu", "name": "解析 baidu.com", "kind": "resolve", "host": "www.baidu.com"},
    {"id": "resolve_apple", "name": "解析 apple.com", "kind": "resolve", "host": "www.apple.com"},
    {"id": "dns_ali", "name": "阿里 DNS", "kind": "tcp", "host": "223.5.5.5", "port": 443},
    {"id": "dns_dnsPod", "name": "腾讯 DNS", "kind": "tcp", "host": "doh.pub", "port": 443},
    {"id": "tcp_apple", "name": "Apple", "kind": "tcp", "host": "www.apple.com", "port": 443},
    {"id": "tcp_ms", "name": "Microsoft", "kind": "tcp", "host": "www.microsoft.com", "port": 443},
    {"id": "tcp_cf", "name": "Cloudflare", "kind": "tcp", "host": "www.cloudflare.com", "port": 443},
    {"id": "tcp_bd", "name": "百度节点", "kind": "tcp", "host": "www.baidu.com", "port": 443},
    {"id": "http_baidu", "name": "百度", "kind": "http", "url": "https://www.baidu.com/", "host": "www.baidu.com"},
    {"id": "http_qq", "name": "腾讯", "kind": "http", "url": "https://www.qq.com/", "host": "www.qq.com"},
    {"id": "http_apple", "name": "Apple 连通", "kind": "http", "url": "https://www.apple.com/library/test/success.html", "host": "www.apple.com"},
    {"id": "http_gh", "name": "GitHub", "kind": "http", "url": "https://github.com/", "host": "github.com"},
]


def _grade(ms: Optional[float], *, ok: bool) -> str:
    if not ok or ms is None:
        return "fail"
    if ms < 50:
        return "excellent"
    if ms < 100:
        return "good"
    if ms < 200:
        return "fair"
    if ms < 400:
        return "slow"
    return "poor"


def _grade_cn(g: str) -> str:
    return {
        "excellent": "极佳",
        "good": "良好",
        "fair": "一般",
        "slow": "偏慢",
        "poor": "较差",
        "fail": "失败",
    }.get(g, g)


def _dns_resolve(host: str, timeout: float = 3.0) -> Tuple[bool, Optional[float], str, List[str]]:
    t0 = time.perf_counter()
    try:
        socket.setdefaulttimeout(timeout)
        infos = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        ms = (time.perf_counter() - t0) * 1000.0
        addrs = []
        for info in infos:
            ip = info[4][0]
            if ip not in addrs:
                addrs.append(ip)
            if len(addrs) >= 3:
                break
        return True, ms, "", addrs
    except Exception as exc:
        ms = (time.perf_counter() - t0) * 1000.0
        return False, ms, str(exc)[:120], []


def _tcp_connect(host: str, port: int, timeout: float = 2.8) -> Tuple[bool, Optional[float], str]:
    t0 = time.perf_counter()
    last_err = ""
    try:
        infos = socket.getaddrinfo(host, int(port), socket.AF_UNSPEC, socket.SOCK_STREAM)
    except Exception as exc:
        ms = (time.perf_counter() - t0) * 1000.0
        return False, ms, str(exc)[:120]
    # Prefer IPv4 first to avoid slow IPv6 blackholes common on some networks
    infos = sorted(infos, key=lambda info: 0 if info[0] == socket.AF_INET else 1)
    for family, socktype, proto, _canon, sockaddr in infos[:4]:
        try:
            with socket.socket(family, socktype, proto) as sock:
                sock.settimeout(timeout)
                sock.connect(sockaddr)
                ms = (time.perf_counter() - t0) * 1000.0
                return True, ms, ""
        except Exception as exc:
            last_err = str(exc)[:120]
            continue
    ms = (time.perf_counter() - t0) * 1000.0
    return False, ms, last_err or "连接失败"


def _http_latency(url: str, timeout: float = 4.0) -> Tuple[bool, Optional[float], str, int]:
    t0 = time.perf_counter()
    code = 0
    try:
        req = urllib.request.Request(
            url,
            method="GET",
            headers={
                "User-Agent": "SupToolsConnectivity/1.0",
                "Accept": "*/*",
                "Connection": "close",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = int(getattr(resp, "status", 0) or 0)
            try:
                resp.read(64)
            except Exception:
                pass
        ms = (time.perf_counter() - t0) * 1000.0
        ok = 200 <= code < 500
        return ok, ms, "" if ok else f"HTTP {code}", code
    except urllib.error.HTTPError as exc:
        ms = (time.perf_counter() - t0) * 1000.0
        code = int(exc.code or 0)
        ok = code > 0
        return ok, ms, f"HTTP {code}", code
    except Exception as exc:
        ms = (time.perf_counter() - t0) * 1000.0
        # Still report latency; treat TLS/redirect noise as soft fail only if no bytes
        return False, ms, str(exc)[:120], 0


def _run_one(target: Dict[str, Any]) -> Dict[str, Any]:
    kind = str(target.get("kind") or "")
    name = str(target.get("name") or target.get("id") or "")
    tid = str(target.get("id") or name)
    out: Dict[str, Any] = {
        "id": tid,
        "name": name,
        "kind": kind,
        "ok": False,
        "ms": None,
        "grade": "fail",
        "grade_cn": "失败",
        "detail": "",
        "addrs": [],
        "http_code": 0,
    }
    if kind == "resolve":
        ok, ms, err, addrs = _dns_resolve(str(target.get("host") or ""))
        out.update(ok=ok, ms=round(ms, 1) if ms is not None else None, detail=err or (" / ".join(addrs) if addrs else ""), addrs=addrs)
    elif kind == "dns":
        # Treat DNS IP reachability as TCP to 53 (or ICMP-less TCP probe)
        host = str(target.get("host") or "")
        port = int(target.get("port") or 53)
        ok, ms, err = _tcp_connect(host, port)
        # Fallback: resolve check if TCP 53 blocked
        if not ok:
            ok2, ms2, err2, addrs = _dns_resolve(host if not host.replace(".", "").isdigit() else "www.baidu.com")
            if ok2:
                ok, ms, err = True, ms2, "解析成功"
                out["addrs"] = addrs
            else:
                err = err or err2
        out.update(ok=ok, ms=round(ms, 1) if ms is not None else None, detail=err or host)
    elif kind == "tcp":
        ok, ms, err = _tcp_connect(str(target.get("host") or ""), int(target.get("port") or 443))
        out.update(ok=ok, ms=round(ms, 1) if ms is not None else None, detail=err or f':{target.get("port")}')
    elif kind == "http":
        ok, ms, err, code = _http_latency(str(target.get("url") or ""))
        out.update(
            ok=ok,
            ms=round(ms, 1) if ms is not None else None,
            detail=err or (f"HTTP {code}" if code else "OK"),
            http_code=code,
        )
    else:
        out["detail"] = "未知类型"
    g = _grade(out.get("ms"), ok=bool(out.get("ok")))
    out["grade"] = g
    out["grade_cn"] = _grade_cn(g)
    return out


def _score(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    ok_n = sum(1 for r in results if r.get("ok"))
    total = len(results) or 1
    all_lat = [float(r["ms"]) for r in results if r.get("ok") and r.get("ms") is not None]
    # Prefer handshake/DNS latency for quality score; HTTP includes TTFB + TLS and skews high
    core_lat = [
        float(r["ms"])
        for r in results
        if r.get("ok") and r.get("ms") is not None and r.get("kind") in ("dns", "tcp", "resolve")
    ]
    latencies = core_lat or all_lat
    avg = sum(latencies) / len(latencies) if latencies else None
    avg_all = sum(all_lat) / len(all_lat) if all_lat else None
    ratio = ok_n / total
    if avg is None:
        score = int(round(ratio * 55))
    else:
        # 0ms → 45 latency points, 300ms → 0 (handshake-oriented)
        lat_pts = max(0.0, 45.0 * (1.0 - min(avg, 300.0) / 300.0))
        score = int(round(ratio * 55 + lat_pts))
    score = max(0, min(100, score))
    if ok_n == total and score < 80:
        score = max(score, 82)
    elif ratio >= 0.9 and score < 70:
        score = max(score, 72)
    if score >= 90:
        label, tone = "优秀", "excellent"
    elif score >= 75:
        label, tone = "良好", "good"
    elif score >= 60:
        label, tone = "一般", "fair"
    elif score >= 40:
        label, tone = "较差", "poor"
    else:
        label, tone = "异常", "fail"
    return {
        "score": score,
        "label": label,
        "tone": tone,
        "ok_count": ok_n,
        "total": total,
        "avg_ms": round(avg_all, 1) if avg_all is not None else None,
        "core_avg_ms": round(avg, 1) if avg is not None else None,
        "success_rate": round(ratio * 100, 1),
    }


def run_connectivity_test(
    *,
    on_progress: ProgressCb = None,
    cancel_check: Optional[Callable[[], bool]] = None,
) -> Dict[str, Any]:
    """Run all probes; call on_progress with incremental updates."""
    results: List[Dict[str, Any]] = []
    total = len(TARGETS)
    started = time.time()

    def emit(phase: str, **extra: Any) -> None:
        if not on_progress:
            return
        payload = {
            "phase": phase,
            "percent": int(round(100 * len(results) / total)) if total else 0,
            "done": len(results),
            "total": total,
            "results": list(results),
            **extra,
        }
        try:
            on_progress(payload)
        except Exception:
            pass

    emit("start", message="开始检测…", current="")

    # Sequential feels more "diagnostic product" with live row updates;
    # still use a small pool for HTTP/TCP overlap.
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(_run_one, t): t for t in TARGETS}
        for fut in as_completed(futures):
            if cancel_check and cancel_check():
                emit("cancelled", message="已取消")
                break
            target = futures[fut]
            try:
                item = fut.result()
            except Exception as exc:
                item = {
                    "id": target.get("id"),
                    "name": target.get("name"),
                    "kind": target.get("kind"),
                    "ok": False,
                    "ms": None,
                    "grade": "fail",
                    "grade_cn": "失败",
                    "detail": str(exc)[:120],
                    "addrs": [],
                    "http_code": 0,
                }
            results.append(item)
            # Keep stable display order by TARGETS order
            order = {str(t["id"]): i for i, t in enumerate(TARGETS)}
            results.sort(key=lambda r: order.get(str(r.get("id")), 999))
            emit(
                "progress",
                message=f"正在测试 {item.get('name')}…",
                current=str(item.get("name") or ""),
                last=item,
            )

    summary = _score(results)
    summary.update(
        {
            "phase": "done",
            "percent": 100,
            "done": len(results),
            "total": total,
            "results": results,
            "elapsed_ms": int(round((time.time() - started) * 1000)),
            "message": "检测完成",
            "groups": _group_results(results),
            "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "busy": False,
        }
    )
    if on_progress:
        try:
            on_progress(dict(summary))
        except Exception:
            pass
    return summary


def _group_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    labels = {
        "resolve": ("域名解析", "本机 DNS 查询耗时"),
        "dns": ("DNS 服务", "公共 DNS 可达性"),
        "tcp": ("节点连通", "HTTPS 端口握手延迟"),
        "http": ("网站访问", "真实 HTTP 请求往返"),
    }
    # Merge legacy dns kind into tcp presentation when mixed
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for r in results:
        kind = str(r.get("kind") or "other")
        if kind == "dns":
            kind = "tcp"
        buckets.setdefault(kind, []).append(r)
    out = []
    for kind in ("resolve", "tcp", "http"):
        rows = buckets.get(kind) or []
        if not rows:
            continue
        title, desc = labels.get(kind, (kind, ""))
        ok_n = sum(1 for r in rows if r.get("ok"))
        out.append({
            "kind": kind,
            "title": title,
            "desc": desc,
            "ok_count": ok_n,
            "total": len(rows),
            "items": rows,
        })
    return out
