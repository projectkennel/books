# 8. The network

Chapter 7 gated which programs a kennel may launch. Where a launched program may reach is the network's
question, and it is the one most directly tied to the harm a confined agent can do, since exfiltration and
command-and-control both travel outbound. The design's move is to give a kennel no network path of its own
and route every connection it makes through a broker that decides, resolves, and dials on its behalf. The
filesystem was confined by building the world the kennel sees; the network is confined by building the path
the kennel takes, in both directions: the one it reaches out along, and the one a connection reaches back in
along.

## 8.1 The four modes

A kennel's relationship to the network is one of four. In `none`, the kennel gets an empty network namespace
with no interfaces and no inet sockets at all, a zero-cost case that needs no proxy and no loopback, right for
an untrusted post-install script or a repository the operator only wants to read. In `constrained`, the
default for a defensible template, the kennel gets its own namespace and reaches a specific allowlist of
destinations through a per-kennel proxy. In `unconstrained`, the same namespace and proxy carry open egress,
keeping the namespace boundary and the audit stream but dropping the allowlist to the invariant denies, for a
build that truly needs the public internet with its traffic still recorded. The three share a shape: a private
network namespace, and egress only through the broker.

The fourth, `host`, is the exception that proves it. A `host`-mode kennel shares the host's network stack
rather than getting its own, which is the only way to run packet capture or raw-socket tooling, and it has no
proxy because there is no namespace boundary to funnel through. The egress gate in that mode is the kernel ACL
directly. Sharing the host stack reinstates host-network reconnaissance in full, the workload can read the
host's interfaces, routes, and listening sockets (T1.6), so the mode is gated on the operator supplying a
reason, the compiler records the reinstatement, and the diff tool surfaces it (`footgun-warn-dont-forbid`).

```
[net]
mode   = "host"
reason = "tcpdump needs the host's interfaces and routes"
```

A by-name allow cannot be expressed in `host` mode and is refused at compile time, because there is no proxy to
resolve a name.

## 8.2 The proxy as gateway

In the three namespace modes the kennel has no route off its own loopback, so it has no network path to the
proxy and no network path to anything: a `connect` to any address but its own loopback listener goes nowhere,
because the namespace is empty of routes. Egress does not cross a network boundary at all. It crosses the
binder gateway. The workload speaks SOCKS5 to an in-kennel shim on the loopback, the shim issues a `CONNECT`
transaction to kenneld on node 0, and kenneld makes the decision: it checks the name against the policy,
resolves it, re-checks the resolved address against the denies, and pins it. It then drives its host-side
`host-netproxy` delegate to dial the pinned address, mints a socketpair, returns one end to the shim as a
conduit, and the delegate splices the other end to the dialled socket. The shim splices the workload to its
end, and traffic flows.

What crosses into the kennel is the conduit, a local socketpair end kenneld minted, never the dialled socket
itself, which stays on the host. kenneld brokered the connection and touched no byte of its payload; the
half-close and teardown ride the socketpair and the conduit's binder death notification
(`control-not-data-plane`). This is the delegate pattern of chapter 2 and the binder gateway of chapter 3 in
one path: a dumb host-side dialer doing the blocking I/O, the daemon as the decision point and nothing more,
and the single controlled crossing being binder rather than a network route.

Routing every connection through the decision point buys three properties that a packet filter cannot. The
policy lives in one place, in user space, where resolving and re-checking a name is ordinary code rather than
a kernel program. The kennel only ever holds a name and never an address, so DNS rebinding is structurally
impossible: kenneld resolves and pins under policy on each request, and a poisoned or shifting answer is
caught before the dial rather than after. And the audit is free, because the component that logs the
connection is the same one that decided it, with nothing to correlate after the fact. A name a kennel asks for
and a name it is refused are the same event in the same log line. The whole of by-name egress policy lives in
that decision, which is why DNS exfiltration is not a hole to be plugged but a path that does not exist: a
kennel has no route to any resolver and cannot make a raw query, so there is no channel to smuggle through
(T1.7).

## 8.3 The two ACLs

