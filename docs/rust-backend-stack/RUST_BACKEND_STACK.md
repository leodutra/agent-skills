# Rust Backend Stack Specification (2026)

## Purpose

This specification defines the default technology and architectural choices for Rust backend systems.

The goals are:

* Correctness
* Maintainability
* Explicitness
* Strong compile-time guarantees
* AI-assisted development
* Operational simplicity
* Long-term sustainability
* Minimal framework magic
* High observability
* Production readiness

The philosophy is:

```text
Prefer explicitness over magic.

Prefer compile-time guarantees over runtime validation.

Prefer standard libraries over external dependencies.

Prefer boring, proven technology over novelty.

Prefer SQL over query DSLs.

Prefer feature-oriented architecture over layer-oriented architecture.

Prefer observability from day one.
```

---

# Language & Toolchain

## Rust

Use:

```text
Rust Stable
Edition 2024
```

Reasoning:

* Largest ecosystem compatibility
* Lowest maintenance burden
* Strongest tooling support

---

## Toolchain Management

Use:

```text
rustup
```

Reasoning:

* Official toolchain manager
* Standard across ecosystem

---

## IDE

Use:

```text
VS Code
rust-analyzer
```

Reasoning:

* Best ecosystem support
* Strong AI integrations
* Excellent debugging experience

---

## Build Cache

Use:

```text
sccache
```

Reasoning:

* Faster local builds
* Faster CI builds

---

# Async Runtime

## Runtime

Use:

```text
Tokio
```

Reasoning:

* Ecosystem standard
* Most mature
* Largest integration surface
* Production proven

---

## CPU-bound Work

Use:

```text
rayon
tokio::spawn_blocking
```

Reasoning:

Async runtimes are not CPU schedulers.

Use Rayon for parallel CPU work.

---

# Web Layer

## HTTP Framework

Use:

```text
Axum
```

Reasoning:

* Built on Hyper and Tower
* Minimal abstraction
* Explicit routing
* Excellent ecosystem support

---

## Middleware

Use:

```text
Tower
```

Reasoning:

* Standard middleware ecosystem
* Composable
* Well understood

---

## HTTP Engine

Use:

```text
Hyper
```

Reasoning:

Foundation of the Rust web ecosystem.

---

# Database

## Database

Use:

```text
PostgreSQL
```

Reasoning:

Best general-purpose relational database.

Provides:

* ACID guarantees
* JSON support
* Full-text search
* Extensions
* Mature ecosystem

---

## Database Access

Use:

```text
SQLx
```

Reasoning:

Provides:

* Compile-time query validation
* Compile-time type validation
* Real SQL
* Excellent AI compatibility
* Easier onboarding
* Better support for advanced PostgreSQL features

Tradeoff:

Diesel provides stronger type-level guarantees but SQLx offers better overall maintainability and SQL ergonomics.

---

## Migrations

Use:

```text
SQLx migrations
```

Rules:

* Every migration must be reviewed.
* Every migration must have a rollback strategy.
* Avoid destructive migrations.
* Prefer additive schema evolution.

---

# Serialization

Use:

```text
Serde
serde_json
```

Reasoning:

Ecosystem standard.

---

# Validation

Use:

```text
validator
```

Reasoning:

Simple declarative validation.

---

# Error Handling

## Domain Errors

Use:

```text
thiserror
```

Pattern:

```rust
#[derive(thiserror::Error)]
pub enum Error {}
```

Reasoning:

Typed errors improve correctness.

---

## Application Errors

Use:

```text
Custom error enums
```

Avoid:

```text
String errors
```

---

## Internal Tooling

Use:

```text
anyhow
```

Reasoning:

Fast iteration for tools and infrastructure code.

---

# Configuration

Use:

```text
config-rs
Environment Variables
```

Rules:

* Secrets must not live in source control.
* Secrets must come from environment or secret managers.

---

# Time

Use:

```text
time
```

Reasoning:

Modern API.

Avoid new usage of:

```text
chrono
```

unless required by dependencies.

---

# IDs

## External IDs

Use:

```text
UUID v7
```

Reasoning:

Time-ordered
Better indexing characteristics

---

## Domain IDs

Use:

```rust
pub struct UserId(Uuid);
```

Reasoning:

Prevent identifier confusion.

---

# Money

Use:

```text
rust_decimal
```

Never use:

```text
f32
f64
```

for financial values.

---

# Collections

## Default Collections

Use:

```text
Vec
HashMap
HashSet
BTreeMap
BTreeSet
```

from std.

Reasoning:

Most stable and battle-tested.

---

## Ordered Maps

Use:

```text
IndexMap
```

when deterministic ordering matters.

---

## Fast Hashing

Use:

```text
rustc-hash
```

only after profiling.

---

## Concurrent Maps

Use:

```text
DashMap
```

only when contention requires it.

---

# Synchronization

## Preferred Locks

Use:

```text
parking_lot
```

Reasoning:

Better performance and ergonomics than std synchronization primitives.

---

# Global Initialization

## Lazy Initialization

Use:

```text
LazyLock
```

Reasoning:

Standard library solution.

Example use cases:

* Static lookup tables
* Regexes
* Metrics

