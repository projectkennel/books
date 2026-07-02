# 3. The two limbs

Chapter 2 set the requirement: complete mediation, every path either absent or mediated, no resource
left present, reachable, and ungoverned. It did not say how. There are two ways to meet that
standard, and only two. A resource can be removed, so there is nothing to mediate. Or it can be
interposed upon, so every use of it is a request the monitor answers. Absence and interposition.

The order between them is not a toss-up. The cheapest, smallest, most certain mediation is the kind
you never perform, because the thing it would have governed is not there. So the first question for
any resource is not how to guard it but whether the workload needs it at all, and only what survives
that question reaches the second limb. That ordering is `do-less` applied to confinement: remove
first, interpose only what cannot be removed.

## 3.1 Absence

The strongest way to mediate a resource is to arrange that the resource is not there
(`construction-by-absence`). A workload is not handed the whole machine and then fenced off from most
of it. It is placed in a world built to contain only what its policy grants, and what the policy does
not grant is not refused on request: it is simply absent. There is no file to refuse, because the
path does not resolve. No host to block, because the network is empty. No service to turn away from,
because its name means nothing in the workload's world.

This is complete mediation reached for free. An absent resource has no access to mediate, because
there is no access to it at all. The monitor does no runtime work to hold the boundary. The boundary
is the shape of the world the workload was given, decided once, when that world was built, and held
beneath the workload by the kernel. What the workload can reach was settled at construction; within
that, it acts directly, and it cannot reach past it, because there is no past-it to reach.

Absence also answers a kind of attack that guarding cannot. A workload that cannot see a resource
cannot probe it or wait for it to appear. The reconnaissance that reads a filesystem for what is
worth taking, or scans for a service to exploit (`T1.1`), runs into a world holding only what was
granted and finds nothing else, because there is nothing else to find. A denied request still tells
the asker that something was there to deny. An absent resource tells it nothing.

This is `do-less` at its sharpest. The economy of mechanism the field has urged since 1975
[SaltzerSchroeder] is usually read as keep the guard small. Absence keeps it smaller still: it
removes the thing the guard would have watched. Every resource a workload does not receive is one the
monitor never has to mediate: an attack surface not reduced but gone. So absence is the limb to
reach for first, and the design reaches for it hard. Most of what a workload would traditionally be
allowed or denied, Kennel instead arranges never to be present at all.

## 3.2 Interposition

Some resources cannot be made absent, because the workload needs them. An agent has to
reach the one API it was sent to use. A build has to talk to the package index it depends on.
Removing these would not confine the workload; it would break it. For these there is the second limb:
the resource stays, but every use of it is a transaction the monitor authorizes, one call at a time
(`interpose-as-transaction`).

This is what Irvine called virtualization: inserting the validation mechanism between the resource
and the code that wants it [Irvine]. The workload does not hold the resource. It holds a request
channel to the monitor, and the monitor holds the resource. Each use is named, checked against the
policy, and either carried out or refused. Nothing is handed over as a standing capability the
workload can keep and reuse unwatched; a use allowed once is not allowed forever, because there is
nothing in the workload's hands to reuse, only the asking.

Interposition is the more expensive limb, and the design spends as little on it as it can. A monitor
that sat in the path of every use would grow large, and a large monitor cannot be verified (Chapter
2). So the monitor mediates the decision, not the traffic. It sets a channel up, decides whether a
use is allowed, and then steps out of the byte path; the data flows directly between the workload and
the resource without passing through the monitor again (`control-not-data-plane`). The monitor is in
the control plane, deciding, never in the data plane, copying. A workload moving a gigabyte through
an approved channel does not move a gigabyte through the monitor, and the code that has to be trusted
does not grow with the load it carries.

What interposition buys, that absence cannot, is a decision that turns on the particulars of a use
rather than the existence of a resource. A workload may need the network and still not be allowed
every destination on it; it may need a service and still not be allowed every operation that service
offers. Where a grant cannot be reduced to a fixed boundary drawn at construction, it becomes a
transaction decided at the moment of use.

There is a limit, though, on what interposition can carry, and it is worth setting down even though
its full weight comes later. A transaction the monitor mediates is an authentication-shaped act, a
host-verifiable use it can bind to a property it is able to check: reach this destination, open this
connection, render this frame. It is never an attestation: the workload vouching, as the user, for
something whose worth would rest entirely on the user's trust, the one thing a boundary built around
untrusted code cannot manufacture, only withhold (`authentication-never-attestation`). Chapter 8
takes up why the line falls exactly there.

Between them the two limbs cover the surface. What a policy can settle in advance, what the workload
may reach and what it may not, is settled by construction: the granted built into its world,
everything else absent, the boundary fixed before the workload runs and held beneath it. What cannot
be settled in advance, because the decision turns on each use, is settled by interposition, one
transaction at a time. There is no third limb, and no resource left present, reachable, and
unmediated, the standard Chapter 2 set. The two are not equal options. Absence is the default and
interposition the exception, because the discipline is to do less (`do-less`), and the least is to remove. The
chapters that follow take the resource classes one at a time (the filesystem, the network, processes,
the services a session depends on) and ask of each, in order, what can be made absent and what is
left to interpose upon.
