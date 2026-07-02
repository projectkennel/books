# 15. Keys

Every chapter to here has leaned on a word it did not define. A policy is signed; the runtime checks
who vouched for it rather than re-arguing it; the trust root is the operator, and the tiers above the
operator sign the templates an operator inherits. Behind each of those is a key, and the volume has
not said where a key's authority comes from, what it means for one to be trusted, or what changes when
one is taken away. The trust material is the last substrate to set down, and it is the smallest,
because the rule that runs through the rest of the design runs through it unchanged: what is trusted is
constructed from what is present, and withdrawn by absence.

## 15.1 Trust is placed, not minted

A kennel runs code the operator has not chosen to trust, and the framework holds to a matching
discipline about trust of its own: it will mint a keypair freely, and it mints no trust at all.
Generating a keypair is mechanical and confers nothing; what confers authority is where the public half
is placed. A key is trusted to vouch for a layer of policy because someone with standing put it where
that layer's keys are read from, for no other reason than that it is there
(`authentication-never-attestation`).

This is the construction limb applied to the trust material rather than to a resource
(`construction-by-absence`). A view of the filesystem holds the paths granted into it and no others; a
tier's authority holds the keys placed into it and no others. What is trusted is the exact set of keys
present, not everything a denylist has not yet caught. There is no standing list of bad keys, because
there is nothing a list would add: a key absent from the place a tier's keys are read is already
without authority, indistinguishable from one that never existed. The gains are absence's usual ones.
Nothing has to be enumerated or kept current, and an error of trust is a key visibly present or visibly
missing, never a stale entry on a revocation list that was meant to catch it and did not.

The framework leans into this rather than standing back from it. The ordinary case is one operator on
one machine who needs a single key to begin, and the framework will generate that key and place it in
the operator's own location as part of setting up, so a new user authors and signs at once instead of
first learning to make and install a key by hand. The key is no special thing: an ordinary public-key
identity in the platform's standard format, not a type the framework invented, so the operator receives
something they may already know how to hold and inspect, and the framework has one fewer thing to
define (`do-less`). It confers no trust by doing so; it spares the
operator a mechanical step in trusting themselves, since a generated and placed operator key is the
operator's own signing identity, stood up by construction in the one tier whose authority is theirs to
hold. What it will not do is the rest: pronounce another party's key good, broker trust between two
parties who do not already share it, or become the authority that decides which keys a tier should
hold. Those are attestation, and a kennel withholds attestation by definition.

## 15.2 The hierarchy of locations

The tiers are the ones the policy model already named: a maintainer who ships a base, a host who adapts
it for a fleet, an operator who writes the leaf. Each tier has a place its keys are read from, and the
places stand in the same order as the tiers. When a settled policy is checked, each link in its
inheritance chain is verified against the place belonging to the tier that signed that link: a
maintainer's base against the maintainer's keys, a host's adaptation against the host's, an operator's
leaf against the operator's. A key in the operator's place cannot vouch for a layer claiming a
maintainer's authority. Where a key sits is the scope of what it may sign.

A place holds any number of keys, and the number may be zero. Several keys in one place are several
independent signers for that tier, any one of which verifies a layer it signed: a tier with three keys
present is three holders who may each vouch, not a quorum that must agree among them. This is the
keys-dimension of multi-operator, and it is free, because a set of trusted keys was always a set. Who
may add a key to a place, and how holders are scoped against one another, is a fuller delegation
question the design leaves open; the plain fact that a tier can carry many signers, each admitted by
presence and withdrawn by absence, falls out of the model with nothing added.

Zero keys is the case worth stating, because it is muteness and not error. A place with no keys is a
tier that signs nothing and vouches for nothing; it is no fault and raises no failure on its own. A
chain fails only where it required a signature the empty place would have supplied, and there it fails
as every unmet requirement in this design fails, by refusing to start rather than running degraded
(`refuse-to-start`). Emptiness at the host tier is the expected shape rather than the exception: most
machines carry a maintainer's base and an operator's leaves with nothing between them, and the host's
place stays empty until an organisation has reason to fill it.

