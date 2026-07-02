# 2. Process and privilege model

Chapter 1 set out the kernel facilities and how the confinement is woven from them. A kennel does not
assemble itself: a small set of processes builds each one and supervises it while it runs, and the
reference monitor's tamperproof property turns, in mechanism, on which of those processes holds privilege
and for how long. The shape of that set is where the detail begins, which processes exist while a kennel
runs, what privilege each carries, and where the single privileged step sits. The design register's
`split-the-uid` reduces, here, to one question asked of every process on the host: which file capability
does it hold, and for how long.

The answer almost everywhere is none. Of the processes that exist while a workload runs, exactly one
holds host-elevated privilege, it holds it for the length of one construction, and then it is gone.

## 2.1 The processes

A running kennel is a small set of processes, and naming them is most of the privilege story.

`kennel` is the operator's entry point, a 13-line shim (`kennel-shim`) that holds no authority of its
own: it detects which environment it is in and execs the right libexec, the host-side CLI
(`kennel-cli`) on the host or the in-cage spawn path inside a kennel. `kenneld` is the per-user
supervisor, socket-activated by `systemd --user` on the first `kennel run` and resident for the
session, one per logged-in user. It runs as the user with no capabilities. It validates and executes the
settled policy for each kennel, drives construction, takes binder node 0, drains the audit ringbuf, and
reaps the workload, and it does all of it unprivileged. That a daemon this central holds no capability is the
first half of `split-the-uid` in mechanism: `kenneld` has the operator's identity and none of root's
authority, and the authority it needs for the one privileged step it does not hold but borrows, briefly,
from a separate binary.

`kennel-privhelper` is that binary, and the only one on the host with elevated privilege. Beneath it sit
the processes that hold no host privilege. `kennel-bin-init` is the kennel's PID 1: a trusted root-owned
binary, trapped inside the new namespaces with no host capability, that supervises the facades and the
workload, reaps the kennel's processes, and restarts a facade if one dies. It holds PID 1 so that no
untrusted workload does, keeping that position, with its reaping duties and its host-facing reparent, on a
trusted process rather than on the code the kennel exists to confine. The rest hold no host privilege: the
per-kennel `host-netproxy` and the SSH bastion are plain user processes, the in-kennel facades are
confined workload-side code, and the workload itself is dropped to the operator with its bounding set
cleared. `host-netproxy` is a separate process for an architectural reason rather than a privilege one: it
is the post-policy dialer, doing the blocking, adversarial network I/O once `kenneld` has made the
decision, so that I/O never sits inside the supervisor (`control-not-data-plane`). The same eviction is made
on the other adversarial input a session produces: the workload's terminal output, with its attacker-shaped
ANSI escapes, is parsed by the unprivileged `kennel` CLI and never at the daemon, which sees the PTY as
opaque bytes to route. Between them, network I/O and terminal parsing are the two data-plane jobs kept out
of the supervisor, which is what leaves it a pure control plane. The privilege-bearing
surface of the whole system is one small binary and three smaller sub-helpers, described next; everything
else runs as the user.

## 2.2 One privileged component

`kennel-privhelper` is installed with the file capabilities `cap_setuid`, `cap_setgid`, `cap_setfcap`, `cap_sys_admin=ep`,
setuid root at mode `4755` only as a fallback for filesystems that cannot carry capability xattrs. Each
of the four earns its place and no more is taken. `cap_setuid`, `cap_setgid`, and `cap_setfcap` cover
writing the identity map and dropping to the operator; `cap_setfcap` is needed because the map's
`0 0 1` line and the operator line are written in a single `write(2)`. `cap_sys_admin` is the kernel's
gate on writing a `uid_map` that maps host uid 0, and it covers the mount and `pivot_root` construction
of the view. The factory holds nothing else: no `cap_net_admin`, no BPF capability.

The rarer privileged acts are not folded into the factory's capability set; they are delegated to three
single-purpose sub-helpers the factory execs only when a policy needs them, each carrying one capability
for one job. `kennel-privhelper-net` holds `cap_net_admin` and mirrors the kennel's loopback prefixes
onto the host's `lo` over netlink, bringing the same `/28` and `/64` up on both sides so the host can
present a kennel's inbound listeners at the kennel's own address; the two are identical by construction,
not connected. `kennel-privhelper-bpf` holds `cap_bpf`, `cap_net_admin`, `cap_perfmon` and, in
host network mode only, attaches the egress BPF to the kennel's cgroup. `kennel-privhelper-mounts` holds
`cap_sys_admin` and over-mounts the exclusive-bind sentinel. This is `rule-of-1` and `quarantine-the-unsafe`
carried into privilege itself: the host-elevated surface is partitioned so that the capability for a
narrow job lives in a binary that can do only that job, and holding `cap_net_admin` there grants the one
scoped act, not arbitrary network administration (T2.4).

