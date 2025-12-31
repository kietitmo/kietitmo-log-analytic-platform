log-analytics-platform/
├── README.md
├── docker-compose.yml
│
├── ingest-service/        # FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── schema.py
│   │   ├── ingest.py
│   │   └── stream.py
│   └── requirements.txt
│
├── aggregator/            # Rust (CORE – nặng thật)
│   ├── Cargo.toml
│   └── src/
│       ├── main.rs
│       ├── log_event.rs
│       ├── window.rs
│       ├── aggregator.rs
│       └── sink.rs
│
├── query-service/         # Node.js (BFF)
│   ├── src/
│   │   └── index.ts
│   └── package.json
│
├── dashboard/             # React
│   ├── src/
│   │   └── App.tsx
│   └── package.json
│
└── log-generator/
    └── generate.py
