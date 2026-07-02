# 3. Binder's Node 0

Chapter 1 placed the binder among the interposition facilities, and chapter 2 placed the processes that
build a kennel and hold and drop its privilege. What joins them is the question chapter 2 left standing:
how a confined workload reaches a service it is allowed to use without being handed a path to it. The answer
is the binder bus, and the short form is that every kennel gets its own and `kenneld` sits on node 0 of each
as the broker that decides what crosses.

## 3.0 What binder is

A reader who has spent time in Landlock and cgroup BPF may never have touched binder, because it comes from
a corner of the kernel that serves Android and little else. Binder is Android's inter-process communication
mechanism, and on an Android device it is not one IPC among several but very nearly the only one: an app
calling a system service, an app handing work to another app, the framework delivering an event, all ride
binder transactions through a kernel driver, brokered by a userspace registry called the servicemanager.

It belongs to an inverted version of the Unix model. On an ordinary system a person owns and runs
applications and the uid names that person; Android turns this around and gives each installed app its own
uid, isolating apps from one another by uid the way a multi-user system isolates people. The users of an
Android phone are the apps, mutually distrusting, and binder is the IPC built for that situation: a
kernel-mediated channel across uid boundaries, with a context manager that brokers which named service a
caller may find and reach, so no app holds ambient access to another. That shape is the kennel's shape too,
which is the deeper reason the primitive fits rather than merely being at hand: a kennel is an app-shaped
unit of mutual distrust, and the IPC it needs is the IPC Android already built.

And it is, by a wide margin, the most exercised IPC mechanism in existence. Binder carries the cross-process
traffic of every Android device, billions of them, and has done so under continuous attack, fuzzing, and
kernel-security scrutiny for more than a decade. Whatever its quirks, no userspace bus written from scratch
will ever see that volume of adversarial use; taking the driver and its model inherits that hardening
instead of setting out to re-earn it.

## 3.1 From connect to call

The move the bus makes is from the connection to the call. The AF_UNIX shim grants a socket by binding its
path into the constructed view and auditing the workload's connect; that gates once, at connect time, and
says nothing about the authority that rides the protocol afterward. A D-Bus call can spawn a session process
or read a stored secret; a Wayland socket can read the clipboard. Binder generalises the move the SSH bastion
made first, putting the decision at the operation rather than the connection: `kenneld` is the policy
decision point for every protocol call, and the workload holds only unforgeable binder references, opaque
kernel handles with no path to enumerate and no abstract name to probe. That is the `reference-monitor`
restated for local services, with the bus as the mediated transaction every call passes through
(`interpose-as-transaction`).

## 3.2 The bus each kennel gets

Each kennel gets its own binderfs instance, a fully independent mount that shares no nodes with any other
kennel's, the way devpts and tmpfs are independent per mount namespace. binderfs carries `FS_USERNS_MOUNT`,
so the instance mounts inside the kennel's child user namespace, in the same full-capability context the
spawn already uses to mount tmpfs, devpts, and proc; there is no host-side mount and no separate privileged
step. The spawn mounts a fresh binderfs at the view's `/dev/binderfs`, with `max=256` capping binder-device
allocation per kennel as a denial-of-service bound rather than a tuning knob, allocates the standard device
named `binder` through `BINDER_CTL_ADD`, and creates the conventional `/dev/binder` symlink so a stock binder
client finds its driver at the default path with no per-workload configuration, the same principle the socket
shim rests on.

Taking node 0 is where the daemon and the instance meet, and the mechanism is more particular than it looks.
`kenneld` runs in the initial user namespace and must hold the context-manager fd for every instance, since
one entity owning every node 0 is the precondition for routing a call from one kennel to another. It cannot
be handed that fd: a binder fd is bound to the process that opened it, so a descriptor passed over a
socketpair cannot be mapped or made context manager by a different process. `kenneld` therefore opens the
device itself, through `/proc/<init>/root/dev/binderfs/binder`, which it is permitted to do because the
kennel's user namespace is operator-owned and the operator `kenneld` is privileged over the instance. It then
calls `BINDER_SET_CONTEXT_MGR`, which is one-per-instance, taking node 0. The workload is later granted
Landlock read and write on the device, reached through the `/dev/binder` symlink, but never on
`binder-control`: only the spawn setup allocates devices, and it does so before the seal. When the kennel
exits, the instance disappears with the child's mount namespace, with no host-side unmount, and pending
transactions receive death notifications as every node is destroyed. Construction is the privileged step
here, not the bus: the `0 0 1` map the instance's uid-0-owned nodes require is the privhelper's act (T5.4),
not a binder-specific privileged surface.

## 3.3 kenneld on node 0

