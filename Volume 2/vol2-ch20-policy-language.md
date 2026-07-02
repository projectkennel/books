# 20. The policy language

*Generated from `schema/policy.toml.schema`. Current as of 0.5.0.*


## `[audit]`

`[audit]`: sink selection, per-class levels, and per-sink tuning

```
[audit]
# optional
sinks    = ["..."]
```
Contains: `[audit.dbus]`, `[audit.exec]`, `[audit.file]`, `[audit.filesystem]`, `[audit.journald]`, `[audit.network]`, `[audit.stdout]`, `[audit.syslog]`, `[audit.unix]`.


`sinks`
:   optional. Active sinks (`file`, `journald`, `syslog`, `stdout`). Default `["file"]`.


### `[audit.dbus]`

`[audit.dbus]` level.

```
[audit.dbus]
# optional
level    = "off" | "denies-only" | "summary" | "full"
```

`level`
:   optional. One of `off`, `denies-only`, `summary`, `full`. One of `off`, `denies-only`, `summary`, `full`.


### `[audit.file]`

`[audit.file]` tuning.

```
[audit.file]
# optional
compress_after_seconds = 0
dir      = "..."
retain_count = 0
rotate_at_bytes = "..."
```

`compress_after_seconds`
:   optional. Gzip a rotated file this many seconds after rotation.

`dir`
:   optional. Override the per-kennel directory (placeholders allowed).

`retain_count`
:   optional. Keep at most this many rotated files per class.

`rotate_at_bytes`
:   optional. Rotate at this size (e.g. `"64M"`, `"1G"`; bare = bytes).


### `[audit.journald]`

`[audit.journald]` — no fields; present to allow the empty table.


### `[audit.syslog]`

`[audit.syslog]` tuning.

```
[audit.syslog]
# optional
facility = "..."
```

`facility`
:   optional. Syslog facility (`user`, `daemon`, `auth`, …). Default `user`.


## `[cap]`

`[cap]`: capabilities and `no_new_privs`.

```
[cap]
# optional
bounding_set = ["..."]
no_new_privs = true
```

`bounding_set`
:   optional. The capability bounding set to retain (empty drops them all).

`no_new_privs`
:   optional. `PR_SET_NO_NEW_PRIVS`. A framework invariant once resolved (must be true).


Example, from `toml/templates/base-bwrap`:

```
[cap]
no_new_privs = true
bounding_set = []
```

## `[[consumes]]`

One `[[consumes]]` entry, a capability this kennel reaches over the mesh.

```
[[consumes]]
# required
name     = "..."
shape    = "af-unix" | "dbus-name" | "binder-connector"
# optional
at       = "..."
env      = ["..."]
key      = "..."
required = true
# decoration
reason   = "..."
```

`at`
:   optional. Where the brokered connector is delivered, in this kennel's own view.

`env`
:   optional. Environment variable(s) synthesised into this kennel to name the connector.

`key`
:   optional. An optional private match token; must match the provider's.

`name`
:   required. The capability's public identifier, resolved against the catalogue at runtime.

`reason`
:   decoration. Why this capability is consumed (required).

`required`
:   optional. Whether the capability's absence fails kennel construction. Hard dependency by

`shape`
:   required. The transport it expects; the broker refuses a mismatched shape. One of `af-unix`, `dbus-name`, `binder-connector`.


Example, from `toml/templates/gui-session`:

```
[[consumes]]
name = "org.projectkennel.wayland"
shape = "af-unix"
at = "/tmp/wayland-0"
required = true
reason = "the confined desktop session reaches its display server — a broker-spawned nested compositor — over the mesh"
```

## `[dbus]`

`[dbus]`: D-Bus mediation.

Contains: `[dbus.audit]`, `[dbus.session]`, `[dbus.system]`.


### `[dbus.audit]`

`[dbus.audit]`: per-kennel D-Bus call audit verbosity.

```
[dbus.audit]
# optional
level    = "off" | "summary" | "full"
```

`level`
:   optional. Verbosity (`"off"`, `"summary"`, `"full"`). One of `off`, `summary`, `full`.


### `[dbus.session]`

