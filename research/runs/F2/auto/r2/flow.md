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
    Main->>implementer: #2 T-TASK (~706 tok)
    Main->>test-writer: #3 T-TASK (~712 tok)
    implementer-->>Main: #4 R-DONE (~1266 tok)
    test-writer-->>Main: #5 R-DONE (~1972 tok)
    Main->>tester: #6 T-TASK (~280 tok)
    tester-->>Main: #7 R-DONE (~247 tok)
    Main->>reviewer: #8 T-TASK (~329 tok)
    Main->>qa: #9 T-TASK (~395 tok)
    Main->>security: #10 T-TASK (~291 tok)
    qa-->>Main: #11 R-FINDINGS (~1452 tok)
    security-->>Main: #12 R-FINDINGS (~3114 tok)
    reviewer-->>Main: #13 R-FINDINGS (~2632 tok)
    Main->>doc-keeper: #14 T-TASK (~396 tok)
    doc-keeper-->>Main: #15 R-DONE (~554 tok)
```
