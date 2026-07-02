# 13. Dynamic spawning

The resource chapters confined a kennel against everything it reaches. What follows is kennels in relation to
one another, and the first relation is the simplest: one kennel asking for another. An agent that does real
work needs helpers, a tool runner, a sub-agent, a server speaking some stdio protocol, and a confined workload
has no authority to build a kennel of its own. How it gets a second kennel without the power to make one is the
chapter.

## 13.1 The trifecta, split

An AI agent is useful only with both code execution and network reach, and a single workload holding both is
the breach. A prompt-injected agent that can run code, see private data, and reach the network has everything an
exfiltration needs in one process, the lethal trifecta in one place. The industry's answers are a virtual
machine per task, heavy to orchestrate, or a container engine run inside the sandbox, which is root-equivalent
and leaks. Kennel has a cheaper primitive to hand, because it can already build a tightly scoped kennel and wire
a channel to it. The move is to split the trifecta across siblings. The agent holds neither capability: it
cannot run code and it cannot reach the network. When it needs one, it asks the daemon to spawn a sibling that
holds exactly that one, a tool kennel that executes with no network, or a fetch kennel that reaches the network
with no execute grant, and talks to it down a channel. No single kennel ever holds both halves of the trifecta,
and the agent that orchestrates them holds neither.

## 13.2 Request, don't author

The rule the rest of the chapter rests on is that a workload cannot introduce policy at runtime
(`request-dont-author`). It does not write a child policy and ask the daemon to run it. It names a template the
operator signed into the trust store, and it writes only the fields that template's manifest declares mutable.
The signature was checked when the operator installed the template, so a spawn is a reference to a capability
the operator already consented to, never a new grant authored by confined code. The agent's whole control over a
spawn is the writes it makes to those declared fields, and that surface is the entire attack surface of the
operation.

```
[spawn]
max_instances = 8
reason = "the orchestrator instantiates fetch, build, and tool helpers per task it is handed"

[[spawn.allow]]
template = "net-fetch@v1"
mutable = ["net.proxy.allow"]

[[spawn.allow]]
template = "argv-tool@v1"
mutable = ["workload.argv"]

[[spawn.allow]]
template = "untrusted-build@v1"
```

The grant carries `max_instances`, the concurrent-instance ceiling the compiler requires so the delegation
cannot become a fork bomb, and a `reason`, because the waiver is loud and validated. Each `[[spawn.allow]]`
names one versioned template the operator signed into the trust store, never a capability, and where present a
`mutable` list narrows the requester to a subset of the fields that template already declares writable.
`net-fetch@v1` exposes the proxy allow-list, itself bounded to a fixed set of package-registry destinations;
`argv-tool@v1` exposes the command line, fenced by the template's `[exec]` floor; `untrusted-build@v1` is
instantiated with no field open at all. The templates carry the authority, and the agent writes only into the
blanks each one fences.

The fence is the template's, not the grant's, and it bounds values and not just which field is open. The
`mutable` list opens `net.proxy.allow` for `net-fetch@v1`, but the template's own signed manifest declares what
may go there, a fixed `match` set the spawn selects from:

```
# in net-fetch@v1's signed manifest
[[mutable]]
field = "net.proxy.allow"
match = [
  "pypi.org:443", "*.pypi.org:443", "files.pythonhosted.org:443",
  "registry.npmjs.org:443", "crates.io:443",
  "github.com:443", "ghcr.io:443",
  ...
]
```

So a spawn may add `pypi.org:443` and cannot add `exfil.example:443`: the field is a selection from a signed
allow-set, never a blank the requester fills freely. The grant opens the field, the template bounds the values,
and neither the agent nor the requester can write past the set the operator signed.

What the agent sends is a patch, a set of field-path and value pairs naming manifest fields, never a candidate
document. The daemon rejects any path the manifest does not open, checks each value against that field's
declared bound, and applies the survivors onto the resolved template, so the instantiation differs from the
signed template only within the manifest and nowhere else (`make-invalid-unrepresentable`). The shape matters as
much as the rule: because the agent submits writes against named fields rather than a whole policy, no adversarial
policy document and no deep tree comparison ever enters the daemon, and the parser the project keeps out of its
trusted base stays out here too (`quarantine-the-unsafe`). The capability floor of every spawn is the signed
template's, and no field the manifest leaves frozen can be moved by any patch. So that the agent need not probe
for its limits, the grant is readable: it can ask the daemon for its own spawn surface and be told which
templates it may name and which fields it may write, with their bounds, and fill the fenced blanks rather than
discover them by firing speculative spawns. The relation it creates is lateral, as every relation in Kennel is.
The daemon is the spawner; requester and spawned kennel are siblings joined by a channel and a brokered
lifetime, not a parent owning a child, and the requester cannot `ptrace` or signal the kennel it asked for,
because reaching into it would defeat the isolation the spawn existed to create.

