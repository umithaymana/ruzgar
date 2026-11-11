# -*- coding: utf-8 -*-
"""
§10 İleri I — Madde el (KALIN, eşik≥40).
ESP-IDF · FreeRTOS · Home Assistant · ROS2 · Firmata/serial · FreeCAD/G-code.
Mimar: hiç ince kalmasın — tüm katmanlar için geçerli.
Ağ: kısa timeout, URL tavanı, recursive GH ağacı YASAK (asılır).
"""
from __future__ import annotations

import json
import re
import socket
import ssl
import sys
import urllib.parse
import urllib.request
import warnings
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kutuphane_bb_dalga_b_tam_eser as m
from kutuphane_bb_dalga_b_tam_eser import _Links, _chunk_write, _html_to_text, _update_katalog

m.UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
_CTX = ssl._create_unverified_context()
socket.setdefaulttimeout(28)
RAF = m.RAF
REPORT = RAF / "25_ILERI_I_MADDE_RAPOR.json"
MIN_PARCA = 40
FETCH_TO = 28
URL_CAP = 72
# ~10k/parça; 40 parça için güvenli gövde
BODY_TARGET = MIN_PARCA * 11000  # 40 parça için güvenlik payı

DAL15 = "15_elektroni_k"
DAL16 = "16_roboti_k"
DAL17 = "17_mekatroni_k"


