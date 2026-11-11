# -*- coding: utf-8 -*-
"""Sağlama pass-2: kalan inceleri özel URL paketleriyle kalınlaştır."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _ileri_i_madde_kalin as i
import _saglama_tum_ince_kalin as s

MIN = i.MIN_PARCA
RAF = i.RAF
REPORT = RAF / "25_SAGLAMA_PASS2_RAPOR.json"

# key → ek URL listesi (yasal/açık)
EXTRA: dict[str, list[str]] = {
    "tour_of_go": [f"https://go.dev/tour/welcome/{n}" for n in range(1, 25)]
    + [f"https://go.dev/tour/basics/{n}" for n in range(1, 18)]
    + [f"https://go.dev/tour/flowcontrol/{n}" for n in range(1, 14)]
    + [f"https://go.dev/tour/moretypes/{n}" for n in range(1, 27)]
    + [f"https://go.dev/tour/methods/{n}" for n in range(1, 26)]
    + [f"https://go.dev/tour/concurrency/{n}" for n in range(1, 12)],
    "zero2prod": [
        "https://www.zero2prod.com/",
        "https://github.com/LukeMathWalker/zero-to-production",
        "https://raw.githubusercontent.com/LukeMathWalker/zero-to-production/main/README.md",
        "https://raw.githubusercontent.com/LukeMathWalker/zero-to-production/main/Cargo.toml",
    ],
    "little_semaphores": [
        "https://greenteapress.com/semaphores/LittleBookOfSemaphores.pdf",
    ],
    "node_best": [
        f"https://raw.githubusercontent.com/goldbergyoni/nodebestpractices/master/sections/{p}"
        for p in [
            "1-project-structure-practices/1-structure-by-components.md",
            "2-error-handling-practices/2.1-async-await.md",
            "3-code-style-practices/3.1-eslint.md",
            "4-testing-and-overall-quality-practices/4.1-at-least.md",
            "5-going-to-production-practices/5.1-monitoring.md",
            "6-security-best-practices/6.1-security-linter.md",
            "7-performance-best-practices/7.1-monitor.md",
        ]
    ]
    + [
        "https://raw.githubusercontent.com/goldbergyoni/nodebestpractices/master/README.md",
        "https://raw.githubusercontent.com/goldbergyoni/nodebestpractices/master/README.chinese.md",
        "https://raw.githubusercontent.com/goldbergyoni/nodebestpractices/master/README.korean.md",
        "https://raw.githubusercontent.com/goldbergyoni/nodebestpractices/master/README.russian.md",
        "https://raw.githubusercontent.com/goldbergyoni/nodebestpractices/master/README.brazilian-portuguese.md",
        "https://raw.githubusercontent.com/goldbergyoni/nodebestpractices/master/README.european-portuguese.md",
        "https://raw.githubusercontent.com/goldbergyoni/nodebestpractices/master/README.japanese.md",
    ],
    "openstax_calc1_pdf": [
        "https://assets.openstax.org/oscms-prodcms/media/documents/CalculusVolume1-OP_bDvXKrE.pdf",
        "https://openstax.org/details/books/calculus-volume-1",
    ],
    "openstax_up1_pdf": [
        "https://assets.openstax.org/oscms-prodcms/media/documents/UniversityPhysicsVolume1-OP.pdf",
        "https://openstax.org/details/books/university-physics-volume-1",
    ],
    "openstax_physics": [
        "https://openstax.org/books/university-physics-volume-1/pages/1-introduction",
        "https://openstax.org/books/university-physics-volume-1/pages/1-1-the-scope-and-scale-of-physics",
        "https://openstax.org/books/university-physics-volume-1/pages/2-1-scalars-and-vectors",
        "https://openstax.org/books/university-physics-volume-1/pages/3-1-position-displacement-and-average-velocity",
        "https://openstax.org/books/university-physics-volume-1/pages/4-1-displacement-and-velocity-vectors",
        "https://openstax.org/books/university-physics-volume-1/pages/5-1-forces",
        "https://openstax.org/books/university-physics-volume-1/pages/6-1-solving-problems-with-newtons-laws",
        "https://openstax.org/books/university-physics-volume-1/pages/7-1-work",
        "https://openstax.org/books/university-physics-volume-1/pages/8-1-conservative-forces",
        "https://openstax.org/books/university-physics-volume-1/pages/9-1-linear-momentum",
        "https://openstax.org/books/university-physics-volume-1/pages/10-1-rotational-variables",
        "https://assets.openstax.org/oscms-prodcms/media/documents/UniversityPhysicsVolume1-OP.pdf",
    ],
    "openstax_linalg": [
        "https://openstax.org/books/algebra-and-trigonometry/pages/1-introduction-to-prerequisites",
        "https://openstax.org/books/algebra-and-trigonometry/pages/2-1-the-rectangular-coordinate-systems",
        "https://openstax.org/books/algebra-and-trigonometry/pages/3-1-functions-and-function-notation",
        "https://openstax.org/books/algebra-and-trigonometry/pages/4-1-linear-functions",
        "https://openstax.org/books/algebra-and-trigonometry/pages/5-1-angles",
        "https://openstax.org/books/algebra-and-trigonometry/pages/6-1-graphs-of-the-sine-and-cosine-functions",
        "https://openstax.org/books/algebra-and-trigonometry/pages/7-1-solving-trigonometric-equations-with-identities",
        "https://openstax.org/books/algebra-and-trigonometry/pages/8-1-non-right-triangles-law-of-sines",
        "https://openstax.org/books/algebra-and-trigonometry/pages/9-1-systems-of-linear-equations-two-variables",
        "https://openstax.org/books/algebra-and-trigonometry/pages/10-1-non-right-triangles-law-of-sines",
        "https://openstax.org/books/algebra-and-trigonometry/pages/11-1-sequences-and-their-notations",
        "https://openstax.org/books/algebra-and-trigonometry/pages/12-1-finding-limits-numerical-and-graphical-approaches",
    ],
    "openstax_psych_page": [
        "https://openstax.org/books/psychology-2e/pages/1-introduction",
        "https://openstax.org/books/psychology-2e/pages/2-1-psychologists-use-the-scientific-method",
        "https://openstax.org/books/psychology-2e/pages/3-1-human-genetics",
        "https://openstax.org/books/psychology-2e/pages/4-1-what-is-consciousness",
        "https://openstax.org/books/psychology-2e/pages/5-1-sensation-versus-perception",
        "https://openstax.org/books/psychology-2e/pages/6-1-what-is-learning",
        "https://openstax.org/books/psychology-2e/pages/7-1-what-is-cognition",
        "https://openstax.org/books/psychology-2e/pages/8-1-how-memory-functions",
        "https://openstax.org/books/psychology-2e/pages/9-1-what-are-lifespan-theories",
        "https://openstax.org/books/psychology-2e/pages/10-1-motivation",
        "https://openstax.org/books/psychology-2e/pages/11-1-what-is-personality",
        "https://openstax.org/books/psychology-2e/pages/12-1-what-is-social-psychology",
        "https://openstax.org/books/psychology-2e/pages/14-1-what-is-stress",
        "https://openstax.org/books/psychology-2e/pages/15-1-what-are-psychological-disorders",
        "https://openstax.org/books/psychology-2e/pages/16-1-mental-health-treatment",
    ],
    "openstax_econ_page": [
        "https://openstax.org/books/principles-economics-3e/pages/1-introduction",
        "https://openstax.org/books/principles-economics-3e/pages/2-1-how-individuals-make-choices-based-on-their-budget-constraint",
        "https://openstax.org/books/principles-economics-3e/pages/3-1-demand-supply-and-equilibrium-in-markets-for-goods-and-services",
        "https://openstax.org/books/principles-economics-3e/pages/4-1-demand-and-supply-at-work-in-labor-markets",
        "https://openstax.org/books/principles-economics-3e/pages/5-1-price-elasticity-of-demand-and-price-elasticity-of-supply",
        "https://openstax.org/books/principles-economics-3e/pages/6-1-consumption-choices",
        "https://openstax.org/books/principles-economics-3e/pages/7-1-explicit-and-implicit-costs-and-accounting-and-economic-profit",
        "https://openstax.org/books/principles-economics-3e/pages/8-1-perfect-competition-and-why-it-matters",
        "https://openstax.org/books/principles-economics-3e/pages/9-1-how-monopolies-form-barriers-to-entry",
        "https://openstax.org/books/principles-economics-3e/pages/10-1-monopolistic-competition",
        "https://openstax.org/books/principles-economics-3e/pages/11-1-corporate-mergers",
        "https://openstax.org/books/principles-economics-3e/pages/12-1-the-economics-of-pollution",
        "https://openstax.org/books/principles-economics-3e/pages/19-1-measuring-the-size-of-the-economy-gross-domestic-product",
        "https://openstax.org/books/principles-economics-3e/pages/24-1-how-economists-define-and-compute-unemployment-rate",
        "https://openstax.org/books/principles-economics-3e/pages/28-1-how-government-borrowing-affects-investment-and-the-trade-balance",
    ],
    "openstax_stats_page": [
        "https://openstax.org/books/introductory-statistics/pages/1-introduction",
        "https://openstax.org/books/introductory-statistics/pages/2-1-stem-and-leaf-graphs-stemplots-line-graphs-and-bar-graphs",
        "https://openstax.org/books/introductory-statistics/pages/3-1-terminology",
        "https://openstax.org/books/introductory-statistics/pages/4-1-probability-distribution-function-pdf-for-a-discrete-random-variable",
        "https://openstax.org/books/introductory-statistics/pages/5-1-continuous-probability-functions",
        "https://openstax.org/books/introductory-statistics/pages/6-1-the-standard-normal-distribution",
        "https://openstax.org/books/introductory-statistics/pages/7-1-the-central-limit-theorem-for-sample-means-averages",
        "https://openstax.org/books/introductory-statistics/pages/8-1-a-single-population-mean-using-the-normal-distribution",
        "https://openstax.org/books/introductory-statistics/pages/9-1-null-and-alternative-hypotheses",
        "https://openstax.org/books/introductory-statistics/pages/10-1-comparing-two-independent-population-means",
        "https://openstax.org/books/introductory-statistics/pages/11-1-facts-about-the-chi-square-distribution",
        "https://openstax.org/books/introductory-statistics/pages/12-1-linear-equations",
        "https://openstax.org/books/introductory-statistics/pages/13-1-one-way-anova",
    ],
    "owasp_top10_2021": [
        "https://owasp.org/Top10/2021/",
        "https://owasp.org/Top10/A01_2021-Broken_Access_Control/",
        "https://owasp.org/Top10/A02_2021-Cryptographic_Failures/",
        "https://owasp.org/Top10/A03_2021-Injection/",
        "https://owasp.org/Top10/A04_2021-Insecure_Design/",
        "https://owasp.org/Top10/A05_2021-Security_Misconfiguration/",
        "https://owasp.org/Top10/A06_2021-Vulnerable_and_Outdated_Components/",
        "https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/",
        "https://owasp.org/Top10/A08_2021-Software_and_Data_Integrity_Failures/",
        "https://owasp.org/Top10/A09_2021-Security_Logging_and_Monitoring_Failures/",
        "https://owasp.org/Top10/A10_2021-Server-Side_Request_Forgery/",
        "https://raw.githubusercontent.com/OWASP/TopTen/master/2021/docs/A00_2021_Introduction.md",
        "https://raw.githubusercontent.com/OWASP/TopTen/master/2021/docs/A01_2021-Broken_Access_Control.md",
        "https://raw.githubusercontent.com/OWASP/TopTen/master/2021/docs/A02_2021-Cryptographic_Failures.md",
        "https://raw.githubusercontent.com/OWASP/TopTen/master/2021/docs/A03_2021-Injection.md",
        "https://raw.githubusercontent.com/OWASP/TopTen/master/2021/docs/A04_2021-Insecure_Design.md",
        "https://raw.githubusercontent.com/OWASP/TopTen/master/2021/docs/A05_2021-Security_Misconfiguration.md",
        "https://raw.githubusercontent.com/OWASP/TopTen/master/2021/docs/A06_2021-Vulnerable_and_Outdated_Components.md",
        "https://raw.githubusercontent.com/OWASP/TopTen/master/2021/docs/A07_2021-Identification_and_Authentication_Failures.md",
        "https://raw.githubusercontent.com/OWASP/TopTen/master/2021/docs/A08_2021-Software_and_Data_Integrity_Failures.md",
        "https://raw.githubusercontent.com/OWASP/TopTen/master/2021/docs/A09_2021-Security_Logging_and_Monitoring_Failures.md",
        "https://raw.githubusercontent.com/OWASP/TopTen/master/2021/docs/A10_2021-Server-Side_Request_Forgery.md",
    ],
    "owasp_asvs_raw": [
        "https://raw.githubusercontent.com/OWASP/ASVS/v4.0.3/4.0/en/0x00-Header.md",
        "https://raw.githubusercontent.com/OWASP/ASVS/v4.0.3/4.0/en/0x01-Frontispiece.md",
        "https://raw.githubusercontent.com/OWASP/ASVS/v4.0.3/4.0/en/0x02-Preface.md",
        "https://raw.githubusercontent.com/OWASP/ASVS/v4.0.3/4.0/en/0x03-Using-ASVS.md",
        "https://raw.githubusercontent.com/OWASP/ASVS/v4.0.3/4.0/en/0x04-Assessment-and-Certification.md",
        "https://raw.githubusercontent.com/OWASP/ASVS/v4.0.3/4.0/en/0x10-V1-Architecture.md",
        "https://raw.githubusercontent.com/OWASP/ASVS/v4.0.3/4.0/en/0x11-V2-Authentication.md",
        "https://raw.githubusercontent.com/OWASP/ASVS/v4.0.3/4.0/en/0x12-V3-Session-management.md",
        "https://raw.githubusercontent.com/OWASP/ASVS/v4.0.3/4.0/en/0x13-V4-Access-Control.md",
        "https://raw.githubusercontent.com/OWASP/ASVS/v4.0.3/4.0/en/0x14-V5-Validation-Sanitization-Encoding.md",
        "https://raw.githubusercontent.com/OWASP/ASVS/v4.0.3/4.0/en/0x15-V6-Cryptography.md",
        "https://raw.githubusercontent.com/OWASP/ASVS/v4.0.3/4.0/en/0x16-V7-Error-Logging.md",
        "https://raw.githubusercontent.com/OWASP/ASVS/v4.0.3/4.0/en/0x17-V8-Data-Protection.md",
        "https://raw.githubusercontent.com/OWASP/ASVS/v4.0.3/4.0/en/0x18-V9-Communications.md",
        "https://raw.githubusercontent.com/OWASP/ASVS/v4.0.3/4.0/en/0x19-V10-Malicious.md",
        "https://raw.githubusercontent.com/OWASP/ASVS/v4.0.3/4.0/en/0x20-V11-BusLogic.md",
        "https://raw.githubusercontent.com/OWASP/ASVS/v4.0.3/4.0/en/0x21-V12-Files-Resources.md",
        "https://raw.githubusercontent.com/OWASP/ASVS/v4.0.3/4.0/en/0x22-V13-API.md",
        "https://raw.githubusercontent.com/OWASP/ASVS/v4.0.3/4.0/en/0x23-V14-Config.md",
    ],
    "pandas_docs": [
        "https://pandas.pydata.org/docs/user_guide/10min.html",
        "https://pandas.pydata.org/docs/user_guide/dsintro.html",
        "https://pandas.pydata.org/docs/user_guide/basics.html",
        "https://pandas.pydata.org/docs/user_guide/io.html",
        "https://pandas.pydata.org/docs/user_guide/indexing.html",
        "https://pandas.pydata.org/docs/user_guide/advanced.html",
        "https://pandas.pydata.org/docs/user_guide/merge.html",
        "https://pandas.pydata.org/docs/user_guide/reshaping.html",
        "https://pandas.pydata.org/docs/user_guide/groupby.html",
        "https://pandas.pydata.org/docs/user_guide/timeseries.html",
        "https://pandas.pydata.org/docs/user_guide/categorical.html",
        "https://pandas.pydata.org/docs/user_guide/visualization.html",
        "https://pandas.pydata.org/docs/user_guide/missing_data.html",
        "https://pandas.pydata.org/docs/user_guide/enhancingperf.html",
        "https://pandas.pydata.org/docs/user_guide/scale.html",
        "https://pandas.pydata.org/docs/user_guide/style.html",
        "https://pandas.pydata.org/docs/user_guide/options.html",
        "https://pandas.pydata.org/docs/user_guide/text.html",
        "https://pandas.pydata.org/docs/user_guide/window.html",
        "https://pandas.pydata.org/docs/user_guide/cookbook.html",
    ],
    "hpbn": [
        "https://hpbn.co/",
        "https://hpbn.co/primer-on-latency-and-bandwidth/",
        "https://hpbn.co/building-blocks-of-tcp/",
        "https://hpbn.co/tls/",
        "https://hpbn.co/http-history/",
        "https://hpbn.co/http1x/",
        "https://hpbn.co/http2/",
        "https://hpbn.co/brief-history-of-http/",
        "https://hpbn.co/xhr-xhr2/",
        "https://hpbn.co/server-sent-events-sse/",
        "https://hpbn.co/websocket/",
        "https://hpbn.co/webrtc/",
        "https://hpbn.co/transport-layer-security-tls/",
        "https://hpbn.co/optimizing-for-mobile-networks/",
        "https://hpbn.co/performance-toolkit/",
        "https://hpbn.co/http2/",
        "https://hpbn.co/primer-on-web-performance/",
        "https://hpbn.co/http-over-udp-quic/",
        "https://hpbn.co/wifi/",
        "https://hpbn.co/mobile-networks/",
    ],
    "beej_net": ["https://beej.us/guide/bgnet/html/split/index.html"]
    + [f"https://beej.us/guide/bgnet/html/split/{p}.html" for p in [
        "intro", "system-calls-or-bust", "sockets", "ip-addresses-structs-and-data-munging",
        "internet-protocol-and-friends", "client-server-background", "a-simple-stream-server",
        "a-simple-stream-client", "datagram-sockets", "slightly-advanced-techniques",
        "network-programming-under-windows", "references", "common-questions", "more-references",
    ]],
    "beej_ipc": ["https://beej.us/guide/bgipc/html/split/index.html"]
    + [f"https://beej.us/guide/bgipc/html/split/{p}.html" for p in [
        "intro", "a-fork-primer", "signals", "pipes", "fifo", "file-locking",
        "message-queues", "semaphores", "shared-memory", "unix-sockets", "more-stuff",
    ]],
    "systemsapproach": [
        "https://book.systemsapproach.org/",
        "https://book.systemsapproach.org/foundation.html",
        "https://book.systemsapproach.org/direct.html",
        "https://book.systemsapproach.org/internetworking.html",
        "https://book.systemsapproach.org/scaling.html",
        "https://book.systemsapproach.org/e2e.html",
        "https://book.systemsapproach.org/congestion.html",
        "https://book.systemsapproach.org/data.html",
        "https://book.systemsapproach.org/security.html",
        "https://book.systemsapproach.org/applications.html",
    ],
    "use_the_index": [
        "https://use-the-index-luke.com/",
        "https://use-the-index-luke.com/sql/preface",
        "https://use-the-index-luke.com/sql/where-clause",
        "https://use-the-index-luke.com/sql/join",
        "https://use-the-index-luke.com/sql/sorting-grouping",
        "https://use-the-index-luke.com/sql/partial-results",
        "https://use-the-index-luke.com/sql/dml",
        "https://use-the-index-luke.com/sql/testing-and-scalability",
        "https://use-the-index-luke.com/sql/myth-directory",
    ],
    "uti_luke": [
        "https://use-the-index-luke.com/",
        "https://use-the-index-luke.com/sql/preface",
        "https://use-the-index-luke.com/sql/where-clause",
        "https://use-the-index-luke.com/sql/join",
        "https://use-the-index-luke.com/sql/sorting-grouping",
        "https://use-the-index-luke.com/sql/partial-results",
        "https://use-the-index-luke.com/sql/dml",
        "https://use-the-index-luke.com/sql/testing-and-scalability",
    ],
    "sqlite_docs": [
        "https://www.sqlite.org/docs.html",
        "https://www.sqlite.org/lang.html",
        "https://www.sqlite.org/lang_select.html",
        "https://www.sqlite.org/lang_createtable.html",
        "https://www.sqlite.org/lang_with.html",
        "https://www.sqlite.org/pragma.html",
        "https://www.sqlite.org/fts5.html",
        "https://www.sqlite.org/json1.html",
        "https://www.sqlite.org/queryplanner.html",
        "https://www.sqlite.org/optoverview.html",
        "https://www.sqlite.org/datatype3.html",
        "https://www.sqlite.org/foreignkeys.html",
        "https://www.sqlite.org/transaction.html",
        "https://www.sqlite.org/atomiccommit.html",
        "https://www.sqlite.org/wal.html",
        "https://www.sqlite.org/fileformat2.html",
        "https://www.sqlite.org/arch.html",
        "https://www.sqlite.org/cintro.html",
        "https://www.sqlite.org/c3ref/intro.html",
        "https://www.sqlite.org/cli.html",
    ],
    "sqlite_lang": [
        "https://www.sqlite.org/lang.html",
        "https://www.sqlite.org/lang_select.html",
        "https://www.sqlite.org/lang_insert.html",
        "https://www.sqlite.org/lang_update.html",
        "https://www.sqlite.org/lang_delete.html",
        "https://www.sqlite.org/lang_createtable.html",
        "https://www.sqlite.org/lang_altertable.html",
        "https://www.sqlite.org/lang_with.html",
        "https://www.sqlite.org/lang_corefunc.html",
        "https://www.sqlite.org/lang_aggfunc.html",
        "https://www.sqlite.org/lang_datefunc.html",
        "https://www.sqlite.org/lang_expr.html",
        "https://www.sqlite.org/lang_analyze.html",
        "https://www.sqlite.org/lang_attach.html",
        "https://www.sqlite.org/lang_transaction.html",
        "https://www.sqlite.org/lang_createindex.html",
        "https://www.sqlite.org/lang_createview.html",
        "https://www.sqlite.org/lang_createtrigger.html",
        "https://www.sqlite.org/lang_vacuum.html",
        "https://www.sqlite.org/lang_returning.html",
    ],
    "pg_docs": [
        "https://www.postgresql.org/docs/current/",
        "https://www.postgresql.org/docs/current/tutorial.html",
        "https://www.postgresql.org/docs/current/sql.html",
        "https://www.postgresql.org/docs/current/queries.html",
        "https://www.postgresql.org/docs/current/ddl.html",
        "https://www.postgresql.org/docs/current/dml.html",
        "https://www.postgresql.org/docs/current/indexes.html",
        "https://www.postgresql.org/docs/current/mvcc.html",
        "https://www.postgresql.org/docs/current/performance-tips.html",
        "https://www.postgresql.org/docs/current/runtime-config.html",
        "https://www.postgresql.org/docs/current/backup.html",
        "https://www.postgresql.org/docs/current/high-availability.html",
        "https://www.postgresql.org/docs/current/functions.html",
        "https://www.postgresql.org/docs/current/datatype.html",
        "https://www.postgresql.org/docs/current/admin.html",
        "https://www.postgresql.org/docs/current/client-interfaces.html",
        "https://www.postgresql.org/docs/current/server-programming.html",
        "https://www.postgresql.org/docs/current/parallel-query.html",
        "https://www.postgresql.org/docs/current/textsearch.html",
        "https://www.postgresql.org/docs/current/json.html",
    ],
    "pg_tutorial": [
        "https://www.postgresql.org/docs/current/tutorial.html",
        "https://www.postgresql.org/docs/current/tutorial-start.html",
        "https://www.postgresql.org/docs/current/tutorial-createdb.html",
        "https://www.postgresql.org/docs/current/tutorial-table.html",
        "https://www.postgresql.org/docs/current/tutorial-populate.html",
        "https://www.postgresql.org/docs/current/tutorial-select.html",
        "https://www.postgresql.org/docs/current/tutorial-join.html",
        "https://www.postgresql.org/docs/current/tutorial-agg.html",
        "https://www.postgresql.org/docs/current/tutorial-update.html",
        "https://www.postgresql.org/docs/current/tutorial-delete.html",
        "https://www.postgresql.org/docs/current/tutorial-transactions.html",
        "https://www.postgresql.org/docs/current/tutorial-window.html",
        "https://www.postgresql.org/docs/current/tutorial-inheritance.html",
        "https://www.postgresql.org/docs/current/tutorial-views.html",
        "https://www.postgresql.org/docs/current/tutorial-fk.html",
    ],
}


def heal_flags() -> int:
    """parca≥40 ama derin_yesil false olanları düzelt."""
    n = 0
    for dal in RAF.iterdir():
        if not (dal.is_dir() and dal.name[:1].isdigit()):
            continue
        path = dal / "katalog.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        changed = False
        for key, meta in (data.get("kaynaklar") or {}).items():
            p = int(meta.get("parca") or meta.get("parca_sayisi") or 0)
            if p >= MIN and not meta.get("derin_yesil"):
                meta["derin_yesil"] = True
                meta["tam_eser"] = True
                meta["ok"] = True
                changed = True
                n += 1
        if changed:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return n


def main() -> int:
    try:
        sys.stdout.reconfigure(line_buffering=True)  # type: ignore[attr-defined]
    except Exception:
        pass

    fixed = heal_flags()
    print("HEAL_FLAGS", fixed, flush=True)
    i.BODY_TARGET = MIN * 12000

    thin_path = Path(__file__).with_name("_thin_left.json")
    thin = json.loads(thin_path.read_text(encoding="utf-8")) if thin_path.is_file() else s.iter_thin()
    # yenile
    thin = s.iter_thin()
    print("THIN_PASS2", len(thin), flush=True)

    out = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "items": {},
        "kalin": [],
        "failed": [],
    }

    for n, item in enumerate(thin, 1):
        dal, key = item["dal"], item["key"]
        tag = f"{dal}/{key}"
        seed = (item.get("url") or "").strip() or s.SEED_OVERRIDE.get(key, "")
        urls = list(EXTRA.get(key) or [])
        if seed:
            urls = [seed] + urls
            urls.extend(s.expand_urls(seed))
        urls = i.uniq(urls, cap=i.URL_CAP)
        if not urls:
            print(f"NO_URL {n}/{len(thin)} {tag}", flush=True)
            out["failed"].append({"tag": tag, "reason": "no_url"})
            continue
        print(f"=== {n}/{len(thin)} {tag} urls={len(urls)}", flush=True)
        if any(u.lower().endswith(".pdf") for u in urls[:1]) or (seed or "").lower().endswith(".pdf"):
            pdf_url = next((u for u in urls if u.lower().endswith(".pdf")), seed)
            meta = s.thick_pdf(dal, key, item["baslik"], pdf_url)
        else:
            meta = i.thick(dal, key, item["baslik"], seed or urls[0], urls, 22)
        parca = int(meta.get("parca") or 0)
        out["items"][tag] = {"parca": parca, "pages": meta.get("html_pages")}
        if parca >= MIN:
            out["kalin"].append(tag)
            print(f"KALIN_OK {tag} {parca}", flush=True)
        else:
            out["failed"].append({"tag": tag, "parca": parca})
            print(f"STILL_THIN {tag} {parca}", flush=True)
        out["ts"] = datetime.now(timezone.utc).isoformat()
        REPORT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    left = s.iter_thin()
    out["thin_left"] = len(left)
    REPORT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("DONE_PASS2", "kalin", len(out["kalin"]), "thin_left", len(left), flush=True)
    return 0 if not left else 1


if __name__ == "__main__":
    raise SystemExit(main())
