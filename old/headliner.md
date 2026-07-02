# What Project Kennel Is

Project Kennel is a reference monitor for the user level of a Linux workstation — the place where AI
coding agents, package install scripts, MCP servers, and freshly cloned build systems now run as
you, with your reach over your files, your keys, your sessions. The host level grew its own monitors
decades ago, in mandatory access control and the LSM framework; the user level, where the code that
now matters actually runs, never did. Kennel is one, built in user space from the kernel's own
primitives — Linux namespaces, Landlock, BPF, and seccomp, with a per-kennel IPC bus as the single
mediated gateway — assembled into a deny-by-default policy the workload cannot rewrite. It runs
unprivileged: not a kernel module, not a ptrace supervisor, but a reference monitor the confined
code has no standing to alter. It starts from a single observation: the code running under your uid
has stopped acting for you, and the permission model still treats its every action as yours.

It confines by deciding, for every resource class, what a workload sees and what each use of it
costs. What policy does not grant is not denied on access — it is not there: a filesystem holding
only the granted paths, a network that is an empty namespace, a socket with no name to connect to.
What cannot be made absent is reached only through a transaction the monitor authorises one call at
a time. The governing discipline is to do as little as possible, because every mechanism is a
surface and every line of mediation can be wrong, and the strongest way to secure a thing is to
arrange that the thing is not there to secure. Deny by default, grant only what is declared, and
make every deviation visible.

What this buys is a boundary you do not have to be right about the workload to hold. Kennel does not
ask whether the code is trustworthy, well-intentioned, or hostile, because that judgement is not an
input to the enforcement and so never gets to be wrong — the threat a workload poses is what it can
reach and do, not what it meant. This is confinement, not detection. The dog loves you and wrecks
the couch anyway, and the answer is to keep the couch safe from whatever the dog turns out to be.
And where a residual remains, the framework names it rather than papering over it, because a
confinement claim is worth only what it can actually enforce.