Egress policy is written at two layers, because two layers enforce it. The name layer is the proxy's: by
host name, port, and protocol, evaluated by kenneld with the resolver's answer vetted against it, the layer
where the interesting policy lives because only user-space code can reason about a name:

```
[[net.proxy.allow]]
name     = "api.anthropic.com"
ports    = [443]
protocol = "tcp"
reason   = "Claude API"
```

The kernel layer is a
cgroup BPF and Landlock ACL by CIDR and port, with no names, because the kernel cannot resolve one:

```
[net.bpf]
families = ["AF_INET", "AF_INET6"]

[[net.bpf.connect.allow]]
cidr   = "*"
ports  = [443]
reason = "https egress to any host"

[[net.bpf.connect.deny]]
cidr   = "10.0.0.0/8"
reason = "no egress into the corporate RFC1918 range"
```

The two
are not redundant. In the namespace modes the kernel is not routing by destination at all, the empty namespace
already does that; what the kernel enforces there is the socket surface. A raw or packet socket would let a
workload build and send frames directly, around the brokered path rather than through it, and a netlink socket
would let it read or reconfigure the stack, so the family ACL denies all three at socket creation. Raw and
packet sockets already need a capability an unprivileged kennel cannot obtain, which makes that denial the
floor for a root-context kennel rather than the load-bearing control in the ordinary case, while the netlink
denial bites even unprivileged. The same kernel layer gates every `bind` against the inbound ACL. In `host`
mode, with no namespace boundary to lean on, the kernel CIDR ACL on `connect` becomes the egress gate itself.

The kernel ACL is author-writable in every mode, and the framework holds it to one direction: an author may
narrow it but never widen it. A connect rule in a namespace mode cannot reach past the proxy the namespace
already pins the kennel to; it can only subtract further. The evaluation is deny-first, a deny match refusing
regardless of any allow, so the narrow direction is the only one a rule can move the policy in. The kernel
enforces the floor and the socket shape; the proxy enforces the reachable world.

## 8.4 The egress floor and its residuals

Beneath every mode sits a small set of denies the framework will not let a policy remove, and they are
deliberately narrow. The mandatory floor is cloud metadata and link-local addresses, the server-side request
forgery target whose reachability turns a fetch into a credential leak, denied even in `unconstrained` and
`host`. It stops there on purpose. Private address space is not on the invariant list, because a kennel
routinely and legitimately needs a local development server, a LAN database, an internal registry, and making
private space permanently unreachable would be a floor that breaks more than it protects. A policy may add
private denies where it knows it needs none; the framework imposes only the few that are never legitimate.

Two residuals are worth naming because the design refuses to paper over them. The first is that a
destination allowlist cannot see inside TLS: a kennel permitted to reach a real API can carry data out inside
its requests, and the answer is a tighter allowlist, not payload inspection the proxy was built specifically
not to do (T1.8). The second is the honest price of keeping the daemon out of the data path. A conduit kenneld
mints for an approved connection lives as long as the connection does; there is no per-connection kill switch
while the kennel runs, because a kill switch would have to sit in the byte stream to cut it, and putting
kenneld in the byte stream is the one thing the gateway design exists to avoid. Revocation is the whole
kennel, frozen and killed through the cgroup, not a single conduit (T1.10). The control plane decides cleanly
and completely; the price is that, once it has decided yes, the bytes are not its to reach back into.

## 8.5 Loopback isolation

The namespace modes give each kennel a small block of addresses of its own, a slice of the `127.0.0.0/8`
loopback space and an IPv6 unique-local `/64`, allocated per user from a `subkennel` table that is the network
analogue of `subuid`. The addresses are bit-packed and computed rather than written by hand, and they exist on
both sides of the namespace boundary at once. Inside the kennel they are what its own loopback carries, so the
workload binds, listens, and connects against them as it would against `127.0.0.1` anywhere. On the host the
same addresses are added as aliases on `lo`, identical by construction and joined by no route, so a port the
workload exposes shows up host-side at the kennel's own address and an operator's `ss` or `lsof` maps it
straight back to the kennel that opened it.