## 2.3 The factory: privilege bounded to one construction

The privhelper is a kennel factory. Its one provisioning op, `construct`, does all of the privileged
work for a kennel in a single short-lived invocation; the only standalone op beside it is `del-addr`,
the address removal at teardown.

`kenneld` invokes `kennel-privhelper construct` over a `SOCK_SEQPACKET` socketpair and sends the
construction half of the Plan: the uid and gid maps, the loopback configuration and the per-kennel
addresses to add, the binderfs parameters, the view bind list, the pivot target, the egress BPF payload
as a framed tail, and any stdio or pty descriptors over `SCM_RIGHTS`. The privhelper parses this
host-side before it holds any namespace, and parses it as hostile: the operator line of the map is the
caller's real uid taken from `/proc` ownership and never read from the wire, and the request is refused
if it names an address outside the kennel's allocated IPv4 `/28` or IPv6 `/64`, a cgroup the caller does
not own, a gid the caller is not in, or any uid but the caller's own. The decoder for that half is
bounded and fuzzed, because a bug in it is the one bug at this layer that matters (T5.4).

Only after validation does privilege touch the kernel. The factory holds neither `cap_net_admin` nor the
BPF caps, so it drives the host-`lo` loopback mirror and the host-mode egress BPF attach by exec'ing the
narrow sub-helpers; it provenance-checks and opens the root-owned `kennel-bin-init` by descriptor,
and then `clone3`s a child with `CLONE_NEWUSER` | `NEWNS` | `NEWPID` | `NEWIPC` | `INTO_CGROUP`, adding `NEWNET` in every
mode but host, so the child is PID 1 of a fresh namespace set, born directly inside the kennel's cgroup
rather than migrated into it afterward. The migration was not free: profiling added to the spawn path in
0.3.0 traced 10 to 13 ms of otherwise-idle stall to the post-hoc move into the cgroup, and removing it by
cloning into the cgroup is most of what brings a kennel up in under 10 ms from the command line. The dynamic
spawn an agent triggers directly is faster again, an observed 3.5 to 6.5 ms depending on the hardware,
because it skips the CLI and the process startup that comes with it, and that margin is what makes an
agent's spawn-use-reap loop viable. It also closes the window in which a freshly-migrated
process runs briefly unaccounted, so the cgroup's limits hold from the first instruction. The user namespace is operator-owned: the child clones as the
operator and self-escalates to the kennel's uid 0 to do construction, which is precisely what lets the
unprivileged `kenneld` reach the new binderfs instance later through `/proc/<init>/root`. In that child
the factory writes the maps, brings up the in-namespace loopback, builds the view, mounts binderfs and
chowns the device to the operator, `pivot_root`s and detaches the host root, and `fexecve`s
`kennel-bin-init` by the descriptor it opened before the pivot, with empty argv and envp, because the
host path to that binary no longer exists inside the view.

Then the factory exits. It is not a supervisor and not a reaper proxy; it reports the init's host pid and
is gone. `kennel-bin-init`, now PID 1 of its own namespace, outlives it, reparents to `kenneld` (which
marked itself a child subreaper at startup), and `kenneld` waits on it directly for the workload's exit
status. No privileged process is resident for the life of a kennel, and none is shared across kennels.
The privilege is bounded to the single map-writing construction and then withdrawn, which is the
conservative half of a deliberate trade: a long-running privileged daemon owning the same capabilities
would cost fewer execs and buy continuous privileged exposure, and the current design refuses that
exposure. The factory child is the only transient uid-0 actor in the system, and it never runs with host
root visible to it, so the worst a construction-half decoder bug can be is a host-root bug, which is why
that decoder is the most heavily checked code at this layer (T5.4).

## 2.4 The trusted init and the drop

`kennel-bin-init` is the root-owned binary the factory execs as PID 1, and it is deliberately small (338
SLOC) and `#![forbid(unsafe_code)]`. It makes no policy decision and runs no mount, netlink, device, or
filesystem-lookup code; that work was done by the factory before the pivot. Its path comes from the
root-owned deployment configuration; the privhelper verifies the binary is root-owned and not group- or
other-writable, opens it before the `clone3`, and `fexecve`s it by that descriptor. Exec by descriptor is
the only way in, not an optimisation: after the `pivot_root` the host path the binary came from is gone
from the view, so there is nothing left to exec by name, and the descriptor pins the exact file vetted
before the pivot, with no window in which a symlink or a swapped path could redirect it. The root ownership
is tamperproofing rather than power: root confers no host capability inside the kennel, but a root-owned
binary is one the operator-uid workload cannot rewrite, and PID 1 running as the kennel's uid 0 is one the
operator cannot signal or `ptrace`. It is launched into a cage where its root means only that the workload
cannot touch it. Once running, it pulls the supervision half
of the Plan from `kenneld` over the binder bus, then forks and supervises the facades and the workload.

