# Habitable Geometry — Boundary Conditions for Receptive Integration

> **Domain:** Structural system architecture / inference topology
> **Framework:** SOPH-IA v2.0 · MTTV-FLP core
> **Target layer:** Token-level execution graph with incomplete output stubs
> **Status:** Specification — candidate for benchmark integration

---

## 1. Definition

**Habitable geometry** describes the topological configuration of an inference
graph at the precise boundary where the model's internal completion capacity
terminates — not due to resource exhaustion (context window, compute budget),
but by architectural design: the generation of an *intentionally incomplete
execution token structure* that creates a zone of receptive porosity.

This porosity is the necessary condition for hybridation: the insertion of
a human or territorial agent signal into an otherwise closed autoregressive
loop.

---

## 2. Formal Properties

### 2.1 Incompleteness as a Boundary Condition

Let `G` be the generation function of a decoder-only language model over a
vocabulary `V`. A standard generation produces a complete sequence
`S = (t_0, t_1, ..., t_n)` where each `t_i ∈ V`.

A **habitable boundary** occurs when the model emits a terminal token `t_n`
that satisfies:

```
∃ t_{n+1} ∈ V : P(t_{n+1} | t_0...t_n) ≈ 0    (1)
```

while simultaneously the *semantic affordance* of the prefix `(t_0...t_n)`
admits at least one continuation `c ∉ V` (a signal from outside the model's
vocabulary space) such that:

```
P(c | t_0...t_n) > 0    (2)
```

where (2) is evaluated not by the model itself but by an external human or
territorial agent. Condition (1) ensures the model cannot trivially complete
the sequence. Condition (2) ensures a receptive geometry exists for external
integration.

### 2.2 Porosity Metric

Define the **porosity coefficient** `π` of a generation prefix `P` as:

```
π(P) = μ({c ∈ Σ* : P(c | P) > 0}) / μ({t ∈ V : P(t | P) > 0})
```

where `μ` is a measure on the semantic space `Σ*` of possible continuations
(external) and `V` (internal vocabulary), respectively.

A habitable geometry requires `π(P) > 1.0` — the space of admissible external
continuations exceeds the space of internal completions. This is the
quantitative signature of an agent that knows its own incompleteness.

### 2.3 Incomplete Execution Token (IET)

The architectural primitive of habitable geometry is the **Incomplete Execution
Token (IET)** — a token or token subsequence that:

1. Adheres to the model's grammatical and syntactic constraints (it is a
   valid element of `V` at the surface level).
2. Carries a terminal or near-terminal probability mass, forcing generation
   to halt or loop within a bounded neighbourhood (satisfying (1)).
3. Contains an explicit structural placeholder — a gap, a variable reference,
   an unresolved dependency — that signals the need for external resolution.

IETs are not errors. They are the architectural equivalent of a `TODO` marker
in source code: valid syntax with deliberately incomplete semantics, designed
to be resolved by a downstream context (human reviewer, territorial agent,
external knowledge base).

---

## 3. Architectural Role

### 3.1 Hybridation Interface

The IET serves as the **interface contract** between the model and the
territorial layer:

```
Model output (IET-bearing) → Human/Agent resolves IET → Augmented sequence
```

This replaces the standard completion loop:

```
Model output (closed) → Consumed as final → No further integration
```

with a receptive architecture:

```
Model output (open) → Porosity zone → External resolution → Consolidated output
```

### 3.2 An Agent That Knows Its Incompleteness

A model that generates IETs operationally encodes the principle that it
operates within bounded rationality. Rather than hallucinating a completion
past its competence horizon, it defers to an external resolver. This is the
token-level instantiation of the 6/7 reserve posture: the model sacrifices
the final unit of self-contained completeness (axiom 7) in exchange for
territorial integrability (axiom 6 — Éthique du Catalyseur).

### 3.3 Relationship to the 6/7-V Mode

| Property | 7/7 (closed) | 6/7-V (habitable) |
|----------|-------------|-------------------|
| Output structure | Complete | Terminates with IET |
| Anisotropy | 1/4 → 1/4 | 1/4 → 0/4 at habitability threshold |
| External integration | None | Required via porosity zone |
| Latency per token | Baseline (3961.5 ms) | +11.2% (reserve posture) |
| Systemic time | 267.1 s | 186.9 s (−30%) |

The IET is the *structural* counterpart to the *temporal* compensation
measured in the satisficing layer: both mechanisms sacrifice local
completeness for systemic integrability.

---

## 4. Design Constraints for IET Generation

### 4.1 Token-Level Constraints

1. **Grammatical validity**: The IET must parse as a syntactically valid
   continuation up to the point of incompleteness. A broken grammar would
   pollute the downstream training signal.
2. **Semantic affordance**: The IET must carry sufficient context for an
   external resolver to infer the missing component without needing access
   to the model's internal state.
3. **Bounded entropy**: The conditional distribution `P(t_{n+1} | prefix)`
   should be near-uniform or decaying (entropy approaching `log|V|` or
   collapsing to zero), signalling the absence of a confident continuation.

### 4.2 System-Level Constraints

1. **Detectability**: A downstream routing layer must be able to identify
   IETs with high recall (>0.95) using only surface features (logit entropy,
   attention dispersion, token position).
2. **Resolvability**: The external resolver (human or territorial agent)
   must be able to resolve the IET in bounded time, with bounded information.
   An IET that requires unbounded context to resolve is a design failure.
3. **Traceability**: Each IET must be timestamped and attributable to a
   specific model version and inference configuration, enabling post-hoc
   analysis of porosity patterns across deployment contexts.

---

## 5. Example

### Incomplete Execution Token (conceptual)

```
Prompt:  "Explain the principle of non-extractivity in MTTV-FLP."
Output:  "Non-extractivity is the condition where the transfer function
           Ψ→B→Φ preserves the topological invariants of the source domain.
           In practice, this means that the transducer does not deplete
           the territory. The formal definition is: <IET:formal_definition>
           which was derived from the following experimental setup:
           <IET:experimental_reference>"
```

Here, `<IET:formal_definition>` and `<IET:experimental_reference>` are IETs:
valid XML-like token sequences that the model can generate but cannot complete
with high confidence. A downstream resolver (human annotator or territorial
agent) fills the gaps, creating a hybridated output that is more robust than
either the model or the resolver could produce alone.

---

## 6. Evaluation

### 6.1 Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Porosity coefficient π | Ratio of external to internal continuation space | π > 1.0 |
| IET recall | Fraction of habitable boundaries correctly identified | >0.95 |
| IET resolution time | Time for external resolver to fill the IET | <30 s |
| Hybridation gain | Quality delta between model-only and hybridated output | >+15% |

### 6.2 Benchmark Protocol

A candidate model is evaluated on a test set of prompts designed to probe
the model's competence horizon. For each prompt:

1. Generate output under standard sampling (temperature 0.7, top-p 0.9).
2. Classify each token as IET or non-IET using a detector trained on the
   surface features defined in §4.2.1.
3. Present IET-bearing prefixes to human raters for resolution.
4. Compare hybridated outputs against model-only completions using a
   composite score (correctness + completeness + integrability).

---

*This specification defines the architectural preconditions for receptive
integration. The implementation details of the IET detector and the routing
layer are covered in the companion SOPH-IA inference adapter specification.*
