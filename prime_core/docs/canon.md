# prime_core canon (v0.1.0)

These eleven decisions are frozen for v0.1.0. Implementation must satisfy
them or canon must be revised first. Subsequent revisions bump to v0.1.1+
rather than mutating the v0.1.0 freeze.

## C1. PCNA topology

61 total seeds = 1 global router + 7 meta routers + 4 sentinels + 49
compute seeds. The 53-node core compute ring = 4 sentinels + 49 compute
seeds. Global router and meta routers are off-ring coordination structure.

## C2. PCNA coherence weights

Must sum to `1.00`:

| Channel    | Weight |
|------------|--------|
| Phi        | 0.30   |
| Theta      | 0.20   |
| Psi        | 0.15   |
| Omega      | 0.15   |
| Memory-L   | 0.12   |
| Memory-S   | 0.08   |

## C3. Greek-letter scale rule

Each Greek letter denotes one scale-recurring role:

- **Phi**   — cognitive substrate (PCNA ring) / coherence-heartbeat (architecture)
- **Psi**   — self-model (PCNA ring) / self-state (architecture)
- **Omega** — autonomy (PCNA ring) / preservation (architecture); unified role is *preservation of autonomy across time*
- **Theta** — microkernel gate (PCNA ring) / boundary (architecture)
- **Sigma** — filesystem observer (PCNA ring) / integration (architecture)

## C4. PTCA tensor shape

`53 × 9 × 8 × 7` (node × sentinel × phase × slot) = `26,796` cells. 53 nodes
indexed by the first 53 primes.

## C5. PTCA sentinel channels

S1 Provenance, S2 Policy, S3 Bounds, S4 Approval, S5 Context, S6 Identity,
S7 Memory, S8 Risk, S9 Audit.

## C6. PTCA exchange scoring

```
score = DELTA × (α·s1 + β·s2 + γ·s3 + γ·s5 + α·s8 + bonus)
DELTA = 1, α = 0.10, β = 0.20, γ = 0.10
```

Sentinel inputs are normalised to `[0, 1]` before scoring. `bonus` is an
explicit route-level adjustment, not implicit fill. The score is an
operational score, not a probability.

## C7. PCEA mechanism

The core PCEA is the bijective base-p cipher over the 53-prime circle.
AES/HKDF/Shamir is *not* the core; if retained, it lives in
`prime_core/pcea/envelope.py` as optional transport. v0.1.0 does not
require the envelope.

## C8. The three 53s are one constant

`PRIME_CORE_SIZE = 53` is defined once at top level and referenced by all
three layers: PCNA core ring membership, PTCA prime-node count, PCEA
prime-circle schedule length. Changing 53 is a whole-quartet change.

## C9. PCTA composition

One PCTA circle = 7 PCNA tensor members. The flat tensor of a circle is
the ordered concatenation of its seven members.

## C10. Sigma injection bound

Sigma is outside the coherence-weight vector and does not receive its own
score weight. Sigma may inject coherence into Psi, but the injection must
satisfy `0.0 <= sigma_injection_strength <= SIGMA_PSI_MAX`.

## C11. Audit asymmetry is canonical

- Phi / Psi / Omega — PTCA-seed audit.
- Theta — PCTA-circle audit.
- Memory-L / Memory-S — memory-state audit (hub averages, flush counts, promotion behavior).

Not an oversight — three different audit kinds for three different ring
roles.
