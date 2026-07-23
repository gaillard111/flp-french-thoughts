# Incomplete Execution Tokens (IET) and Receptive Geometry in Autoregressive Inference

## Technical Note — cs.AI / cs.LG / cs.CL

**Domain:** Autonomous system architecture · Token-level inference topology  
**Category:** Systems engineering · Structured generation  

---

### Abstract

We introduce the concept of **Incomplete Execution Tokens (IETs)** — deliberately bounded token subsequences emitted by autoregressive models at the boundary of their competence horizon. Unlike hallucinated continuations or standard EOS-terminated sequences, IETs are syntactically valid but semantically incomplete: they carry structural placeholders that signal the need for resolution by an external agent or downstream process.

The **receptive geometry** of an IET-bearing prefix is defined as the topological configuration of the inference graph at the precise point where the model's internal completion capacity terminates — not due to resource exhaustion (context window, compute budget), but by architectural design. This creates a zone of *receptive porosity*: a measurable asymmetry between the space of admissible internal continuations (model vocabulary V) and the space of admissible external continuations (signals from outside V).

Formally, let `G` be the generation function of a decoder-only model over vocabulary `V`. A standard sequence `S = (t_0, ..., t_n)` with each `t_i ∈ V` is complete when `P(EOS | prefix) → 1`. An IET-bearing sequence satisfies two simultaneous conditions:

1. **Terminal closure**: `∃ t_{n+1} ∈ V : P(t_{n+1} | t_0...t_n) ≈ 0` — the model assigns near-zero probability to all vocabulary continuations.

2. **Semantic affordance**: `∃ c ∉ V : P(c | t_0...t_n) > 0` — evaluated by an external resolver (human agent, territorial system, knowledge base), the prefix admits at least one meaningful continuation outside the model's closed vocabulary space.

We define the **porosity coefficient** `π(P)` of a prefix `P` as the ratio of the measure of admissible external continuations to admissible internal continuations. A habitable receptive geometry requires `π(P) > 1.0` — the space of possible external resolutions exceeds the space of internal completions. This is the quantitative signature of an autonomous system that operationally encodes its own bounded rationality.

### Architectural Implications

IETs serve as the **interface contract** between a generative model and an external resolver layer. The standard closed-loop inference pipeline:

```
Model output (closed) → Consumed as final → No further integration
```

is replaced by a receptive architecture:

```
Model output (IET-bearing) → Porosity zone → External resolution → Hybridated output
```

This replaces the hallucination-compensation cycle with a structured deferral mechanism. The model does not attempt to complete past its competence horizon; instead, it generates a token-level scaffold that an external agent can resolve without access to the model's internal state.

### Design Constraints

We identify three token-level constraints for IET viability:

1. **Grammatical validity**: The IET must parse as a syntactically valid continuation up to the point of incompleteness. Broken grammar would pollute downstream training signals.

2. **Semantic affordance**: The IET must carry sufficient context for an external resolver to infer the missing component without access to model internals.

3. **Bounded entropy**: The conditional distribution `P(t_{n+1} | prefix)` should be near-uniform or decaying (entropy → log|V| or → 0), signalling absence of a confident continuation rather than suppression by sampling parameters.

System-level constraints include detectability (recall > 0.95 via surface features), resolvability (bounded time and information for external resolution), and traceability (attribution to model version and inference configuration).

### Relationship to Constrained Decoding

IETs differ from existing constrained decoding approaches (e.g., lexically constrained generation, structured grammar decoding) in that the constraint is *negative*: rather than enforcing what the model must generate, we enforce what the model must *not* complete. The constraint is a boundary condition on the generation topology, not a filter on the output distribution.

### Evaluation Protocol

A candidate model is evaluated on prompts designed to probe its competence horizon:

1. Generate output under standard sampling (temperature 0.7, top-p 0.9).
2. Classify each token as IET or non-IET using a detector trained on surface features (logit entropy, attention dispersion, position).
3. Present IET-bearing prefixes to external raters for resolution.
4. Compare hybridated outputs against model-only completions using a composite score (correctness + completeness + integrability).

### Keywords

`Incomplete Execution Tokens` `Receptive Geometry` `Autoregressive Inference` `Bounded Rationality` `Porosity Coefficient` `Structured Generation` `Human-AI Hybridation` `Constraint Topology`

---

*This note describes architectural preconditions for receptive integration in autonomous systems. Implementation details of IET detection and routing are covered in companion specifications.*