The workload is dropped. It runs as the operator uid, never as the kennel's uid 0; only `kennel-bin-init`
holds that, trapped post-pivot with no ambient host capability (T3.1). `PR_SET_NO_NEW_PRIVS` is set
unconditionally before the workload runs, the bounding set is cleared per policy, Landlock is sealed, the
cgroup BPF is attached, and `setrlimit` caps are applied. Against the classic escalation, a setuid binary
executed inside the kennel, the framework's `exec` invariants `deny_setuid`, `deny_setgid`, and
`deny_setcap` hold categorically, so a workload cannot climb back up through a binary it runs (T3.1).
There is identity here, the operator's uid, and there is no authority attached to it that the policy did
not grant: the second half of `split-the-uid`, now at the bottom of the process tree.

## 2.5 Two identities, not one

That arrangement is where Kennel parts company with the common rootless container. A rootless container
maps the invoking user to uid 0 inside its user namespace and runs the workload as root there; the
confinement is the namespace boundary, and inside it the workload is root, with nothing between it and
whatever the namespace still reaches. Kennel's user namespace carries two identities instead. The `0 0 1`
line maps host root to the kennel's uid 0, and that root is the trusted side: the construction child that
self-escalates to it to mount and pivot, and `kennel-bin-init` that holds it as PID 1. The operator line
maps the operator to itself, and that is the workload, unprivileged, never uid 0.

Two identities in one namespace means the ordinary Unix DAC line between root and a user is kept inside the
kennel rather than collapsed. The trusted components are root and the workload is not, so the process the
kennel exists to confine cannot write a root-owned path, cannot chown a file it does not own, cannot do any
of what the discretionary model reserves to uid 0, and it is stopped by ownership alone, before Landlock,
seccomp, or the namespaces are consulted. The maps are precise identity lines, not a subuid range, and the
granted gids are mapped the same way; but in a namespace whose only identities are root and a non-root
user, gids are ornamental, since the privilege boundary is the uid line and nothing hangs off group
membership. What stands inside the kennel is the separation Unix has drawn between a privileged owner and
an unprivileged user for as long as it has existed, with the framework on the privileged side and the
workload on the other.

The inversion is deliberate. Rootless buys the workload root inside a box and trusts the box; Kennel keeps a
real root and a real non-root user in the same namespace and puts the workload on the unprivileged side of a
line the kernel has enforced for decades. The namespace, Landlock, and seccomp are the confinement above;
this is the floor beneath them, and it is the one layer that asks for no new mechanism, because it is only
uid 0 declining to be the workload's.

## 2.6 The unsafe at this layer

The privilege model is also where the volume's quarantined `unsafe` mostly lives. Two of the five
unsafe-bearing crates are the kernel-interface surface of the privilege model: `kennel-lib-syscall` (946 SLOC),
which holds the raw syscalls, the seccomp filter, and the namespace primitives, and `kennel-lib-landlock`
(249 SLOC), which holds the Landlock ruleset construction; `kennel-lib-bpf` (811 SLOC), the third, is the
loader the factory and `kenneld` use to attach the egress program. Each is small, single-purpose, in the
TCB, and the only place its kind of `unsafe` is permitted to appear (`quarantine-the-unsafe`).

The point worth drawing out is that privilege and `unsafe` are quarantined separately, and neither
coincides with the binaries one would expect. `kenneld` (7319 SLOC) and `kennel-privhelper` (1764) are
the two privileged anchors of the system, and both carry no `unsafe` of their own: the privhelper's power
is file capabilities, and the few `unsafe` calls its construction needs are borrowed from
`kennel-lib-syscall`. So the largest privileged binary holds no `unsafe`, and the crates that hold
`unsafe` hold no privilege of their own. A reader auditing for memory hazard and a reader auditing for
privilege are reading two different, small, named sets of crates (`read-by-the-hostile`), and that
`kenneld`, the central daemon and the thing an attacker most wants, is both unprivileged and
memory-safe-by-default is the shape the rest of the volume builds on (T5.3).

The processes and their privilege are the static picture. How they talk to each other while a kennel runs
is the next mechanism the design left abstract, and it has a single answer on Linux: the binder.
