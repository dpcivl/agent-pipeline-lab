# 메시지 흐름

```mermaid
sequenceDiagram
    participant Human as human
    participant Main as main
    participant implementer as implementer
    participant test-writer as test-writer
    participant tester as tester
    participant reviewer as reviewer
    participant qa as qa
    participant security as security
    participant doc-keeper as doc-keeper
    Human->>Main: #1 H-INPUT (~31 tok)
    Main->>implementer: #2 T-TASK (~623 tok)
    Main->>test-writer: #3 T-TASK (~539 tok)
    implementer-->>Main: #4 R-DONE (~1204 tok)
    test-writer-->>Main: #5 R-DONE (~1748 tok)
    Main->>tester: #6 T-TASK (~192 tok)
    tester-->>Main: #7 R-DONE (~76 tok)
    Main->>reviewer: #8 T-TASK (~291 tok)
    Main->>qa: #9 T-TASK (~299 tok)
    Main->>security: #10 T-TASK (~296 tok)
    reviewer-->>Main: #11 R-FINDINGS (~2245 tok)
    security-->>Main: #12 R-FINDINGS (~2703 tok)
    qa-->>Main: #13 R-FINDINGS (~2073 tok)
    Main->>implementer: #14 T-FIX (~393 tok)
    Main->>test-writer: #15 T-FIX (~306 tok)
    implementer-->>Main: #16 R-DONE (~486 tok)
    test-writer-->>Main: #17 R-DONE (~618 tok)
    Main->>tester: #18 T-RERUN (~110 tok)
    tester-->>Main: #19 R-DONE (~172 tok)
    Main->>reviewer: #20 T-REREVIEW (~210 tok)
    Main->>qa: #21 T-REREVIEW (~238 tok)
    Main->>security: #22 T-REREVIEW (~140 tok)
    reviewer-->>Main: #23 R-FINDINGS (~832 tok)
    qa-->>Main: #24 R-FINDINGS (~830 tok)
    security-->>Main: #25 R-FINDINGS (~822 tok)
    Main->>doc-keeper: #26 T-TASK (~364 tok)
    doc-keeper-->>Main: #27 R-DONE (~395 tok)
```
