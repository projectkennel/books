# 17. The settled artefact

What the compiler emits is the thing the runtime trusts, and it is shaped to make that trust cheap. A settled
policy is flat. The inheritance chain has been folded, the includes merged, the deltas applied, the source
signatures verified, and what remains carries no `template_base`, no `include`, and no delta operator, only the
final effective rules. The constructs the compiler resolved are not simplified in the settled form, they are
absent from it: there is no chain for the runtime to walk and no delta for it to apply, because the settled
document has no place to express either (`make-invalid-unrepresentable`). The body the runtime reads is a small
fixed set of fields, the kennel's name, the placeholders left for it to fill, the framework invariants the
compiler asserted, the resolved effective policy, and a provenance block, signed as a unit.

## 17.1 The canonical body and its signature

A signature is only as good as the agreement between signer and verifier on what bytes it covers, and the
settled policy fixes those bytes as its canonical form. The artefact is a TOML document, and its signature is an
SSHSIG, the same object the SSH toolchain signs and verifies. The SSHSIG is computed not over the body directly
but over a small fixed preimage that carries a SHA-512 of it: the namespace the signature is bound to and the
hash of a deterministic serialisation of the body in field order, with the signature envelope that sits beside
it in the document excluded from that serialisation. Signer and verifier derive the canonical bytes the same way
and hash them the same way, so they agree on the covered content to the byte, and that single SHA-512 is the one
place the body's bytes enter the signature, which makes the determinism of the canonical form the thing both
ends must reproduce exactly. There is no sorted-key or normalised-number canonicalisation of the kind a JSON
scheme would reach for, because both ends derive the same serialisation from the same struct and the schema
carries no floats to normalise. The form keeps its one deliberate property, that a sub-table which is empty is
omitted from the canonical bytes entirely, so a policy granting no SSH and no host sockets hashes to exactly the
bytes it would have before those tables existed in the schema. New optional surface can be added without
invalidating the signature of every policy that does not use it; the omission that keeps a signature stable
across schema growth now keeps the hash under it stable, and the SSHSIG with it.

```
settled_schema_version = 2
compiler_version = "0.5.0"

# the canonical body: the resolved sections the runtime enforces
[fs]
# ...
[exec]
# ...

[signature]            # excluded from the bytes it covers
algorithm = "sshsig"
signature = "-----BEGIN SSH SIGNATURE-----\n...\n-----END SSH SIGNATURE-----\n"
```

The header fixes the schema version the runtime must understand and the compiler that produced the body, and
the body is the resolved policy with every inheritance already folded in. The `[signature]` table sits in the
same document but outside the bytes it signs, so a verifier strips it, derives the canonical form of everything
else, and checks the SSHSIG against that.

## 17.2 What the runtime does with it

The runtime's whole interaction with a settled policy is short, and that brevity is the dividend the compiler
paid for. It deserialises the document, verifies the one SSHSIG against the trust store in-process, de-armouring
it, requiring its namespace and its embedded key to be the kennel-policy namespace and a trusted key, then
recomputing the canonical hash and rebuilding the preimage for a single ed25519 check, re-asserts the framework
invariants, substitutes the placeholders that could only be filled at spawn,
and builds the kernel objects. None of the template machinery is linked on this path: there is no chain to
walk, no fragment to fetch, no delta to apply, no source signature to chase, and no `ssh-keygen` to exec,
because all of that produced the
artefact already and left its result flat. The placeholders it fills are the ones intrinsically per-spawn, the
kennel's runtime context, the invoking user, the generated name and home, recorded in the artefact as a
deferred list so the runtime knows exactly which it owns. They are deferred because they cannot be otherwise: a
settled artefact is distributed to a fleet unchanged, the same signed bytes on every machine, so a per-user or
per-instance value has no single answer at compile and can only be filled where the kennel starts. It
substitutes those and no others, and a settled
policy that still carries an unsubstituted placeholder the deferred list does not name is refused rather than
spawned, because such a placeholder is a compiler defect and enforcing a policy with a hole in it is worse than
refusing one (`refuse-to-start`).

## 17.3 A signature is not a safety proof

A valid signature on a settled policy means a key the operator trusts vouched for the artefact. It does not mean
the artefact upholds the structural guarantees that define what a kennel is, because those guarantees are the
framework's and not the signer's, and a trusted key can sign a policy that quietly drops one. So the runtime
re-asserts the framework invariants against the effective rules as a final gate, regardless of the signature: a
climb-back bar that must be set, the setuid and setgid denials, the mandatory home shim, the cloud-metadata
deny that no egress may remove, the process-isolation namespace, the proxy-only egress. These are a handful of
cheap structural checks, and they hold whoever signed the artefact and however it arrived, by compile on the
machine or by push from a fleet controller. A validly signed settled policy that violates one is refused at
spawn. The list of invariants the compiler asserted travels in the artefact, but it travels as an audit record
of what compile checked, never as a substitute for the runtime check; the runtime re-runs them regardless of
what that field claims. This is the one place the runtime deliberately repeats the compiler's work, and it earns
its keep, because it means no policy, whatever key signed it and whatever path it took, can disable the
protections that make a kennel a kennel.

## 17.4 Provenance and attestation

The artefact describes itself. A provenance block records every input that produced it: the compiler version,
the schema version, the threat-catalogue version the templates were authored against, and each resolved
template and fragment by name, version, signing key, and signature. Because the signature commits to those bytes
through their hash, established in the previous chapter, that last record is exact: a reader can see precisely which signed source
artefacts, at which versions and which bytes, were composed into the result, and can do so without any of those
sources present, reading only the settled file. Two settled policies can be diffed directly, and their
provenance compared revision to revision, without resolving anything.

That self-description is also what makes the artefact attestable. Because the enforced policy is the signed
policy, with no live resolution between the signature and the enforcement that could let the two diverge, the
artefact's signature is its identity. An organisation that compiles centrally and pushes only signed settled
policies can have a workstation demonstrate that it runs an approved revision, because the bytes it enforces are
the bytes the organisation signed and the signature proves it. The runtime trust surface on that workstation is
one signature check against a pinned key, the resolution machinery and the templates and the lockfile all left
behind on the compile infrastructure, and what arrives is a flat, signed, self-describing artefact whose
identity is exactly the policy it enforces. The keys that make that signature mean something are what the next
chapter takes up.