Node 0 is the service registry, the analogue of Android's servicemanager: a caller reaches it through the
well-known handle and never by name, and its verbs carry the same names as Android's interface even though
the transaction codes are `kenneld`'s own and nothing is wire-compatible. A service process registers a name
with `addService`; a workload resolves one with `getService` and receives a node reference or a failed reply;
`listServices`, `isDeclared`, and `getDeclaredInstances` are the introspection a caller may run on its own
grants. Every name is bounded and validated, checked against the kennel's settled policy before `kenneld`
records or resolves it, and audited on every verb. The check that a service is declared before it can be
registered is the manifest check Android makes against VINTF, with the settled policy standing in for the
manifest: a service the policy does not declare cannot register and reports as undeclared. Binder's general
capability-passing, the transfer of arbitrary node references between processes, is not used; references are
issued only by `kenneld`, and they cross between kennels only as `kenneld` brokers them on the mesh bus, the
subject of the inter-kennel chapter. That drops the reference-graph bookkeeping that
makes Android's implementation subtle while keeping the unforgeable references, the synchronous calls, the
death notifications, and the per-instance isolation.

The bus carries the kennel's own control plane as well. `kennel-bin-init` is a binder consumer on the same
instance, pulling its Plan from node 0 and sending the lifecycle notifications that tell `kenneld` a facade
crashed or the workload exec'd. Those verbs are gated by the unforgeable binder caller identity, the init's
host pid at euid 0, a value the privhelper hands `kenneld` at construction rather than anything the caller
puts on the wire, so a workload can address node 0 but cannot exercise them. The identity binder stamps on
every transaction is the gate, not a token the payload carries, which is why the gate holds against a
workload that controls its own payload bytes entirely.

A reserved prefix, `org.projectkennel.*`, is `kenneld`'s own. It is both context manager and the provider of
a built-in set under that prefix, and two rules hold before any policy lookup: an `addService` for a reserved
name from any caller other than `kenneld` is refused, with no policy override, and a `getService` for a
reserved name always resolves to `kenneld`'s local node and is never routed to a peer kennel. A reserved node
exists only when its policy section is non-empty, so the absence of the node is itself the proof that the
capability was not granted (`construction-by-absence`). The registry verbs are cheap in-memory operations,
but a facade verb performs real host I/O, so node 0 is served by a pool of looper threads per instance rather
than one: each looper receives, handles, and replies to its own transactions, and the pool is sized so that
one looper blocked on a host dial does not stall the others. A dial carries a deadline, so a wedged or
hostile target degrades to a refusal on that one transaction rather than tying up the instance.

## 3.4 A transaction across the boundary

The AF_UNIX facade is the example whose whole shape fits here, and it shows the bus replacing a path with a
brokered connection. The workload sends a `CONNECT` transaction to the `org.projectkennel.IAfUnix/default`
node carrying the requested socket path as a bounded, validated string. `kenneld` checks the path against the
kennel's `[[unix.allow]]` list, the same settled grant the shim consumed. On allow it performs the
`connect()` itself, host-side, and returns the connected fd in the reply as a `BINDER_TYPE_FD`; on deny it
returns a failed reply and audits it. The workload receives an already-connected socket and never holds a
path into the host's AF_UNIX namespace; the path does not appear in the constructed view at all, which closes
the residual where a workload could enumerate the socket paths it was granted, or probe for ones it was not.
The grant is exercised at the call, audited at the call, and the workload uses the connection without ever
reaching the name behind it (`mediate-use-not-reach`). The D-Bus facade and the network facade are larger,
each parsing a foreign wire protocol, and each takes its own chapter; the AF_UNIX facade is the one that
shows the move whole.

## 3.5 Control plane, not data plane

What the workload gets back is an fd, and that is the point at which `kenneld` leaves. The connected socket
flows its bytes directly between the workload and the far end; `kenneld` brokered the connection and then
stepped out of the path it brokered, parsing control-plane structures and never the payload stream
(`control-not-data-plane`). The fd and shared-memory object types are permitted within a single instance,
between two parties already inside the same trust boundary, so passing the connected socket to the workload
is sound.

Reaching a service in another kennel is a separate matter, gated by bilateral policy: the edge exists only
where both kennels' signed policy declares it, a `provide` on one side and a `consume` on the other (T5.2).
How that reach is mediated across the instance boundary is the subject of the inter-kennel chapter, not this
one.

## 3.6 The crate and the unsafe

The binder ioctl ABI is hand-rolled in `kennel-lib-binder`, built in the same shape as the BPF loader crate,
with `unsafe` confined to a single file holding the ioctl FFI and the crate listed among the few that carry
it. There is no `libbinder`: that library and its NDK form carry Android-specific dependencies, so the crate
binds the kernel's stable binder UAPI directly, the way the BPF crate compiles against the kernel headers
(`own-your-supply-chain`, and `dont-roll-your-own` for what the kernel already provides). The split between
mechanism and policy is the BPF crate's split again: `kennel-lib-binder` owns the command loop, the encode
and decode of the command stream and transaction data, the context-manager looper primitive, device
allocation, the protocol-version check that requires binder version 8 at open, and death-notification
plumbing, and `kenneld` owns which registrations and resolutions are
permitted, the registries, the reserved services, and cross-kennel mediation, under `#![forbid(unsafe_code)]`. The
consequence worth stating is where the untrusted input lands. The command-stream decoder consumes bytes the
workload controls, so it is an untrusted-input parser, reachable from inside every kennel because the bus is
unavoidable, and it carries a fuzz target for that reason (T5.1). The unsafe is a small, separately reviewed,
fuzzed leaf; the policy brain that decides every crossing holds none of it (`rule-of-1`,
`quarantine-the-unsafe`).
