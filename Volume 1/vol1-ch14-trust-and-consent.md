# 14. Trust and consent

The grant has been written and the grant has been enforced, and both rest on signatures. A signature is
only ever as meaningful as the trust behind the key that made it, so the trust itself has to be set
down: the hierarchy it forms, what is allowed to cross its boundaries, and who is entitled to vouch for
what. It is also where the reference monitor's third property, that the thing to be trusted be small
enough to trust, finally comes home, now that everything it guards has been described.

## 14.1 The trust root

At the top of the hierarchy is not the framework but the user. The default context (the user's
ordinary, unconfined shell, with the full authority of their account) is the trust root, and every
kennel sits beneath it (`split-the-uid`). The framework that builds and mediates those kennels is not
above the user in any sense that matters: it can do nothing in the user's name that the user could not
do from their own shell, it owns no authority the user lacks, and it runs, like everything else, as the
user. What it has that a kennel does not is the policy decisions, the mediation, the record: it sits
higher than the things it confines, and level with the hand that configures it.

And it is bounded by consent at every turn. The user installs the framework, writes or adopts its
policies, enables its services, and can switch the whole of it off. It does not try to confine the
user, and could not if it tried: a confinement framework that set out to restrain the very context that
installs and configures it would simply be removed, and a design that depends on restraining its own
trust root has misunderstood where the trust lies. So the framework draws its boundaries around the
processes the user chose to confine, and around nothing else. An adversary already in the default
context is not a kennel that has escaped; it is the user, by assumption, and there is nothing left to
confine them with, which is exactly why the line is drawn where it is, with the user on the trusted
side of it.

## 14.2 What crosses

Because the boundary is built by construction, what crosses it is short to list, and the list is
exactly what the operator declared (`construction-by-absence`). Into a kennel goes the invocation that
started it, the environment the policy synthesised, the constructed view of the filesystem, the
standard streams where they were granted, and a working directory inside the granted paths. Out of a
kennel comes what a parent is owed: the exit status and signals to the process that launched it, the
standard output and error, the audit record written through the framework rather than by the workload's
own hand, and whatever the workload wrote into the paths it was granted to write. That is the whole of
it.

Everything else does not cross, and does not have to be enumerated to be denied. A workload does not
reach the user's session bus, raise a notification, touch the clipboard, send input to another window,
or signal a process outside its own boundary, not because each of these was thought of and forbidden,
but because none of them was constructed into the kennel's world, and what is not there cannot be
crossed to. The consent model is legible for the same reason: an operator reads what crosses by reading
what they declared, and may take everything they did not mention as not crossing. Between two sibling
kennels the list is shorter still: nothing crosses by default, the two being mutually invisible until
a policy on both sides declares a seam between them.

## 14.3 What the tiers are for

Trust enters the system as signatures, but the signatures carry less than it might seem, because the
thing that most needs securing does not depend on them. The floor (the invariants that make a kennel a
kennel) is re-asserted at every spawn regardless of who signed the policy, or whether it was signed at
all (Chapter 13). It secures itself (`reference-monitor`). A settled run-policy can only narrow within a floor it cannot move and
runs with the operator's own authority, so an operator may sign their own without granting any
escalation, and there is nothing to withhold. With the floor off their shoulders, what the signatures
are left to do is mostly a matter of practice, with a single exception.

The maintainers ship a set of sane templates (a base that denies everything, and useful shapes built
on it) because a framework that offered a blank deny-everything and a manual would be unusable, and an
unusable safety tool is none. An operator picks one and fills in their specifics, or writes their own;
nothing forbids a baseline of one's own on a machine whose trust one controls.

Which signatures a machine treats as baselines is set by whoever controls its trust configuration: the
operator on their own machine, the organisation on a managed fleet, where a personal key is not a system
key and a user cannot quietly swap a mandated baseline for one of their own. That is what lets a company
require a confinement for a task and have it stick, the way device management and audit and workplace
policy make other obligations stick: governance the signatures support rather than impose.

One thing they do impose. A reserved name (the kind a kennel resolves against to reach a standing
service) is claimable only by the tier that owns it: the project's own names, under
`org.projectkennel.*`, by the maintainers; a host's namespace by that host. Here the signature is not
serving a convenience or backing a rule that something else enforces; it is the authority itself,
because a name others trust to resolve to a particular provider is worth nothing unless it is anchored
to whoever is entitled to answer it. The carve-out is deliberately small.

## 14.4 Small enough to trust

All of this (the hierarchy, the crossings, the signatures) exists to be trusted, and a thing to be
trusted must be small enough to be understood. This is the reference monitor's third property, and it
is where the design's recurring question, how can I do less, stops being a disposition and becomes a
discipline (`do-less`). The trusted base is what has to be audited, so every part of it must earn its
place: a facade is admitted only where construction cannot reach the threat, and each is answerable to
the specific threat it closes rather than added because it might help. What can be left out is left
out, because what is not in the base is not in the audit.

The honest cost of the parts that remain is smaller than it first appears. A facade does parse
adversary-supplied protocol, on every message, for the life of the kennel: the obvious objection to
interposition, and a real one. But the facade sits on the untrusted side of the boundary and holds no
authority. It turns a hostile request into a typed transaction and does nothing else; the decision on
that transaction is the monitor's, made on an identity the workload cannot forge, and any privileged
effect is carried out by a policy-free actor doing only what the monitor already authorised. The parser
of hostile input is therefore outside the thing that must be trusted, present in the system but not in
the base whose correctness the whole rests on.

That accounting is clean for the ephemeral case and owes a concession for the standing one. The actor
behind a facade is policy-free but not effect-free: it carries out the authorised transaction, and a
standing provider carries the one leg into the host its job requires (the real bus, the real display)
for the whole of its life, not for a single brokered call. A compromised provider does not forge a
decision, but it holds that granted leg and can act through it within the authority the grant already
gave, which is the standing-provider residual named where the mesh introduces it (`T3.10`). The parser
is outside the base; the standing foothold is not removed, only confined to the one leg and made
answerable for it. The two sections state the same fact at different altitudes, and the honest reading
is the narrower: interposition moves the hostile parser out of the trusted base and bounds the
provider's reach, it does not reduce a standing provider's granted foothold to nothing.

The trust root and the tiers above it have stood behind every signed thing in the design, the
authorities that vouch for what an operator may inherit, yet the material that vouching is made of has
stayed implicit. What a key is, what its presence and absence mean, and why the framework mints none of
it, is the substrate the rest has rested on without naming, and the next thing to set down.