`[dbus.session]`: the user session bus (the common case: notifications, portals).

```
[dbus.session]
# optional
enabled  = true
```
Contains: `[dbus.session.allow]`, `[dbus.session.deny]`.


`enabled`
:   optional. Whether this bus is reachable at all. Absent/`false` ⇒ no connection to this bus.


#### `[dbus.session.allow]`

`[dbus.<bus>.allow]`: what the kennel may reach (an allowlist; default-deny).

```
[dbus.session.allow]
# optional
broadcast = ["..."]
call     = ["..."]
own      = ["..."]
talk     = ["..."]
```

`broadcast`
:   optional. Signals the kennel may receive (a subset of senders it may `talk` to).

`call`
:   optional. Finer than `talk`: specific `destination=interface.member` calls.

`own`
:   optional. Names the kennel may own (be addressable as). Almost always empty.

`talk`
:   optional. Destinations the kennel may call methods on and receive replies/signals from


## `[env]`

`[env]`: environment curation.

```
[env]
# optional
deny     = ["..."]
pass     = ["..."]
set      = "..."
```

`deny`
:   optional. Variables denied even if passed (globs allowed).

`pass`
:   optional. Variables passed through from the caller's environment (globs allowed).

`set`
:   optional. Variables forced to a specific value. Declared last: as a TOML table it must


Example, from `toml/templates/base-bwrap`:

```
[env]
set = { TMPDIR = "/tmp", NO_PROXY = "" }
```

## `[exec]`

`[exec]`: what may be `execve`'d.

```
[exec]
# optional
allow    = ["..."]
deny     = ["..."]
deny_setcap = true
deny_setgid = true
deny_setuid = true
deny_writable = true
path     = ["..."]
shell    = "..."
```

`allow`
:   optional. Allowlisted binary paths (the execve allowlist). Execution is deny-by-default:

`deny`
:   optional. Denylisted absolute paths or globs.

`deny_setcap`
:   optional. Refuse file-capability binaries (framework invariant).

`deny_setgid`
:   optional. Refuse setgid binaries (framework invariant).

`deny_setuid`
:   optional. Refuse setuid binaries at execve (framework invariant once resolved).

`deny_writable`
:   optional. Refuse execution of files in writable paths (framework invariant).

`path`
:   optional. `PATH` search roots the resolver records for the workload's environment.

`shell`
:   optional. The kennel's login shell: the synthetic-`passwd` `pw_shell` and


Example, from `toml/templates/argv-tool`:

```
[exec]
allow = ["/bin/echo", "/usr/bin/echo", "/bin/cat", "/usr/bin/cat", "/bin/true", "/usr/bin/true", "/bin/sh"]
```

## `[fs]`

`[fs]` and its sub-tables.

```
[fs]
# optional
deny     = ["..."]
exclusive = ["..."]
read     = ["..."]
write    = ["..."]
```
Contains: `[fs.dev]`, `[fs.home]`, `[fs.proc]`, `[fs.tmp]`.


`deny`
:   optional. Categorical denies (belt-and-braces over the constructed view). Replace or increment

`exclusive`
:   optional. Writable paths bound **exclusively** (T2.8): while the kennel runs, `kenneld`

`read`
:   optional. Paths granted read (and directory traversal / execute). Replace (`read = ["…"]`) or

`write`
:   optional. Paths granted write. Replace or increment at the same key.


Example, from `toml/templates/argv-tool`:

```
[fs]
read = ["/usr/**", "/bin/**", "/lib/**", "/lib64/**"]
```

### `[fs.dev]`

`[fs.dev]`: the minimal `/dev`.

```
[fs.dev]
# optional
allow    = ["..."]
```
Contains: `[[fs.dev.passthrough]]`.


`allow`
:   optional. The trivial pseudo-device baseline bound into the kennel's `/dev` (`/dev/null`,


**`[[fs.dev.passthrough]]`** entries (or `{ add, remove }` increment), optional:

`group`
:   optional. The owning group that gates access (e.g. `dialout`, `modem`, `dip`). Access is

