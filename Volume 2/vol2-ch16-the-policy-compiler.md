# 16. The policy compiler

The chapters before this one described what the runtime enforces. What the operator writes is not that. A
written policy names a template to extend, pulls in shared fragments, carries deltas that add and remove
grants, and leaves variables for the runtime to fill, none of which the enforcement path should ever see. A
naive system would resolve all of it on every spawn: parse the leaf, walk the inheritance chain, verify each
template's and fragment's signature, check the lockfile, merge the includes, apply the deltas, validate the
invariants, substitute the variables, and only then have something to enforce. That is a great deal of complex,
fallible, security-critical code, and running it on the hot path of every `kennel run` is the wrong place for
it. Kennel does not work that way. It compiles.

## 16.1 The authored artefact and the enforced artefact

The systems Kennel is measured against already draw this line. AppArmor authors a text profile and a parser
compiles it into a binary policy loaded into the kernel, with the text never consulted at enforcement; SELinux
compiles a monolithic binary policy from source modules. The authored artefact and the enforced artefact are
different things, and the compile step is where the expensive and fallible work happens, once and deliberately,
rather than on every enforcement. `kennel compile` takes a leaf policy and produces a settled policy: a flat,
fully resolved document in which the inheritance chain has been folded, the includes merged, the deltas applied,
and every source signature and lockfile pin verified. The settled policy carries no `template_base`, no
`include`, and no delta operators, only the final effective rules, signed as a unit by the compiling authority.
The division of labour is the point. The complex code runs at compile time, where the operator can review the
output before anything runs; the spawn path links none of the template machinery and consumes an artefact whose
shape is fixed and simple.

## 16.2 The fold

Resolution is a fold down a chain. The compiler walks a leaf's `template_base` to the root template, the minimal
`base-confined` that every confined template extends, and folds the chain root-first into one effective policy
with no base left to resolve. Composition follows the model an SSH client uses for its configuration, and every
field falls into exactly one of three classes.

A **scalar** takes the most-derived value that sets it and inherits where a level is silent. Object sub-tables
merge shallowly, field by field, the child overriding.

A **list-shaped grant** composes uniformly, whatever it grants: a bare assignment *sets* (a child's non-empty
list replaces the inherited one; an empty or absent one inherits), and the explicit `add`/`remove` deltas
*increment* that set-or-inherit base. This one rule covers the path lists (`fs.read`, `fs.write`, `fs.deny`,
`exec.allow`), the typed grant lists (`unix.allow`, `net.proxy.allow`, `net.proxy.deny.policy`, `net.udp.allow`,
the `net.bpf` ACLs, `ssh.destinations`, `fs.dev.passthrough`), the mesh demand side (`consumes`), the spawn
target set (`spawn.allow`), and the supplementary groups (`identity.groups`) — every delta entry carrying its
own `reason`, because an increment is a grant. A bare-set that discards a non-empty inherited list is legal — a
template may define its own floor, a leaf may redefine a surface wholesale — but never silent: the compiler
warns, naming the field and what was dropped, so the clobber that once showed only in a compiled-artefact diff
shows at compile time.

A **floor** unions down the chain and is never replaced: a child can only add to it, because non-removability
is exactly what makes it a floor. The invariant denies (`net.proxy.deny.invariant`), the seccomp denylist, the
exec and env denylists (`exec.deny`, `env.deny`), and the socket-family denylist (`net.bpf.deny_families`) all
compose this way; there is no remove form for any of them.

Three list fields stay set-replace deliberately, each for a stated reason. `provides` — the mesh supply side —
is attributed wholesale to one declaring layer, because the reserved-namespace gate resolves that layer's
signing tier to decide whether a reserved name may be claimed at all; per-entry composition would smear that
authority attribution across layers. The `mutable` manifest is the spawn target template's own contract about
which of its fields a spawner may patch; letting an includer inject mutability additively would be a hole, not
a feature. And `audit.sinks` is deployment configuration — where events go, not what is granted. All three
still get the clobber warning.

Inheritance is single-parent with no diamonds, and a user's own policy is a leaf that extends one template and
is not itself extensible, which keeps developers from accumulating unmaintained team templates that drift from
the reviewed set. Where unrelated templates must share a cross-cutting fragment, a corporate egress allowlist
or a mandated audit block, that fragment is pulled in as a signed, version-pinned, additive-only include rather
than forced into a contrived hierarchy — add-only means exactly the increment forms above, never a bare set.
The folded result is then translated into the runtime's effective form, the flat representation the enforcement
path reads.

## 16.3 The signature is the commitment