This is the loopback mirror of chapter 2, and its point is attribution without plumbing: there is no routing,
no address translation, and no interface beyond the aliases, so the same address reality holds on both sides
and a kennel's sockets are observable from the host as themselves. The isolation is the namespace's: another
kennel cannot reach these addresses, because each kennel's loopback lives in its own network namespace and is
structurally invisible to the next; the operator's own shell can reach them through the host alias, which is
correct, since the operator is the one in control. Raising the host alias is the single privileged step the
namespace modes add, an address-add on `lo` scoped to the reserved space and carried by the same narrow
sub-helper that holds `CAP_NET_ADMIN` for nothing else. The honest residual is at the mirror itself: a
host-side listener standing at the kennel's address is reachable by anything on the host that can route to
`lo`.

## 8.6 Binding and the inbound mirror

A kennel that runs a development server or a language server needs to `bind`, and the bind happens natively
inside its network namespace, so the listener is reachable from within the kennel by ordinary loopback. The
policy sits at the syscall: every `bind` is decided by the kernel bind ACL at the cgroup hook, and one that
matches no rule fails there:

```
[[net.bpf.bind.allow]]
cidr   = "127.0.0.1/32"
ports  = [8080]
reason = "the local development server"
```

The bind ACL is the entire decision; exposing an allowed listener to the host is
mechanism rather than a second policy, and that mechanism is the inbound mirror, the one place the binder data
direction runs into the kennel rather than out of it. Egress has the kennel
originating and so pulling outward; an inbound connection originates outside, so the leg that carries it
inward runs from the daemon into the kennel. The mechanism is the mirror image of the proxy: a host-side
delegate, the reverse of the outbound dialer, binds each exposed port on the host alias at the kennel's own
address and accepts, and the in-kennel facade registers a callback once and then sleeps in the kernel, costing
nothing while idle.

On an accepted connection the delegate mints a socketpair, splices the connection to its own end, and hands
the other end to the daemon, which routes it to the sleeping facade as a one-way delivery that wakes it; the
facade connects the workload's native listener and splices. The daemon makes no fresh policy decision on the
inbound path, because the bind ACL already decided what could be exposed at the moment the workload bound the
port, and it touches no byte, because the delegate minted the conduit and does the splicing. The only
descriptor that crosses into the kennel is a benign socketpair end; no host listener and no accepted
connection ever does, so nothing crosses into the trusted base (`control-not-data-plane`). The direction is
reversed knowingly: pushing into the kennel is the logical data direction for an inbound connection, and the
callback the facade hands up is bounded by a death notification that stops the daemon pushing to a torn-down
kennel, a one-way delivery that lets it never block on the facade, and a registration the daemon honours only
for a port the policy already exposes.

## 8.7 Shaping the bind

The last of the inbound machinery is as much about not breaking tools as about safety. Much of the
development-server ecosystem binds `0.0.0.0` by default, and denying that would break it, so the kennel
rewrites instead: a cgroup hook on `bind` turns a bind to the wildcard address into a bind to the kennel's own
private address, and `getsockname` reflects the rewrite, so a tool that asked for `0.0.0.0` reports that it is
listening on the kennel's address and behaves correctly. A dual-stack socket is the trap underneath that: a v6
listener that also accepts v4 would slip the rewrite, so the kennel forces `IPV6_V6ONLY` on and intercepts the
attempt to clear it, making a workload that wants v4 ask for it as v4. Two kennels can both bind the same port
without colliding, because each binds inside its own namespace and the host mirrors land on distinct
addresses, and the kennel's `/etc/hosts` shadows `localhost` to its own address so the tools that hardcode it
still resolve to the right place.

What makes the shaping small is that the namespace has already removed the worst of what a bind could reach. A
kennel has no LAN interface, no VPN or overlay interface, and no host `127.0.0.1` service inside its namespace
to collide with or silently stand in for, because none of them were built into its network world
(`construction-by-absence`). The bind ACL and these rewrites shape what is left, the kennel's own loopback, and
decide which of its ports are mirrored out to the host. Through all of it the workload sees none of the binder
mechanics underneath; the in-kennel facade is a translation layer and nothing more, and as a parser of the
workload's own socket traffic it is treated as untrusted and fuzzed.