`path`
:   optional. The device node, an absolute path under `/dev` (e.g. `/dev/ttyUSB0`,

`reason`
:   decoration. Why this device is exposed (required).

`threats`
:   decoration. Threat tags, required to carry an `exposed` tag (passthrough widens the


Example, from `toml/templates/base-bwrap`:

```
[fs.dev]
allow = [
    "/dev/null", "/dev/zero", "/dev/random", "/dev/urandom",
    "/dev/tty", "/dev/pts/**",
]
```

### `[fs.home]`

`[fs.home]`: the constructed `$HOME` view.

```
[fs.home]
# optional
persist  = ["..."]
readonly = true
shadow   = true
```

`persist`
:   optional. Home-relative paths that **persist** across runs. By default the

`readonly`
:   optional. Make the constructed `$HOME` **read-only** (default: writable). The home root

`shadow`
:   optional. Whether `$HOME` is shadowed by a constructed view (must be true once resolved).


Example, from `toml/templates/base-bwrap`:

```
[fs.home]
shadow = true
```

### `[fs.proc]`

`[fs.proc]`: procfs hidepid.

```
[fs.proc]
# optional
hidepid  = true
```

`hidepid`
:   optional. Mount `/proc` with `hidepid=2`.


Example, from `toml/templates/base-bwrap`:

```
[fs.proc]
hidepid = true
```

### `[fs.tmp]`

`[fs.tmp]`: the private `/tmp` tmpfs.

```
[fs.tmp]
# optional
size     = "..."
writable = true
```

`size`
:   optional. Size cap in human form (`"512M"`, `"1G"`).

`writable`
:   optional. Whether the workload may **write** to its `/tmp` tmpfs (the Landlock write grant). Absent ⇒


Example, from `toml/templates/base-bwrap`:

```
[fs.tmp]
writable = true
size = "512M"
```

## `[identity]`

`[identity]`: the workload's identity inside the kennel.

```
[identity]
# optional
group    = "..."
groups   = ["..."]
user     = "..."
```

`group`
:   optional. The workload's masked **primary** group name (synthetic `/etc/passwd` `pw_gid`

`groups`
:   optional. Supplementary group names to retain (e.g. `["dialout", "plugdev"]`). The user

`user`
:   optional. The workload's masked user name, `$USER`/`$LOGNAME` and the synthetic


## `[lifecycle]`

`[lifecycle]`: TTL and TTL action. `ttl` is the human form (`"8h"`); the

```
[lifecycle]
# optional
ttl      = "..."
ttl_action = "exit" | "warn" | "renew"
```

`ttl`
:   optional. Time-to-live in human form (`"8h"`, `"1h"`, `"30m"`).

`ttl_action`
:   optional. What to do at TTL expiry: `"exit"` (alias `"stop"`, the default) ends the One of `exit`, `warn`, `renew`.


Example, from `toml/templates/argv-tool`:

```
[lifecycle]
ttl = "5m"
ttl_action = "exit"
```

## `[[mutable]]`

One `[[mutable]]` manifest entry: a leaf field a spawn of this template may write.

```
[[mutable]]
# optional
field    = "..."
freeform = true
from     = ["..."]
match    = ["..."]
max      = 0
oneof    = ["..."]
type     = "..."
under    = "..."
# decoration
reason   = "..."
```

`field`
:   optional. The dotted leaf-field path this entry opens (`net.proxy.allow`, `rootfs.writable`, `fs.write`).

`freeform`
:   optional. Freeform bound: no shape at all, the loud last-resort footgun. Any value is accepted; a

`from`
:   optional. Pool bound: the fixed set a spawn may append values from.

`match`
:   optional. Pattern bound: the pre-baked net-destination shapes an open value must match

`max`
:   optional. Pool bound: the maximum number of appended entries.

`oneof`
:   optional. Oneof bound: the enumerated member list a spawn selects from.

`reason`
:   decoration. The justification a `freeform` variant requires (the loud rule).

`type`
:   optional. Predicate bound: the value type (currently `relpath`).

`under`
:   optional. Predicate bound: the root the value resolves under (`RESOLVE_IN_ROOT`, traversal-free).


Example, from `toml/templates/argv-tool`:

```
[[mutable]]
field = "workload.argv"
freeform = true
reason = "the caller chooses the command to run within the [exec].allow floor; the cage contains it"
```

## `[net]`

`[net]` and its sub-tables.

```
[net]
# optional
mode     = "none" | "constrained" | "unconstrained" | "host"
proxy_listen_v4_address = "..."
proxy_listen_v6_address = "..."
# decoration
reason   = "..."
```
Contains: `[net.audit]`, `[net.bind]`, `[net.bpf]`, `[net.ipv6]`, `[net.proxy]`.


`mode`
:   optional. Egress mode: `"none"` (own empty net-ns, no interfaces), `"constrained"` (own net-ns, One of `none`, `constrained`, `unconstrained`, `host`.

`proxy_listen_v4_address`
:   optional. IPv4 proxy listen address as `"offset:port"` within the kennel's subnet. A

`proxy_listen_v6_address`
:   optional. IPv6 proxy listen address as `"offset:port"`.

`reason`
:   decoration. Required (non-empty) only when `mode = "host"`: the documented justification for


Example, from `toml/policies/interactive`:

```
[net]
mode = "host"
reason = "an interactive human shell needs direct, unmediated egress (git/ssh/curl) on the host network stack"
```

### `[net.audit]`

`[net.audit]`: per-kennel egress audit log.

```
[net.audit]
# optional
level    = "summary" | "full"
log_path = "..."
```

`level`
:   optional. Audit verbosity (`"summary"`, `"full"`). One of `summary`, `full`.

`log_path`
:   optional. Where the per-kennel egress JSONL log is written.


Example, from `toml/templates/base-confined`:

```
[net.audit]
log_path = "~/.local/state/kennel/<kennel>/network.jsonl"
level = "summary"
```

### `[net.bind]`

`[net.bind]`: bind-address rewriting policy (the wildcard-rewrite knobs; the bind

```
[net.bind]
# optional
allow_host_loopback_v4 = true
allow_host_loopback_v6 = true
allowed_ports = ["..."]
in6addr_any_policy = "rewrite" | "deny"
inaddr_any_policy = "rewrite" | "deny"
min_port = 0
```

`allow_host_loopback_v4`
:   optional. Whether binding the host IPv4 loopback is permitted.

`allow_host_loopback_v6`
:   optional. Whether binding the host IPv6 loopback is permitted.

`allowed_ports`
:   optional. Explicit allowlist of bindable ports. When non-empty, the workload may

`in6addr_any_policy`
:   optional. What to do with a wildcard IPv6 bind. One of `rewrite`, `deny`.

`inaddr_any_policy`
:   optional. What to do with a wildcard IPv4 bind (`"rewrite"` / `"deny"`). One of `rewrite`, `deny`.

`min_port`
:   optional. Lowest bindable port.


Example, from `toml/templates/base-confined`:

```
[net.bind]
inaddr_any_policy = "rewrite"
in6addr_any_policy = "rewrite"
allow_host_loopback_v4 = false
allow_host_loopback_v6 = false
min_port = 1024
```

### `[net.bpf]`

`[net.bpf]`: the kernel/syscall ACL (the cgroup `connect4/6` + `bind4/6` BPF and the

```
[net.bpf]
# optional
deny_families = ["..."]
families = ["..."]
```
Contains: `[net.bpf.bind]`, `[net.bpf.connect]`.


`deny_families`
:   optional. Denied socket families (`inet_sock_create` returns EPERM): `AF_NETLINK`, `AF_PACKET`, …

`families`
:   optional. Permitted socket families (defence in depth; e.g. `["AF_INET", "AF_INET6", "AF_UNIX"]`).


#### `[net.bpf.bind]`

`[net.bpf.bind]`: the inbound BIND ACL (cidr + ports, deny-first).

Contains: `[[net.bpf.bind.allow]]`, `[[net.bpf.bind.deny]]`.


**`[[net.bpf.bind.allow]]`** entries (or `{ add, remove }` increment), optional:

`cidr`
:   optional. The CIDR (`"10.0.0.0/8"`, a bare address, or `"*"` = `0.0.0.0/0` + `::/0`).

`ports`
:   optional. Permitted ports (empty = any port).

`protocol`
:   optional. Transport protocol (`"tcp"`, `"udp"`, `"any"`). One of `any`, `tcp`, `udp`.

`reason`
:   decoration. Why this rule exists (required).

`threats`
:   decoration. Threat tags.


**`[[net.bpf.bind.deny]]`** entries (or `{ add, remove }` increment), optional:

`cidr`
:   optional. The CIDR (`"10.0.0.0/8"`, a bare address, or `"*"` = `0.0.0.0/0` + `::/0`).

`ports`
:   optional. Permitted ports (empty = any port).

`protocol`
:   optional. Transport protocol (`"tcp"`, `"udp"`, `"any"`). One of `any`, `tcp`, `udp`.

`reason`
:   decoration. Why this rule exists (required).

`threats`
:   decoration. Threat tags.


### `[net.ipv6]`

`[net.ipv6]`: IPv6-specific options.

```
[net.ipv6]
# optional
force_v6only = true
```

`force_v6only`
:   optional. Force `IPV6_V6ONLY=1` so a dual-stack socket cannot escape the v4 rewrite.


Example, from `toml/templates/base-confined`:

```
[net.ipv6]
force_v6only = true
```

### `[net.proxy]`

`[net.proxy]`: the user-space egress policy the per-kennel proxy enforces

Contains: `[net.proxy.deny]`, `[[net.proxy.allow]]`.


**`[[net.proxy.allow]]`** entries (or `{ add, remove }` increment), optional:

`cidr`
:   optional. A CIDR destination, when the rule is by-address rather than by-name.

`name`
:   optional. The destination host (or dot-prefixed suffix). Mutually informative with `cidr`.

`ports`
:   optional. Permitted ports.

`protocol`
:   optional. Transport protocol (`"tcp"`, `"udp"`, `"any"`). One of `any`, `tcp`, `udp`.

`reason`
:   decoration. Why this destination is permitted (required).

`threats`
:   decoration. Threat tags.

`tls`
:   optional. `tls.required` and friends.


#### `[net.proxy.deny]`

`[net.proxy.deny]`: the deny table: the non-removable `invariant` floor and the

Contains: `[[net.proxy.deny.invariant]]`, `[[net.proxy.deny.policy]]`.


**`[[net.proxy.deny.invariant]]`** entries, optional:

`cidr`
:   required. The denied CIDR (e.g. `"169.254.169.254/32"`).

`reason`
:   decoration. Why the deny exists (required).

`threats`
:   decoration. Threat tags.


**`[[net.proxy.deny.policy]]`** entries (or `{ add, remove }` increment), optional:

`cidr`
:   required. The denied CIDR (e.g. `"169.254.169.254/32"`).

`reason`
:   decoration. Why the deny exists (required).

`threats`
:   decoration. Threat tags.


## `[[provides]]`

One `[[provides]]` entry, a capability this kennel offers over the mesh.

```
[[provides]]
# required
name     = "..."
shape    = "af-unix" | "dbus-name" | "binder-connector"
# optional
endpoint = "..."
key      = "..."
# decoration
reason   = "..."
```

`endpoint`
:   optional. Where the capability is exposed, in the provider's own view. Optional: an omitted

`key`
:   optional. An optional private match token, never advertised in the catalogue.

`name`
:   required. The capability's public identifier, what the catalogue advertises. A reserved

`reason`
:   decoration. Why this capability is offered (required).

`shape`
:   required. The typed transport. One of `af-unix`, `dbus-name`, `binder-connector`.


Example, from `toml/templates/dbus-broker`:

```
[[provides]]
name = "org.projectkennel.dbus-broker"
shape = "binder-connector"
endpoint = "/dev/binderfs-mesh/binder"
reason = "kenneld pushes per-consumer ACCEPT_SESSION (bus + method filter) to the broker's control node on the mesh"
```

## `[rootfs]`

`[rootfs]`: an OCI image unpacked as the kennel's root filesystem.

```
[rootfs]
# optional
image    = "..."
path     = "..."
persistence = "discard" | "persist"
readonly = ["..."]
writable = ["..."]
# decoration
reason   = "..."
```

`image`
:   optional. The `image@sha256:…` the build pulled from; the runner refuses unless it equals the

`path`
:   optional. The unpacked image rootfs (the store entry's `rootfs/`).

`persistence`
:   optional. Rootfs persistence: `"discard"` (default) | `"persist"`. `"persist"` is a One of `discard`, `persist`.

`readonly`
:   optional. Closure-lock: rootfs paths Landlock denies writes to, the executable-closure

`reason`
:   decoration. Why this substrate is trusted (required; the substrate-trust waiver is loud).

`writable`
:   optional. Closure-lock holes: rootfs paths kept writable, carved back out of `readonly`


## `[seccomp]`

`[seccomp]`: the seccomp filter (source carries a deny list; the resolver

```
[seccomp]
# optional
allow    = ["..."]
deny     = ["..."]
profile  = "..."
```

`allow`
:   optional. Syscalls explicitly allowed.

`deny`
:   optional. Syscalls denied on top of the profile.

`profile`
:   optional. The baseline profile name (`"default"`).


Example, from `toml/templates/base-bwrap`:

```
[seccomp]
profile = "default"
deny = [
    "userfaultfd", "perf_event_open", "bpf",
    "process_vm_readv", "process_vm_writev",
    "kexec_load", "kexec_file_load",
    "mount", "umount", "umount2", "pivot_root",
    "swapon", "swapoff", "reboot",
    "init_module", "finit_module", "delete_module",
    "personality",
]
```

## `[service]`

`[service]`: the supervision discipline for a service kennel.

```
[service]
# optional
backoff  = "..."
max_attempts = 0
restart  = "always" | "on-failure" | "never"
```

`backoff`
:   optional. Initial delay before a restart in human form (`"500ms"`, `"2s"`, default `"500ms"`); doubles

`max_attempts`
:   optional. Restarts within the crash-loop window before declared-but-failed (default `5`; must be ≥ 1).

`restart`
:   optional. Restart discipline: `always` / `on-failure` (default) / `never`. One of `always`, `on-failure`, `never`.


Example, from `toml/templates/dbus-broker`:

```
[service]
restart = "on-failure"
```

## `[signature]`

The `[signature]` envelope carried by a signed artefact.

```
[signature]
# required
algorithm = "..."
key_id   = "..."
signature = "..."
# optional
signed_fields = ["..."]
```

`algorithm`
:   required. Signature algorithm. Must be `"sshsig"` ([`SSHSIG_ALGORITHM`]).

`key_id`
:   required. Identifies the signing key in the trust store. The SSHSIG also embeds the

`signature`
:   required. The armored SSHSIG (`-----BEGIN SSH SIGNATURE-----` …) over the canonical

`signed_fields`
:   optional. The top-level fields the signature covers (every field except


Example, from `toml/policies/interactive`:

```
[signature]
algorithm = "sshsig"
key_id = "kennel-maint-2026"
signature = "-----BEGIN SSH SIGNATURE-----\nU1NIU0lHAAAAAQAAADMAAAALc3NoLWVkMjU1MTkAAAAgKWVn2EUqe+ju7quWQv7aY/ihwM\npBFaipL7vU2UVH85IAAAAbcG9saWN5LnYxQHByb2plY3RrZW5uZWwub3JnAAAAAAAAAAZz\naGE1MTIAAABTAAAAC3NzaC1lZDI1NTE5AAAAQO4+Qm6EihZIVrHHJHc5lYaTh22kJbwk+8\nYVUolVJ+bBxwFC1WisLKlFSZ4fXR916/2Lo8NXG0LCGg+pvSOcygQ=\n-----END SSH SIGNATURE-----\n"
```

## `[spawn]`

`[spawn]`: the delegated-instantiation grant.

```
[spawn]
# optional
max_instances = 0
# decoration
reason   = "..."
```
Contains: `[[spawn.allow]]`.


`max_instances`
:   optional. Concurrent-instance ceiling across this grant's spawns, the fork-bomb bound.

`reason`
:   decoration. Why this delegation is extended (required; the spawn waiver is loud, validated at compile).


**`[[spawn.allow]]`** entries, optional:

`mutable`
:   optional. Optional per-requester narrowing: the subset of the template's `[[mutable]]` manifest fields

`template`
:   optional. The trust-store template name (`net-fetch`).


## `[ssh]`

`[ssh]`: per-kennel SSH egress (source-only).

```
[ssh]
# optional
allow_headless = true
```
Contains: `[[ssh.destinations]]`.


`allow_headless`
:   optional. Whether a granted key may be driven by a non-interactive (CI) kennel with no


**`[[ssh.destinations]]`** entries (or `{ add, remove }` increment), optional:

`dest`
:   optional. The SSH destination, in the form the host-side `ssh` is invoked with

`options`
:   optional. Host-side `ssh` invocation options for this destination, passed verbatim as argv

`reason`
:   decoration. Why this destination is granted (required).

`threats`
:   decoration. Threat tags.


## `[trust]`

`[trust]`: the masked workspace manifest (T2.8).

```
[trust]
# optional
manifest = true
on_change = "warn" | "freeze" | "kill"
```

`manifest`
:   optional. Maintain a `.trust-manifest.json` at the root of every writable/persistent

`on_change`
:   optional. What `kenneld` does when a watched trigger is mutated during the run: One of `warn`, `freeze`, `kill`.


## `[tty]`

`[tty]`: terminal hardening for an interactive (PTY) workload.

```
[tty]
# optional
filter_terminal_escapes = true
```

`filter_terminal_escapes`
:   optional. Filter the dangerous escape sequences a workload could write toward the


## `[unix]`

`[unix]`: `AF_UNIX` policy.

```
[unix]
# optional
abstract = "deny" | "allow"
```
Contains: `[[unix.allow]]`.


`abstract`
:   optional. Abstract-namespace socket disposition (`"deny"` / `"allow"`). One of `deny`, `allow`.


**`[[unix.allow]]`** entries (or `{ add, remove }` increment), optional:

`env`
:   optional. An environment variable to set to the shim path (e.g. `SSH_AUTH_SOCK`).

`name`
:   optional. A logical name (e.g. `"ssh-agent"`) for a per-kennel service instance.

`real`
:   optional. The real host socket path.

`reason`
:   decoration. Why this socket is granted (required).

`shim`
:   optional. The shim path the socket is bound at inside the kennel.

`threats`
:   decoration. Threat tags.


Example, from `toml/templates/dbus-broker`:

```
[unix]
```

## `[unsafe]`

`[unsafe]`: the advisory footgun umbrella.

Contains: `[unsafe.ptrace]`, `[unsafe.signal]`.


### `[unsafe.ptrace]`

`[unsafe.ptrace]`: ptrace across the kennel boundary (scoping from PID-ns + seccomp).

```
[unsafe.ptrace]
# optional
allow_from = ["..."]
allow_targets = ["..."]
```

`allow_from`
:   optional. Permitted sources.

`allow_targets`
:   optional. Permitted targets (`"self"`, …).


## `[workload]`

`[workload]`: the command the kennel runs, optionally pinned.

```
[workload]
# optional
argv     = ["..."]
cwd      = "..."
pinned   = true
sha256   = ["..."]
```

`argv`
:   optional. The command + args (`argv[0]` is the program). Absent ⇒ supplied at `kennel run`.

`cwd`
:   optional. Working directory inside the view (may carry a `~`/`<home>` placeholder).

`pinned`
:   optional. Refuse a CLI `--` override of `argv` unless `--force` (pin exactly what runs).

`sha256`
:   optional. Accepted lowercase-hex SHA-256 digests of the workload binary; the spawn verifies


Example, from `toml/policies/interactive`:

```
[workload]
argv = ["/bin/bash"]
```

## Common forms

**Threat tags**: carried inline on any grant that can widen surface, as `threats = { exposed = [...], mitigated = [...] }`.

**The increment**: any list field also accepts `[[<list>.add]]` / `[[<list>.remove]]`, folded over the inherited list at compile.