## 15.3 Admission, not termination

A key is consulted at one moment, when a kennel is constructed and its policy verified. It is not
consulted again while the kennel runs, because a running kennel re-reads no policy and re-verifies no
signature; its world was settled at the start and does not shift under it. That is what gives removal
its exact meaning. Taking a key out of its place reaches into nothing already running. It changes one
thing: the next construction that would have relied on that key fails to verify, and refuses to start.

The shape to hold is locking an account rather than killing its processes. Locking an account stops
the next login and leaves the open sessions alone; removing a key stops the next kennel and leaves the
running ones alone. They are different acts with different blast radii, and treating one as the other
is the usual mistake. Removal is the quiet, construction-time act: it withdraws the authority to make
new kennels under that key, and says nothing about the kennels the key has already admitted.

When a running kennel does have to be stopped, that is the other act, and the design keeps the two
apart. A kennel is terminated from outside by an explicit command, the way any supervised process is
ended by something above it, and that lever belongs to the tool that runs kennels, not to the trust
material. Keys govern admission and only admission. Whether a kennel may start is the key model's
question; whether a running one must stop is answered by the mechanism that supervises kennels, not by
the one that vouches for their policies.

## 15.4 Keys over time

A design that builds trust from present keys and consults them only at construction has, almost in
passing, said most of what there is to say about policy over time. The machinery a longer-lived system
usually accretes (a register of retired keys, a deprecation state carried on templates, tooling to
march a fleet from one version to the next) is machinery this design does not build, and in each case
for the same reason: the model covers the ground without it.

A template version owes nothing to the versions before it. It is a complete statement at its place in
a chain, not a difference against its predecessor, and a newer version may be stricter than an older
one in any way it chooses, up to adding a categorical denial the older one did not carry. Because a
settled policy is immutable once compiled, none of this reaches a kennel by itself: a settled policy
was resolved against the versions it named, carries its own signature, and is untouched by any later
version of anything it drew from. Change is always deliberate, a re-compilation against the newer
material that yields a new settled policy for the operator to sign. Nothing settled moves, so nothing
drifts.

The version is named in the open: a leaf inherits not from `base-confined` but from `base-confined@v1`,
and the version is a fixed part of what the name points at. That makes the three things an author can do
to a published version distinct. Editing `@v1` in place is the unsafe one, because every policy that
named it resolves against the changed thing on its next compile, and a change that tightened a rule or
moved a field surfaces as a compile failure in a policy that was sound the day before. Publishing `@v2`
beside it touches nothing already named: `@v1` still resolves, and adopting `@v2` is a migration done
one policy at a time, by re-pointing and re-compiling on the operator's own schedule. Removing `@v1`
behaves like every removal in this design: the name stops resolving, and the next policy that tries to
recompile against it does not find it and refuses, exactly as a construction that reached for an absent
key refuses. A published version is best treated as immutable, then: add beside it, retire by removing
it, and do not edit it under the policies that already trust it by name.

Where that deliberate re-compilation meets a floor that has risen, the design's preference for loudness
finishes the job. A newer version that raises the floor will refuse to produce a kennel for a leaf that
crossed the new line, and it refuses at compile, in front of the operator performing the upgrade, named
as the breaking change it is (`refuse-to-start`). A raised floor is never a quiet narrowing found out
later; it is a re-compilation that halts and says what it will no longer allow. An operator who wants
the older, looser behaviour still has it, in the policy they already settled and signed, until they
choose to move.

Deprecation, then, is not a state a key or a version carries. It is the absence of the key you would
have used. A key does not know it is being retired and is not marked as retired; the discipline of
signing is what steers an author to the right key, and the only hard lever is the one already
described, removing the key so the next construction that reaches for it refuses. The design keeps no
record of what is old. It keeps what is present, and lets absence carry the meaning it carries
everywhere else in it (`do-less`).

One thread has run through every chapter without being drawn out on its own: each time the monitor
decides, it can record what it decided. That account, and what it may and may not contain, is the last
piece of the design to set down.