def _fetch(url: str, timeout: int = FETCH_TO) -> bytes | None:
    try:
        print("FETCH", url[:110], flush=True)
        req = urllib.request.Request(
            url,
            headers={"User-Agent": m.UA, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8"},
        )
        with urllib.request.urlopen(req, timeout=timeout, context=_CTX) as r:
            data = r.read()
        return data if len(data) >= 200 else None
    except Exception as e:
        print("FETCH_FAIL", url[:90], type(e).__name__, e, flush=True)
        return None


m._fetch = _fetch


def uniq(urls: list[str], cap: int = URL_CAP) -> list[str]:
    seen = set()
    out = []
    for u in urls:
        u = (u or "").split("#")[0].strip()
        if not u or u in seen:
            continue
        seen.add(u)
        out.append(u)
        if len(out) >= cap:
            break
    return out


def bfs(seeds, pred, limit=60, max_depth=1, timeout=FETCH_TO):
    seen = set()
    out = []
    q = deque()
    for s in seeds:
        q.append((s, 0))
        seen.add(s.split("#")[0])
    while q and len(out) < limit:
        url, depth = q.popleft()
        url = url.split("#")[0]
        if not pred(url):
            continue
        out.append(url)
        if depth >= max_depth:
            continue
        data = _fetch(url, timeout=timeout)
        if not data:
            continue
        raw = data.decode("utf-8", "ignore")
        try:
            p = _Links()
            p.feed(raw)
            hrefs = list(p.hrefs)
        except (AssertionError, ValueError):
            hrefs = re.findall(r"""href\s*=\s*["']([^"']+)["']""", raw, flags=re.I)
        for h in hrefs:
            try:
                abs_u = urllib.parse.urljoin(url, h).split("#")[0]
            except ValueError:
                continue
            if "://" not in abs_u or abs_u in seen:
                continue
            try:
                if not pred(abs_u):
                    continue
            except Exception:
                continue
            # JS/CDN/asset atla
            if any(abs_u.lower().endswith(ext) for ext in (".js", ".css", ".png", ".jpg", ".svg", ".zip", ".pdf", ".woff")):
                continue
            seen.add(abs_u)
            q.append((abs_u, depth + 1))
    return out


def deepen_kalin(dal, key, baslik, seed, urls, expected_pages: int) -> dict:
    """HTML listesini kalın hedefe kadar çeker; erken durur (asılma / ince yok)."""
    page_urls = uniq(urls, URL_CAP)
    dal_path = RAF / dal
    raw = dal_path / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    # mevcut parça — asla incelme (küçültme yasağı)
    prev_parca = 0
    kat_path = dal_path / "katalog.json"
    if kat_path.is_file():
        try:
            prev = json.loads(kat_path.read_text(encoding="utf-8"))
            prev_parca = int(((prev.get("kaynaklar") or {}).get(key) or {}).get("parca") or 0)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            prev_parca = 0
    bodies: list[str] = []
    got = 0
    for i, url in enumerate(page_urls):
        data = _fetch(url, timeout=FETCH_TO)
        if not data:
            print("MISS_HTML", url[:100], flush=True)
            continue
        (raw / f"{key}_{i:02d}.html").write_bytes(data)
        text = _html_to_text(data)
        if len(text) < 200:
            print("WEAK_HTML", url[:90], len(text), flush=True)
            continue
        got += 1
        bodies.append(f"\n\n## Kaynak sayfa: {url}\n\n{text}")
        body_len = sum(len(b) for b in bodies)
        print("HTML_OK", got, "chars", len(text), "body", body_len, url[-70:], flush=True)
        # Yeterli gövde + makul sayfa → erken dur (asılma yok, ince yok)
        if body_len >= BODY_TARGET and got >= 22:
            print("EARLY_STOP", key, "got", got, "body", body_len, flush=True)
            break
    body = "\n".join(bodies)
    meta = {
        "kaynak_id": f"{dal}_{key}",
        "baslik": baslik,
        "url": seed,
        "dal": dal,
        "truncated": False,
        "html_pages": got,
        "html_expected": expected_pages,
        "updated_utc": datetime.now(timezone.utc).isoformat(),
    }
    # yeni gövde önceki parçadan zayıfsa yazma (hasar koruması)
    approx = max(1, len(body) // 10000) if body else 0
    if prev_parca and approx < prev_parca and approx < MIN_PARCA:
        print("SKIP_SHRINK", key, "prev", prev_parca, "approx", approx, flush=True)
        meta["parca"] = prev_parca
        meta["parca_sayisi"] = prev_parca
        meta["ok"] = prev_parca >= MIN_PARCA
        meta["tam_eser"] = meta["ok"]
        meta["derin_yesil"] = meta["ok"]
        meta["html_got"] = got
        meta["skipped_shrink"] = True
        return meta
    meta["parca"] = _chunk_write(dal_path, key, body, meta) if body else prev_parca
    meta["parca_sayisi"] = meta["parca"]
    # Mimar: kalın = parça≥40 (tek büyük sayfa da geçerli; sayfa sayısı yalnız yakıt)
    kalin_ok = meta["parca"] >= MIN_PARCA and len(body) > 5000
    meta["ok"] = kalin_ok
    meta["tam_eser"] = kalin_ok
    meta["derin_yesil"] = kalin_ok
    meta["html_got"] = got
    _update_katalog(dal_path, key, meta)
    print(
        "DONE_HTML",
        key,
        "pages",
        got,
        "/",
        expected_pages,
        "parca",
        meta["parca"],
        "yesil",
        meta["derin_yesil"],
        flush=True,
    )
    return meta


def thick(dal, key, baslik, seed, urls, expected_pages: int) -> dict:
    meta = deepen_kalin(dal, key, baslik, seed, urls, expected_pages)
    parca = int(meta.get("parca") or 0)
    flag = "KALIN" if (meta.get("derin_yesil") and parca >= MIN_PARCA) else "INCE!"
    print("THICK", key, "pages", meta.get("html_pages"), "parca", parca, "dy", meta.get("derin_yesil"), flag, flush=True)
    return meta


def gh_raw_fixed(owner: str, repo: str, ref: str, paths: list[str]) -> list[str]:
    return [
        f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{urllib.parse.quote(p)}"
        for p in paths
    ]


def main() -> int:
    try:
        sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
    except Exception:
        pass

    results: dict = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "min_parca": MIN_PARCA,
        "items": {},
    }

    # ---- 1) ESP-IDF — leaf docs, recursive tree YOK ----
    print("=== ESP-IDF", flush=True)
    esp_seeds = [
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/index.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/build-system.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/partition-tables.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/fatal-errors.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/startup.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/deep-sleep-stub.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/wifi.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/bluetooth.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/ulp.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/unit-tests.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/error-handling.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/linker-script-generation.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/app_trace.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/core_dump.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/dfu.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/jtag-debugging/",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/system/freertos.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/system/log.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/system/esp_event.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/system/esp_timer.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/system/mem_alloc.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/network/esp_netif.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/network/esp_wifi.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/protocols/esp_http_client.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/protocols/esp_https_server.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/protocols/mqtt.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/protocols/mdns.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/peripherals/gpio.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/peripherals/uart.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/peripherals/i2c.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/peripherals/spi_master.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/peripherals/adc_oneshot.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/storage/nvs_flash.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/storage/spiffs.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/storage/fatfs.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/security/secure-boot-v2.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/security/flash-encryption.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/hw-reference/esp32/get-started-devkitc.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/low-power-mode.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/performance/index.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/tools/idf-tools.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-guides/tools/idf-monitor.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/migration-guides/index.html",
        "https://docs.espressif.com/projects/esp-idf/en/latest/esp32/api-reference/kconfig.html",
    ]
    urls = bfs(
        esp_seeds[:12],
        lambda u: "docs.espressif.com/projects/esp-idf" in u and "/_static/" not in u,
        limit=40,
        max_depth=1,
    )
    urls = uniq(esp_seeds + urls + gh_raw_fixed(
        "espressif",
        "esp-idf",
        "master",
        [
            "README.md",
            "CONTRIBUTING.md",
            "docs/README.md",
            "examples/README.md",
            "examples/get-started/README.md",
            "examples/wifi/README.md",
            "examples/protocols/README.md",
            "examples/peripherals/README.md",
            "examples/system/README.md",
            "examples/storage/README.md",
        ],
    ))
    print("ESP urls", len(urls), flush=True)
    results["items"]["esp_idf"] = thick(
        DAL15,
        "esp_idf_docs",
        "ESP-IDF docs + selected README — gömülü el (kalın)",
        "https://docs.espressif.com/projects/esp-idf/en/latest/",
        urls,
        40,
    )

    # ---- 2) FreeRTOS ----
    print("=== FreeRTOS", flush=True)
    fr_seeds = [
        "https://www.freertos.org/Documentation/02-Kernel/02-Kernel-features/00-Kernel-features",
        "https://www.freertos.org/Documentation/02-Kernel/02-Kernel-features/01-Tasks-and-co-routines/00-Tasks-and-co-routines",
        "https://www.freertos.org/Documentation/02-Kernel/02-Kernel-features/02-Queues-mutexes-and-semaphores/00-Queues-mutexes-and-semaphores",
        "https://www.freertos.org/Documentation/02-Kernel/02-Kernel-features/03-Direct-to-task-notifications/00-Direct-to-task-notifications",
        "https://www.freertos.org/Documentation/02-Kernel/02-Kernel-features/04-Software-timers/00-Software-timers",
        "https://www.freertos.org/Documentation/02-Kernel/02-Kernel-features/05-Event-groups/00-Event-groups",
        "https://www.freertos.org/Documentation/02-Kernel/02-Kernel-features/06-Stream-and-message-buffers/00-Stream-and-message-buffers",
        "https://www.freertos.org/Documentation/02-Kernel/04-API-references/01-Task-creation/00-TaskCreation",
        "https://www.freertos.org/Documentation/02-Kernel/04-API-references/02-Task-control/00-TaskControl",
        "https://www.freertos.org/Documentation/02-Kernel/04-API-references/03-Queue-management/00-QueueManagement",
        "https://www.freertos.org/Documentation/02-Kernel/04-API-references/04-Semaphore-and-Mutexes/00-Semaphores",
        "https://www.freertos.org/Documentation/02-Kernel/04-API-references/05-Software-timer-control/00-SoftwareTimers",
        "https://www.freertos.org/Documentation/02-Kernel/04-API-references/06-Event-groups-or-flags/00-EventGroups",
        "https://www.freertos.org/Documentation/02-Kernel/04-API-references/10-Task-notifications/00-TaskNotifications",
        "https://www.freertos.org/Documentation/02-Kernel/07-Memory-management/01-Memory-management",
        "https://www.freertos.org/Documentation/02-Kernel/07-Memory-management/02-Example-implementations",
        "https://www.freertos.org/Documentation/03-Libraries/02-Networking-and-connectivity/01-FreeRTOS-Plus-TCP/01-Introduction",
        "https://www.freertos.org/features.html",
        "https://www.freertos.org/implementation/a00002.html",
        "https://www.freertos.org/a00106.html",
        "https://www.freertos.org/Realtime_task_priorities.html",
        "https://www.freertos.org/Queues-Semaphores-Mutexes.html",
        "https://www.freertos.org/Interrupts.html",
        "https://www.freertos.org/Software-timers.html",
        "https://www.freertos.org/FreeRTOS-Plus/",
        "https://www.freertos.org/Documentation/RTOS_book.html",
    ]
    urls = uniq(
        fr_seeds
        + bfs(
            fr_seeds[:8],
            lambda u: "freertos.org" in u and not u.endswith((".zip", ".pdf")),
            limit=40,
            max_depth=1,
        )
        + gh_raw_fixed(
            "FreeRTOS",
            "FreeRTOS-Kernel",
            "main",
            ["README.md", "History.txt", "Quick_Start_Guide.md"],
        )
    )
    print("FreeRTOS urls", len(urls), flush=True)
    results["items"]["freertos"] = thick(
        DAL15,
        "freertos_docs",
        "FreeRTOS kernel + API — gerçek zamanlı el (kalın)",
        "https://www.freertos.org/Documentation/RTOS_book.html",
        urls,
        40,
    )

    # ---- 3) Home Assistant ----
    print("=== Home Assistant", flush=True)
    ha_seeds = [
        "https://www.home-assistant.io/getting-started/",
        "https://www.home-assistant.io/docs/",
        "https://www.home-assistant.io/docs/configuration/",
        "https://www.home-assistant.io/docs/configuration/yaml/",
        "https://www.home-assistant.io/docs/configuration/basic/",
        "https://www.home-assistant.io/docs/automation/",
        "https://www.home-assistant.io/docs/automation/basics/",
        "https://www.home-assistant.io/docs/automation/trigger/",
        "https://www.home-assistant.io/docs/automation/condition/",
        "https://www.home-assistant.io/docs/automation/action/",
        "https://www.home-assistant.io/docs/scripts/",
        "https://www.home-assistant.io/docs/scene/",
        "https://www.home-assistant.io/docs/blueprint/",
        "https://www.home-assistant.io/docs/mqtt/",
        "https://www.home-assistant.io/docs/mqtt/broker/",
        "https://www.home-assistant.io/docs/mqtt/discovery/",
        "https://www.home-assistant.io/docs/mqtt/sensor/",
        "https://www.home-assistant.io/docs/energy/",
        "https://www.home-assistant.io/docs/backend/database/",
        "https://www.home-assistant.io/docs/auth/",
        "https://www.home-assistant.io/docs/hassio/",
        "https://www.home-assistant.io/integrations/",
        "https://www.home-assistant.io/integrations/mqtt/",
        "https://www.home-assistant.io/integrations/esphome/",
        "https://www.home-assistant.io/integrations/zwave_js/",
        "https://www.home-assistant.io/integrations/zigbee/",
        "https://www.home-assistant.io/integrations/modbus/",
        "https://www.home-assistant.io/integrations/template/",
        "https://www.home-assistant.io/integrations/rest/",
        "https://www.home-assistant.io/integrations/shell_command/",
        "https://www.home-assistant.io/voice_control/",
        "https://www.home-assistant.io/dashboards/",
        "https://www.home-assistant.io/common-tasks/general/",
        "https://www.home-assistant.io/installation/",
        "https://developers.home-assistant.io/docs/architecture_index/",
        "https://developers.home-assistant.io/docs/development_index/",
        "https://developers.home-assistant.io/docs/api/websocket/",
        "https://developers.home-assistant.io/docs/api/rest/",
        "https://developers.home-assistant.io/docs/core/entity/",
        "https://developers.home-assistant.io/docs/creating_integration_file_structure/",
    ]
    urls = uniq(
        ha_seeds
        + bfs(
            ha_seeds[:10],
            lambda u: (
                ("home-assistant.io" in u)
                and ("/docs/" in u or "/integrations/" in u or "/getting-started" in u or "developers.home-assistant.io" in u)
            ),
            limit=35,
            max_depth=1,
        )
        + gh_raw_fixed(
            "home-assistant",
            "home-assistant.io",
            "current",
            [
                "README.md",
                "source/_docs/configuration/index.markdown",
                "source/_docs/automation/index.markdown",
                "source/_docs/mqtt/index.markdown",
            ],
        )
    )
    print("HA urls", len(urls), flush=True)
    results["items"]["home_assistant"] = thick(
        DAL16,
        "home_assistant_docs",
        "Home Assistant docs + entegrasyon — ev otomasyonu el (kalın)",
        "https://www.home-assistant.io/docs/",
        urls,
        40,
    )

    # ---- 4) ROS2 ----
    print("=== ROS2", flush=True)
    ros_seeds = [
        "https://docs.ros.org/en/humble/index.html",
        "https://docs.ros.org/en/humble/Installation.html",
        "https://docs.ros.org/en/humble/Tutorials.html",
        "https://docs.ros.org/en/humble/Concepts.html",
        "https://docs.ros.org/en/humble/How-To-Guides.html",
        "https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools/Configuring-ROS2-Environment.html",
        "https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools/Introducing-Turtlesim/Introducing-Turtlesim.html",
        "https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Nodes/Understanding-ROS2-Nodes.html",
        "https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Topics/Understanding-ROS2-Topics.html",
        "https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Services/Understanding-ROS2-Services.html",
        "https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Actions/Understanding-ROS2-Actions.html",
        "https://docs.ros.org/en/humble/Tutorials/Beginner-CLI-Tools/Understanding-ROS2-Parameters/Understanding-ROS2-Parameters.html",
        "https://docs.ros.org/en/humble/Tutorials/Beginner-Client-Libraries/Creating-A-Workspace/Creating-A-Workspace.html",
        "https://docs.ros.org/en/humble/Tutorials/Beginner-Client-Libraries/Creating-Your-First-ROS2-Package.html",
        "https://docs.ros.org/en/humble/Tutorials/Beginner-Client-Libraries/Writing-A-Simple-Py-Publisher-And-Subscriber.html",
        "https://docs.ros.org/en/humble/Tutorials/Intermediate/Launch/Launch-Main.html",
        "https://docs.ros.org/en/humble/Tutorials/Intermediate/Tf2/Introduction-To-Tf2.html",
        "https://docs.ros.org/en/humble/Tutorials/Intermediate/Testing/CLI.html",
        "https://docs.ros.org/en/humble/Concepts/Basic.html",
        "https://docs.ros.org/en/humble/Concepts/Intermediate.html",
        "https://docs.ros.org/en/humble/Concepts/Advanced.html",
        "https://docs.ros.org/en/humble/Concepts/Basic/About-Nodes.html",
        "https://docs.ros.org/en/humble/Concepts/Basic/About-Topics.html",
        "https://docs.ros.org/en/humble/Concepts/Basic/About-Services.html",
        "https://docs.ros.org/en/humble/Concepts/Basic/About-Actions.html",
        "https://docs.ros.org/en/humble/Concepts/Basic/About-Interfaces.html",
        "https://docs.ros.org/en/humble/How-To-Guides/Launch-file-different-formats.html",
        "https://docs.ros.org/en/humble/How-To-Guides/Topics-Services-Actions.html",
        "https://docs.ros.org/en/humble/How-To-Guides/Sync-Vs-Async.html",
        "https://docs.ros.org/en/humble/How-To-Guides/Overriding-QoS-Policies-For-Recording-And-Playback.html",
        "https://docs.ros.org/en/humble/Releases.html",
        "https://docs.ros.org/en/humble/Related-Projects.html",
        "https://docs.ros2.org/latest/",
    ]
    urls = uniq(
        ros_seeds
        + bfs(
            ros_seeds[:8],
            lambda u: "docs.ros.org" in u or "docs.ros2.org" in u,
            limit=35,
            max_depth=1,
        )
        + gh_raw_fixed(
            "ros2",
            "ros2_documentation",
            "humble",
            ["README.md", "source/Tutorials.rst", "source/Installation.rst", "source/Concepts.rst"],
        )
    )
    print("ROS2 urls", len(urls), flush=True)
    results["items"]["ros2"] = thick(
        DAL16,
        "ros2_docs",
        "ROS 2 Humble docs — robotik el (kalın)",
        "https://docs.ros.org/en/humble/",
        urls,
        40,
    )

    # ---- 5) Firmata + serial (küçük repolar OK; fixed path tercih) ----
    print("=== Firmata/serial", flush=True)
    urls = uniq(
        [
            "https://www.arduino.cc/reference/en/language/functions/communication/serial/",
            "https://docs.arduino.cc/learn/communication/uart/",
            "https://docs.arduino.cc/language-reference/en/functions/communication/serial/",
            "https://docs.arduino.cc/built-in-examples/communication/SerialCallResponse/",
            "https://docs.arduino.cc/built-in-examples/communication/SerialEvent/",
            "https://docs.arduino.cc/built-in-examples/communication/SerialCallResponseASCII/",
            "https://docs.arduino.cc/built-in-examples/communication/MIDI/",
            "https://docs.arduino.cc/learn/communication/wire/",
            "https://docs.arduino.cc/learn/communication/spi/",
            "https://pyserial.readthedocs.io/en/latest/",
            "https://pyserial.readthedocs.io/en/latest/shortintro.html",
            "https://pyserial.readthedocs.io/en/latest/pyserial_api.html",
            "https://pyserial.readthedocs.io/en/latest/tools.html",
            "https://pyserial.readthedocs.io/en/latest/url_handlers.html",
            "https://pyserial.readthedocs.io/en/latest/examples.html",
            "https://pyserial.readthedocs.io/en/latest/appendix.html",
            "https://github.com/firmata/protocol",
            "https://github.com/firmata/arduino",
            "https://github.com/pyserial/pyserial",
        ]
        + bfs(
            [
                "https://pyserial.readthedocs.io/en/latest/",
                "https://docs.arduino.cc/learn/communication/uart/",
                "https://www.arduino.cc/reference/en/language/functions/communication/serial/",
            ],
            lambda u: any(
                x in u
                for x in [
                    "arduino.cc",
                    "docs.arduino.cc",
                    "pyserial.readthedocs.io",
                    "github.com/pyserial",
                    "github.com/firmata",
                ]
            ),
            limit=40,
            max_depth=1,
        )
        + gh_raw_fixed(
            "firmata",
            "protocol",
            "master",
            [
                "README.md",
                "protocol.md",
                "protocolVersioning.md",
                "featureProposal.md",
                "additions.md",
            ],
        )
        + gh_raw_fixed(
            "firmata",
            "arduino",
            "master",
            [
                "readme.md",
                "examples/StandardFirmata/StandardFirmata.ino",
                "examples/AnalogFirmata/AnalogFirmata.ino",
                "examples/EchoString/EchoString.ino",
            ],
        )
        + gh_raw_fixed(
            "pyserial",
            "pyserial",
            "master",
            [
                "README.rst",
                "documentation/shortintro.rst",
                "documentation/pyserial_api.rst",
                "documentation/tools.rst",
                "documentation/examples.rst",
                "documentation/url_handlers.rst",
            ],
        )
    )
    print("Firmata urls", len(urls), flush=True)
    results["items"]["firmata_serial"] = thick(
        DAL15,
        "firmata_serial",
        "Firmata + pySerial + Arduino UART — seri köprü (kalın)",
        "https://github.com/firmata/protocol",
        urls,
        35,
    )

    # ---- 6) FreeCAD + G-code ----
    print("=== FreeCAD/G-code", flush=True)
    fc_seeds = [
        "https://wiki.freecad.org/Main_Page",
        "https://wiki.freecad.org/Getting_started",
        "https://wiki.freecad.org/User_hub",
        "https://wiki.freecad.org/Power_users_hub",
        "https://wiki.freecad.org/Manual",
        "https://wiki.freecad.org/Part_Workbench",
        "https://wiki.freecad.org/PartDesign_Workbench",
        "https://wiki.freecad.org/Sketcher_Workbench",
        "https://wiki.freecad.org/TechDraw_Workbench",
        "https://wiki.freecad.org/Path_Workbench",
        "https://wiki.freecad.org/CAM_Workbench",
        "https://wiki.freecad.org/Mesh_Workbench",
        "https://wiki.freecad.org/Python_scripting_tutorial",
        "https://wiki.freecad.org/FreeCAD_Scripting_Basics",
        "https://wiki.freecad.org/Topological_data_scripting",
        "https://wiki.freecad.org/Scripted_objects",
        "https://wiki.freecad.org/Macros",
        "https://wiki.freecad.org/FeaturePython_Custom_Properties",
        "https://wiki.freecad.org/PartDesign_Pad",
        "https://wiki.freecad.org/PartDesign_Pocket",
        "https://wiki.freecad.org/Sketcher_CreateSketch",
        "https://wiki.freecad.org/Path_Post",
        "https://wiki.freecad.org/CAM_Post",
        "https://linuxcnc.org/docs/stable/html/",
        "https://linuxcnc.org/docs/stable/html/gcode/overview.html",
        "https://linuxcnc.org/docs/stable/html/gcode/g-code.html",
        "https://linuxcnc.org/docs/stable/html/gcode/m-code.html",
        "https://linuxcnc.org/docs/stable/html/gcode/o-code.html",
        "https://linuxcnc.org/docs/stable/html/gcode/other-code.html",
        "https://linuxcnc.org/docs/stable/html/gcode/coordinates.html",
        "https://linuxcnc.org/docs/stable/html/gcode/tool_compensation.html",
        "https://reprap.org/wiki/G-code",
        "https://reprap.org/wiki/G-code/Introduction",
        "https://marlinfw.org/docs/gcode/G000-G001.html",
        "https://marlinfw.org/docs/gcode/G028.html",
        "https://marlinfw.org/docs/gcode/M104.html",
        "https://marlinfw.org/docs/gcode/M109.html",
        "https://marlinfw.org/meta/gcode/",
    ]
    urls = uniq(
        fc_seeds
        + bfs(
            fc_seeds[:10],
            lambda u: any(
                x in u
                for x in [
                    "wiki.freecad.org",
                    "linuxcnc.org/docs",
                    "reprap.org/wiki/G-code",
                    "marlinfw.org",
                ]
            ),
            limit=40,
            max_depth=1,
        )
        + gh_raw_fixed(
            "FreeCAD",
            "FreeCAD",
            "main",
            [
                "README.md",
                "CODE_OF_CONDUCT.md",
                "SECURITY.md",
                "src/Mod/Path/README.md",
                "src/Mod/CAM/README.md",
                "src/Mod/Part/README.md",
                "src/Mod/PartDesign/README.md",
                "src/Mod/Sketcher/README.md",
                "src/Mod/Mesh/README.md",
                "src/Mod/TechDraw/README.md",
            ],
        )
    )
    print("FreeCAD urls", len(urls), flush=True)
    results["items"]["freecad_gcode"] = thick(
        DAL17,
        "freecad_gcode",
        "FreeCAD wiki + LinuxCNC/RepRap/Marlin G-code — sahneden parçaya (kalın)",
        "https://wiki.freecad.org/Main_Page",
        urls,
        40,
    )

    ince = []
    kalin = 0
    for k, v in results["items"].items():
        parca = int(v.get("parca") or 0)
        dy = bool(v.get("derin_yesil"))
        print("SUMMARY", k, "parca", parca, "dy", dy, "pages", v.get("html_pages"), flush=True)
        if dy and parca >= MIN_PARCA:
            kalin += 1
        else:
            ince.append({"key": k, "parca": parca, "dy": dy, "pages": v.get("html_pages")})

    results["kalin"] = kalin
    results["n"] = len(results["items"])
    results["ince"] = ince
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("WROTE", REPORT, flush=True)
    print("DONE_ILERI_I", "kalin", kalin, "/", results["n"], "ince", len(ince), flush=True)
    if ince:
        print("INCE_LIST", ince, flush=True)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
