# 8. Cryptographic services

A workload that does real work reaches for the user's cryptographic agents: it pushes to a remote over
SSH, signs a commit, authenticates to a host it was told to reach. These are among the most dangerous
sockets in the session (a connection to a signing agent is the standing authority to act as the user),
and like every other resource they are default-deny: no cryptographic authority reaches a kennel unless
the policy grants it, and the agent socket itself never crosses at all.

Whether a grant can exist, and what shape it takes, turns on a line drawn sharply here but not
invented: it is a standing law of the whole design (`authentication-never-attestation`). A
cryptographic agent does two different things under one socket. It authenticates: proves, now, to one
party, that the user holds a key. And it attests: asserts, durably and portably, that the user vouches
for these bytes. The boundary can carry the first and must never carry the second, and the reason
reaches far past signing.

A capability the monitor mediates may be authentication-shaped: a constrained, host-verifiable act it
can bind to a property it is able to check (may I reach this host, may I open this connection, render
this frame, carry this transport). That is what the interposition limb has been carrying all along; every
facade of the last two chapters was an authentication-shaped capability bound to a checkable edge. A
capability may never be attestation-shaped: vouching, signing, issuing a secret ("trust that this is
so"), whose entire worth comes from the trust of its origin. And a kennel's origin is untrusted by
construction. A kennel that vouches is a trust root placed inside the boundary built to confine it: a
trust claim with nothing behind it. You cannot automate trust for an untrusted thing. SSH and GPG are
the two services the user runs that fall on opposite sides of this one law.

## 8.1 Authentication

SSH is the authentication-shaped case (the destination is exactly the checkable property the capability
binds to), and it is solvable, though not by brokering the agent. The agent's protocol signs a blob that
carries no destination, so an agent, or any broker filtering in front of one, can bound which key signs
but never which host the signature authenticates to. A workload holding the socket opens it directly,
asks for a signature over a challenge it built for a host of its own choosing, and authenticates as the
user anywhere that key is accepted: a host the policy never named, reached by reusing a key across
destinations the operator never meant to join (`T1.6`). The agent is a destination-blind oracle, and no
broker can make it destination-aware, because the destination is not in the protocol to filter on.

So the design changes what the workload holds. The signing authority stays out of the kennel; in its
place the workload is given a synthetic credential, and here the direction is easy to get backwards and
worth stating flat. For each destination granted, the trusted side mints a fresh keypair. The kennel
receives the *private* key; the trusted side keeps the *public* key and binds it to the real
destination. The instinct that the private key is the precious secret is the one to drop: this synthetic
private key authenticates to nothing real on its own: it is a disposable index. The security-bearing
half is the public key, because its binding to a destination is what the workload must never reach. The
workload holds the index; the trusted side holds the table, and the destination follows from which
credential authenticated, settled when it was minted, never read from anything the workload asks
(`split-the-uid`).

What the trusted side does with a matched credential is re-originate. It makes a new connection outward,
as the operator, with the operator's own real key (the key that never entered the kennel and never
will), carrying the workload's command through to the bound destination and signing against that host
and no other. The workload reaches the re-origination point over the egress machinery of the previous
chapter, allowlisting only that point and never the destinations behind it. So cross-host reuse, the
whole danger of the oracle, is not guarded against but made impossible to express: the key that could go
anywhere is never in the kennel, and the key that is there leads to exactly one host by construction.
The re-origination point is no bespoke proxy in the trusted path: it is the same ubiquitous SSH server
software every platform runs, configured to delegate one decision to the trusted authority, so the only
new trusted code is the small resolution from credential to destination.

## 8.2 Attestation

GPG is the attestation-shaped case, and it is not solvable, because there is nothing to engineer: only
a contradiction. A signed commit or release tells readers who will never see the kennel that the user
stood behind these bytes; its worth is the user's trust, and the user's trust is the one thing the
boundary exists to withhold from what runs inside. To let the kennel attest as the user is to mint
trust-bearing claims from inside a boundary built to deny trust. No broker resolves it: a broker would
have to decide which attestations the user *means*, which is judging intent, which the design refuses
(`good-boy`). So the framework builds no GPG facade, and unlike SSH there is no re-originated
form that would save it: the need itself does not belong in confinement. What is refused is the mediated
service, the framework standing behind a signing act as safe; the raw agent socket, like any raw grant, an
operator may still force as a warned footgun they own, and the runtime does not pretend the connect is
unavailable. The framework will not *build* the attesting broker; it does not police what the operator
connects by hand.