Integrity runs on ed25519 signatures end to end, and the compiler's handling of them is the security-critical
half of its work. Every source template and fragment is signature-verified as the chain resolves, against the
trust store the operator controls, so a chain that pulls in an artefact no trusted key signed fails to compile
rather than folding an unsigned grant into the result. What a reference resolved to is then pinned. The
lockfile records, for every reference, the signing-key identity and the artefact's signature. A
reference with no prior pin is trust-on-first-use, accepted and recorded so the pin is established the first
time it resolves, and a later compile that resolves the same `name@version` to a different signature is a hard
error rather than a warning. A deployment that will not extend that first-use trust compiles under a
require-signed posture, where an unsigned ancestor or include is refused outright rather than pinned. The
signature is the pin. A kennel signature is an SSHSIG, the armored OpenSSH detached signature `ssh-keygen`
produces and verifies, and the pin commits to the canonical bytes through a SHA-512 of them carried in the
signature's fixed preimage rather than over the bytes directly. Re-tagging a version to different bytes changes
their hash and so the signature, and re-signing the same name under another trusted key changes the signature
too, so both are caught. The hash lives inside the signature object rather than as a second commitment carried
beside it, so the lockfile records one signature per reference as before. The settled policy the compiler emits
is itself signed as an SSHSIG over its canonical body by the compiling authority, produced through `ssh-keygen
-Y sign` so that a key in a file, an agent, or a hardware token are alike to the compiler, one signature
standing for the whole resolved result. The variables that can be fixed at compile, the installation constants a deployment knows when it
builds the artefact, are substituted here and baked in; the ones intrinsically per-spawn are left for the
runtime, recorded so it knows exactly which it owns.

## 16.4 Lint and the footgun warnings

Two kinds of judgement run over a policy, and they sit at different stages. Compile surfaces footgun warnings
on the source, the loud grants and unenforced sections an author should see before signing. The linter runs
later and judges the settled policy for internal incoherence, the combinations that contradict themselves once
the fold has run: a grant the resolved network mode renders vacuous, a listener inherited under a mode that
cannot use it. It exists because the fold can pull in a field the leaf author never wrote and never sees, the
case where a leaf sets one network mode but inherits a proxy listener from its base and the two disagree, which
no reading of the leaf alone would catch. Where `policy show` describes a settled artefact, `policy lint`
judges it, and a non-empty result is a non-zero exit; the shipped template corpus is required to lint clean,
asserted by a test, so the baseline an operator builds on is coherent before their own deltas land on it.

```
[[unix.allow]]
name = "ssh-agent"
real = "/run/user/1000/ssh-agent.sock"
shim = "~/.ssh/agent.sock"
reason = "the workload signs its own git pushes"

# compile warns, and does not refuse:
# [[unix.allow]] `ssh-agent` shims an SSH agent (name = "ssh-agent" /
# env = "SSH_AUTH_SOCK"): an exposed agent is a destination-blind signing
# oracle. Shim a raw agent only if you accept that any code in the kennel
# can sign for any destination.
```

The grant compiles, because the operator may have meant it, and it warns, because they may not have. A footgun
is a grant the framework will carry but an author should see in full before they sign over it, so the warning
names the grant, the threat it opens, and the narrower section that exists for the safe version of the same
need.

## 16.5 The compiler is out of the trusted base

All of this, the TOML parsing of arbitrary templates, the chain walk, the glob handling, the include conflict
resolution, the signature verification, is the most complex and most fallible code in the policy path, and none
of it runs in the daemon. The compiler is a separate crate the command-line tool links and the daemon does not,
some three and a half thousand lines of authoring front end held behind a hard crate boundary, and a dependency
query against the daemon shows none of it present. The runtime keeps only the verify-and-load half: check one
signature over the settled policy, re-assert the framework invariants, fill the per-spawn variables, build the
kernel objects, and spawn. The fallible resolver is quarantined where its failures are review-time feedback
rather than a fault in the trusted base (`quarantine-the-unsafe`), and the daemon's reachable surface shrinks by
exactly the code that does not need to be there.

That boundary is what makes the two operating modes possible without weakening either. A developer iterating on
a policy does not type the compile step: `kennel run` of a source policy compiles it in memory when no fresh
settled artefact exists, signs the result and records the lockfile pins, marks it a development build, and runs
it, recompiling when it detects a changed input against the recorded provenance, so the edit-run loop stays
tight. An organisation instead compiles centrally, on infrastructure that holds the templates, the fragments,
the lockfile, and the signing key, and pushes only the signed settled policies to workstations that need none
of the resolution machinery; there the runtime trust surface is one signature check against a pinned key. The
authored artefact stays where the complexity is reviewed, and the enforced artefact arrives simple, fixed, and
signed, which is the shape the next chapter takes up.