---

## One-Time Initialization

Use:

```text
OnceLock
```

Reasoning:

Explicit initialization.

Example use cases:

* Application container
* Runtime configuration

---

## Legacy

Avoid:

```text
lazy_static
```

unless maintaining older code.

---

# Security

## Password Hashing

Use:

```text
Argon2
```

Reasoning:

Current industry standard.

---

## TLS

Use:

```text
rustls
```

Reasoning:

Modern Rust-native TLS.

---

## Encryption

Use:

```text
ring
```

when cryptographic primitives are required.

---

# Authentication

Default:

```text
Secure Session Cookies
```

Avoid JWT unless:

* Multiple services require token propagation
* Stateless authentication is required

---

# Authorization

Use:

```text
Policy-based authorization
```

Example:

```rust
pub trait Policy {
    fn authorize(&self, actor: &Actor) -> bool;
}
```

Reasoning:

Authorization rules remain explicit and testable.

---

# Observability

## Logging

Use:

```text
tracing
tracing-subscriber
```

Reasoning:

Structured logging from day one.

---

## Metrics

Use:

```text
Prometheus
```

---

## Dashboards

Use:

```text
Grafana
```

---

## Distributed Tracing

Use:

```text
OpenTelemetry
```

---

# Networking

## HTTP Client

Use:

```text
reqwest
```

---

## gRPC

Use:

```text
tonic
```

---

## WebSockets

Use:

```text
Axum WebSocket support
```

---

# Caching

## Local Cache

Use:

```text
Moka
```

---

## Distributed Cache

Use:

```text
Redis
```

Rule:

Do not introduce Redis until a real caching requirement exists.

---

# Background Processing

## In-process Jobs

Use:

```text
Tokio Tasks
```

---

## Distributed Jobs

Use:

```text
Redis-backed queue
```

only when needed.

---

# Search

Default:

```text
PostgreSQL Full Text Search
```

Introduce dedicated search engines only when PostgreSQL is no longer sufficient.

---

# Testing

## Unit Tests

Use:

```text
Rust built-in test framework
```

---

## Integration Tests

Use:

```text
tests/
```

---

## Property Tests

Use:

```text
proptest
```

Reasoning:

Property tests often find bugs traditional tests miss.

---

## HTTP Tests

Use:

```text
reqwest
```

---

## Test Strategy

Prefer:

```text
Real implementations
Fakes
Builders
```

Avoid:

```text
Heavy mocking
```

---

## Database Testing

Prefer:

```text
Ephemeral PostgreSQL
Testcontainers
```

over mocks.

---

# Benchmarking

Use:

```text
criterion
```

Reasoning:

Reliable benchmark methodology.

---

# Profiling

Use:

```text
cargo-flamegraph
pprof
```

Reasoning:

Profile before optimizing.

---

# Static Analysis

## Formatting

Use:

```text
rustfmt
```

---

## Linting

Use:

```text
clippy
```

Warnings should generally be treated as errors.

---

## Security Auditing

Use:

```text
cargo-audit
```

---

## Dependency Policy

Use:

```text
cargo-deny
```

Reasoning:

Supply-chain governance.

---

# API Documentation

Use:

```text
utoipa
```

Reasoning:

OpenAPI generation.

---

# Internal Documentation

Use:

```text
rustdoc
```

for public interfaces.

---

# Architecture Decision Records

Maintain:

```text
docs/adr/
```

Reasoning:

Major architectural decisions should be recorded and justified.

---

# Architecture

## Structure

Use feature-oriented organization.

Example:

```text
orders/
├── create-order/
├── cancel-order/
├── refund-order/
├── policies/
├── newtypes/
├── errors.rs
└── mod.rs
```

Avoid:

```text
controllers/
services/
repositories/
entities/
```

Reasoning:

Features change together.
Layers do not.

Feature-oriented architecture scales better.

---

# Deployment

## Containerization

Use:

```text
Docker
```

---

## Base Images

Use:

```text
Distroless Images
```

where possible.

---

## CI/CD

Use:

```text
GitHub Actions
```

---

## Orchestration

Use:

```text
Kubernetes
```

only when operational requirements justify it.

Do not introduce Kubernetes prematurely.

---

# Dependency Principles

Before adding a dependency:

Ask:

```text
Can std solve this?

Can existing dependencies solve this?

Is this dependency maintained?

Does it reduce complexity?

Will it still be useful in five years?
```

---

# Final Stack Summary

```text
Rust Stable (2024)

Tokio
Axum
Tower
Hyper

PostgreSQL
SQLx

Serde
Validator

ThisError
Anyhow

Tracing
OpenTelemetry
Prometheus
Grafana

Argon2
Rustls

Reqwest
Tonic

Time
UUID v7
Rust Decimal

IndexMap
Parking Lot
Rayon

LazyLock
OnceLock

Proptest
Criterion

Cargo Audit
Cargo Deny

Utoipa

Docker
GitHub Actions
Kubernetes (when justified)
```

Core philosophy:

```text
Explicit > Magic

Compile-time > Runtime

SQL > Query DSL

Features > Layers

Observability by Default

Profile Before Optimizing

Prefer Boring Technology
```
