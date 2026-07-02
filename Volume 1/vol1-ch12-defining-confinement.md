# 12. Defining confinement

The chapters to here have described what each boundary does. None has shown how an operator asks for
one. That is the policy: the artefact in which a confinement is declared, signed, and handed to the
framework to enforce. This part of the book is about the policy: how it is written, how it becomes the
thing that enforces, and what crosses the boundaries it draws. Because a policy is a written thing,
this is the first chapter that shows the writing.

What it shows first is how little of it there is.

## 12.1 Intent, not machinery

A confinement could be specified in full every time: every path denied, every default set, every floor
restated, for every kennel. It is not. An operator's policy declares the intent particular to one
kennel and inherits everything else from a template someone signed. A complete working policy for a
coding agent is about this long:

```toml
template = "ai-coding-strict@v4"
name = "myproj-ai"

[[fs.read.add]]
path = "~/projects/myproj/**"
reason = "the project I am working on"

[[net.allow.add]]
name = "api.anthropic.com"
ports = [443]
reason = "the model API this agent calls"
threats.exposed = ["T1.8"]
```

Two grants and a name. The project this agent may read, the one endpoint it may reach: the facts only
this operator knows. Everything that makes the kennel safe (the categorical denials, the empty world,
the non-escalation floor, the deny-by-default on every resource) is in the template named on the first
line, written and signed by someone who maintains it, inherited here without being restated. The
operator adapts a confinement; they do not compose one from nothing. It is the same discipline the
delegation and mesh chapters turned on workloads and services, turned now on the operator: fill the
blanks of a signed thing, do not author the whole.

## 12.2 Deltas carry their reason

What the operator writes are deltas: changes against the inherited policy. There are a few kinds: add
an entry to a granted set, remove one the template allowed, override a single value, or (for a
template author) mark a rule so that no policy downstream may remove it. The two `add` blocks above
are the common case; the rest are rarer and, by design, more conspicuous.

Every delta must say why (`tell-me-why`). The `reason` field is not decoration and not optional: a policy that omits
it does not compile. A grant without a reason is a grant nobody will understand in six months, and the
design refuses to accept one. The reason travels with the delta into the audit log, the risk report,
and the review diff, so the question *why can this agent reach that?* always has an answer attached to
the grant itself rather than living in someone's memory.

The rarer the delta, the louder it reads. Adding a project path is unremarkable. Removing one of the
template's default denials is not. It is the operator deliberately lowering a guard the template
raised, and it shows up in the diff as exactly that:

```toml
[[fs.deny.remove]]
path = "~/.config/git/**"
reason = "this workflow needs the user's git config; accepted exposure"
threats.exposed = ["T1.1"]
```

The grant names the threat it accepts. An operator who writes this has not slipped past a default; they
have signed their name to crossing it, in a line a reviewer reading the diff cannot miss.

## 12.3 Inheritance and the floor

The template the operator named is itself a short policy, written as deltas against a template above
it, up to a root that grants nothing at all. The chain is linear by rule: each template extends
exactly one parent, and the language forbids the branching structures that would make resolution
ambiguous, so there is never a question of which of two inherited values wins:

```
base-confined@v1          (maintainer) grants nothing: deny-by-default on every
                          resource, the categorical denials, the non-escalation floor.
  |
ai-coding-for-company     (host) adds the shape the organisation wants for a coding
                          agent: the tools it may run, the registries it may reach,
                          the secret files it scrubs.
  |
my-coding-project-x       (operator) the leaf: this project, this endpoint.
```

The layers tend to fall along three tiers. The project's maintainers ship the root and the general
templates; the host an operator runs on extends those with what the organisation requires; the operator
writes the leaf with the facts only they hold. Each tier authors at its own level and signs with its
own key, so a single effective policy is composed of links that were written and signed by different
hands (the maintainer's root, the host's baseline, the operator's leaf), and resolving the chain
verifies each link against the tier that signed it. The tiers are a convention of authorship, not a
fixed depth: an operator may extend a maintainer template with no host in between, or a host may stack
several of its own. What holds in every case is the shape: one parent per link, signed by whoever wrote
it.

Read down the chain, a confinement is assembled from the most general to the most specific, each layer
adding only what it alone knows. Read up it, every kennel traces back to the same root that begins by
denying everything, so deny-by-default is not a setting a policy chooses but the floor every policy is
built up from.

Some of that floor cannot be lowered. A template may mark a rule as an invariant, and an invariant
propagates down every chain beneath it and cannot be removed by any delta, with any reason, however far
downstream:

```toml
[[net.deny.invariant]]
cidr = "169.254.169.254/32"
reason = "the cloud metadata endpoint; never reachable from a kennel"
```

A leaf policy can remove an ordinary default deny (loudly, as above) but it cannot remove this one,
and the compiler rejects the attempt rather than honour it. This is the floor of the resource chapters
expressed in the language: the categorical denials that hold regardless of policy are invariants no
policy can weaken, and the language draws the line between a default that may be crossed with a reason
and a floor that may not be crossed at all.

One more limit keeps that floor meaningful, and it needs stating with care: a leaf policy is not, by
itself, a template. An operator's adaptation confines their own kennel; it does not silently become a
baseline other operators inherit from. This takes nothing from the operator. Templates are written and signed at all three
tiers (by the project's maintainers, by the host, and by the operator themselves), so an operator who
wants a reusable baseline authors and signs one exactly as the other tiers author theirs. The operator
is one of those who define confinement, not someone the framework holds at arm's length. The design
confines the workload, never the operator who defines the confinement; a framework that reached to
confine its own operator would only be bypassed, as the premise held from the first chapter. What the
rule prevents is the accident: a one-off leaf, never meant as a baseline, copied and extended until a
sprawl of unmaintained policies has drifted from the floor they all started above. A baseline is made
deliberately (authored, signed, versioned) or it is not a baseline.

A policy, then, is a small and reasoned declaration: a handful of grants the operator alone can supply,
written as deltas that each say why, over a deep inheritance of confinement the operator never restates
and a floor the operator cannot lower. It reads as intent because the machinery is elsewhere:
inherited, signed, and out of the operator's hands. What it does not yet explain is how this written
intent becomes the thing that enforces: how the chain, the deltas, the signatures, and the
floor are resolved into something a kennel can be held to, and what happens when any of it does not
check out. That is the next chapter.