And the refusal is a category, not a case. No facade the monitor ever grows (none built today, none
added later) may be a secrets broker or a signing service, for the same reason. Handing the act off to
a keyring, a hardware token, a vault does not rescue it; it only relocates the attestation to "I am
authorised to fetch this on the workload's behalf," which is the broker vouching for an authority it
cannot be trusted to vouch for. The whole category is refused, not merely left unbuilt.

What a kennel legitimately needs by way of trust material comes to it the other way around: not
brokered at runtime but placed at construction. A credential a workload truly requires arrives as a
signed construction parameter, present in the kennel because the operator put it there, declared and
visible in the policy (Chapter 4). That is the authentication-shaped form of the same need: the kennel has
what it was given, rather than asking a peer to vouch for it at runtime. The construction limb supplies
trust; the interposition limb never manufactures it.

So the two services divide on the one law, and the law divides more than them.
Authentication is a proof to one party, bound to a property the host can check and re-originated with
the real key kept home. Attestation is a claim to everyone, bound to nothing a host can verify, and not
to be made from inside a boundary built to withhold the very trust it would carry. That check-ability is
what decides whether the monitor may *mediate* a capability or must confine itself to *connecting* the
workload to it and stepping out. To mediate is to parse the protocol and pass the requests that clear a
rule, which is the monitor vouching that each passed request is a legitimate one; it can only do that
honestly where the property it vouches for is one it can check. Authentication has such a property, the
destination, so the monitor mediates it and binds each act to the host it is for. Attestation has none,
so a facade that mediated it would be vouching for an authority it cannot verify, and the monitor refuses
to build one. What the operator connects raw is a different thing: a bare fd the monitor parsed nothing
on and vouched nothing for, the operator's to own. The line is not signing versus not-signing but
mediate versus connect, and it falls where check-ability does. Every facade the monitor offers stands on
the first side; the entire category of vouching stands on the second, never mediated, and where the
operator forces a raw connect to it the monitor carries the bytes without standing behind them. The key
that goes one place is all the workload is given, and the standing to vouch for the user is
given to no workload, by no facade, ever.

What is refused is the standing to vouch *as the operator*. The workload vouching *as itself* is a
different act entirely, and nothing forbids it. An operator who wants a kennel to sign draws a second
identity, a signing key distinct from their own, and hands the workload its private half the way any
other trust material enters, placed at construction and declared in the policy. The workload then signs
in its own name, and the signature is worth exactly the trust that identity has earned, which is the
operator's to confer and the operator's to bound. No facade mediates it and no agent is exposed, because
the workload holds the key rather than asking a broker to wield the operator's; the construction limb
supplied the trust and the interposition limb never entered. The line the law draws runs between the two
identities, not across signing itself: the operator may give a kennel a voice, on the condition that it
is the kennel's own and never a theft of theirs.

## 8.3 The man-in-the-middle we can't be

There is a move the SSH bastion seems to license. If an authentication can be re-originated, why not a
request: let the workload reach a remote API without holding the token, and have the framework insert
the credential into the workload's outbound HTTPS on the way past. The workload never sees the secret;
the same shape that made re-origination clean, applied to the web. The goal is right, which is what
makes it tempting.

It fails on direction. Re-origination proxies between two connections the bastion is an endpoint of: it
terminates one and originates another, both real, wielding a key that was the operator's to begin with
and binding it to a destination the host can check. Header injection is not that. The framework is not
an endpoint of the workload's HTTPS session, so to add a header it must terminate the transport under a
certificate authority the workload is forced to trust and re-encrypt to the origin. That CA is the
whole problem. The SSH bastion's trust anchor was scoped to one thing we owned, the synthetic key we
minted; a CA the workload trusts is unscoped by construction, able to present a fabricated identity for
`google.com`, for a package registry, for any origin the workload will ever reach. We would not be
vouching to the remote that the workload is authorised; we would be vouching to the workload that every
remote is who it claims to be, having made ourselves the issuer that says so. That is a false
attestation in the direction §8.2 refused, aimed at the confined side: TLS's entire authentication
guarantee inside the kennel would root in a CA we hold, so a single flaw in that proxy impersonates the
whole internet to the code we are supposed to be confining. We would have fixed one credential handoff
by making the framework a trusted issuer for every remote at once. So it is not built. The credential a
workload needs enters at construction, held by the workload as its own; the destination is mediated as
reach, and the encrypted stream is left to the two parties that own it.