## 13.3 The handoff, and the daemon out of the path

The spawn itself is an outward broker of file descriptors, the same shape as every other thing the daemon
brokers. The requester sends a `SPAWN` transaction naming the template and carrying its patch and no
descriptors, with its reply flagged to receive them. The daemon validates the grant, resolves the named template
from the trust store and verifies it against the signature the requester's own compiled policy recorded,
re-checks that the template is eligible to be a spawn target, and applies the patch, all in its verify path and
never in a policy compiler. Then it mints the channel, a socketpair for the bidirectional protocol and a
separate pipe for the spawned kennel's standard error, injects the far ends into the new kennel's supervision
plan, and returns the near ends to the requester in the reply. Nothing flows into the daemon in any of this:
node 0 issues descriptors outward and never accepts them inward, and a spawn is one more case of that invariant,
not an exception to it. The spawned kennel's init boots and seals it and, as its last act before `execve`, places
the injected ends on the workload's stdio and runs the template's entrypoint.

Once the spawned kennel is running, the daemon and the bus are gone from between the two. The tool reads and
writes its protocol natively over stdio, the requester reads and writes its end of the socketpair, and the bytes
move kernel to kernel with nothing in the middle, the same control-plane-only discipline the network proxy keeps
(`control-not-data-plane`). The protocol that rides the channel is opaque to Kennel on purpose. The spawn
primitive is a generic transport for a confined stdio service, and a model-context server is one convention that
rides it exactly as a language server or any other stdio tool would; teaching the daemon to understand the
protocol's messages would put a per-message mediation surface and a dependency on someone else's evolving
specification inside the trusted base, which is the thing the single chokepoint exists to refuse. Kennel writes
no first-party interposer either, because a first-party one would re-import the exact parser it just kept out;
an operator who wants tool-level mediation runs an existing proxy for it, confined in a disposable kennel
between requester and tool like any other vendored code. The separate pipe for standard error is the small detail
that makes the channel trustworthy: a traceback or a panic in the tool leaves on its own descriptor rather than
corrupting the framed protocol, and the spawned kennel's own pre-`execve` failures, a seal that will not apply,
a filter that will not compile, route to the host audit instead, so the requester sees a clean end-of-file for
an infrastructure fault and tool output only once its own tool is the thing running.

## 13.4 Ephemerality, fate-sharing, and the depth bound

A spawned kennel leaves no trace on the host, and that is a separate property from the trust argument rather than
a consequence of it. The instantiation is built in memory, because no child policy is ever authored to write to
disk; the kennel takes a transient name that consumes no operator namespace; its root is ephemeral and it cannot
write host disk, and what artifacts pass between siblings pass as memory objects over the channel, charged to and
bounded by the spawned kennel's own cgroup. It also must not outlive its purpose, which three reapers enforce on
the one freeze-and-kill mechanism. When the requester is done it closes the channel and the tool reads
end-of-file and exits, the graceful path; if the requester instead crashes or is itself reaped, the daemon
sees its binder session drop and kills the spawned kennel regardless of whether the tool noticed, the backstop
for a hung tool; and independently of the requester, every spawn-target template declares its own lifetime
bound, so a tool whose requester holds the session open forever still reaps itself at its declared limit. The
concurrent ceiling is held by an atomic claim taken before construction and released on every terminal outcome,
including a build that aborts before the kennel ever reaches the reaper, so a boot failure cannot leak a slot.

Spawning is one level deep by rule. A template that may be named as a spawn target may not itself carry the
spawn grant, which is a fork-bomb prohibition and not a feature deferred for later: recursion would turn the
concurrent ceiling from a global bound into a per-node one and the lifetime coupling from a single hop into a
chain, so the depth bound keeps both flat by construction. Eligibility to be a target, that a template carries no
spawn grant of its own, declares a lifetime and resource ceilings, and declares the manifest that fences the
write surface, is checked when the spawner is installed rather than the target, because a template cannot know
at its own install which future policy will name it. That install-time check is fail-fast feedback, not the
authoritative gate, because the trust store is mutable and a re-signed entry could otherwise slip an ineligible
target past a stale pass. Two things close the gap at spawn time: the requester's compiled policy pins the
signature of every template it names, and the daemon verifies the resolved template against that pin and
re-runs the eligibility check on it regardless, fail-closed on either. The pin carries the ordinary supply-chain
cost, that a spawn target cannot be patched in place without every spawner that names it failing closed until
recompiled, which is the deliberate trade of byte-exact integrity over convenience. The grant that opens all of
this is loud, declared by the operator and surfaced in the risk report as the delegated-spawning exposure it is
(T3.9).
