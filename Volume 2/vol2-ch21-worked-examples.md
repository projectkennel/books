# 21. Worked examples

A single confined thing, followed from the floor to a running shell. Each tier is a real shipped file; the prose is the file's own. Read top to bottom and you watch confinement accrete: the floor denies, the template widens it four different ways, the leaf pins it.


## `base-confined` — the floor every kennel stands on

Template: base-confined — the floor every kennel stands on. Inherits: nothing — this is the root of every confined template. Threat catalogue: THREATS.md v0.4

The minimal confined posture: no_new_privs, setuid/setgid/setcap denial, the constructed-$HOME view, proxy-only egress, the cloud-metadata + link-local invariant denies (RFC1918 stays reachable — see [net]), a curated environment, and a defence-in-depth seccomp filter.

Deny-by-default across the board: exec.allow is EMPTY, which now denies ALL execution (execution is deny-by-default like fs and net) — so base-confined cannot run anything and is not usable on its own. A derived template/leaf adds the binaries it needs to `exec.allow`; the compiler then resolves and grants exactly the shared libraries those binaries link (see the `[lib]` section below). Only enforced sections appear here; sections the runtime does not implement (dbus/x11/ptrace/signal) are deliberately omitted — declaring them would warn.

See docs/design/05-templates.md and templates/README.md.

```
template_name = "base-confined"
```

### Capabilities (framework invariants)


```
[cap]
no_new_privs = true        # PR_SET_NO_NEW_PRIVS, always; cannot be set false
bounding_set = []          # drop the entire capability bounding set
```

### Execution (deny-by-default)


exec.allow is empty, which DENIES ALL EXECUTION: a merely-readable file is not executable. A derived template/leaf adds the binaries it needs; `permissive-exec` (a `**` entry) is the explicit opt-out that restores the open posture.

There is intentionally NO exec.deny list: under deny-by-default it would be moot (sudo/su/pkexec/… are not in any allowlist, so they never run; and the deny_* flags below + no_new_privs neuter setuid escalation regardless). A deny list that enforces nothing is theatre, so it is omitted rather than shipped as reassurance.

```
[exec]
allow = []
```

```
deny_setuid = true         # refuse setuid binaries at execve (framework invariant)
deny_setgid = true         # refuse setgid binaries (framework invariant)
deny_setcap = true         # refuse file-capability binaries
deny_writable = true       # refuse execution of files in writable paths
```

```
path = ["/usr/bin", "/usr/local/bin", "/bin"]
```

### Filesystem


The constructed view (fs.home, below): $HOME is a fresh tmpfs into which only granted paths are bound. Non-granted paths do not exist in the view (T1.1).

```
[fs]
# Read baseline: the curated base every dynamically-linked workload needs
# (§4.2 construction-by-absence). Only these subtrees are bound into the
# view; everything else under /usr (headers, source, /usr/local) is simply not
# present. The filesystem floor prevents data leakage; the real enforcement is
# at exec.allow|deny (Landlock FS_EXECUTE). Absent subtrees on this host (e.g.
# /usr/lib64 on usrmerge distros, /usr/libexec on Debian) are silently skipped.
read = [
    # The curated /usr base:
    "/usr/bin/**", "/usr/sbin/**",        # binary search path (Landlock gates exec)
    "/usr/lib/**",                        # shared libraries, locale, multiarch
    "/usr/lib64/**",                      # 64-bit lib path (Fedora/RHEL; skipped if absent)
    "/usr/libexec/**",                    # helper binaries (git-core etc; skipped if absent)
    "/usr/share/**",                      # arch-independent data (terminfo, zoneinfo, CAs, locale)
    # usrmerge compat:
    "/lib/**", "/lib64/**",
    # TLS root CAs + linker config (not under /usr):
    "/etc/ssl/**", "/etc/pki/**",
    "/etc/ld.so.conf", "/etc/ld.so.conf.d/**", "/etc/ld.so.cache",
    # update-alternatives symlink farm: many tools (awk→gawk, vi, editor, pager,
    # java, …) are reached via /usr/bin/<tool> -> /etc/alternatives/<tool> -> real
    # binary. Without /etc/alternatives in the view the symlink dangles and the tool
    # is "command not found". It is non-sensitive (symlinks only), bound read-only.
    "/etc/alternatives/**",
    # The libc/NSS files are SYNTHESISED per-kennel (scrubbed of host specifics),
    # not bound from the host: /etc/{hosts,resolv.conf,nsswitch.conf,services,
    # protocols,passwd,group,host.conf}. See kenneld::etc and §7.2.5.
    "/proc/self/**", "/proc/cpuinfo", "/proc/meminfo", "/proc/version",
    "/sys/devices/system/cpu/**",        # processor-count detection
]
```

```
# Write baseline: none. The workload's writable space is the constructed $HOME and
# the private /tmp (below); a usable template or leaf grants its project write paths.
write = []
```

```
# There is intentionally NO fs.deny list. The constructed view is deny-by-default:
# only fs.read/fs.write paths exist in it at all, so the host's ~/.ssh, ~/.aws,
# /etc/shadow, /dev/mem, … are simply absent — not present-but-denied. And a deny
# that fell *inside* a granted directory could not be enforced anyway (Landlock is
# allow-only and cannot subtract a single path). A long credential denylist here
# would be reassurance theatre; the real control is granting narrowly, not denying
# broadly. (T1.1/T2.1 are defended by the view's absence-by-default, not a denylist.)
```

```
# The constructed $HOME (T1.1). HOME is /home/<user> (the masked [identity].user,
# default `kennel`); granted ~/ paths are bound beneath it; the Landlock ruleset
# backstops on the resolved view (§7.2.3/.5). The home root is writable by default,
# but it is a fresh tmpfs — anything written directly there is ephemeral. Persistence
# is opt-in per path via `persist` (or a writable ~/ grant), which binds the real host
# inode read-write beneath the home. Set `readonly = true` to suppress the default
# home-write grant (only write-granted ~/ paths stay writable then).
[fs.home]
shadow = true
```

```
# Private /tmp (T1.1): a fresh tmpfs; the host /tmp is invisible.
[fs.tmp]
writable = true
size = "512M"
```

```
# Procfs: PID namespace + hidepid=2 — the workload sees only its own tree (T1.1, T1.6).
[fs.proc]
hidepid = true
```

```
# Minimal /dev: a constructed tmpfs with only these nodes bound in (T1.1, T1.6). Each
# granted node is also Landlock read/write/ioctl-able (§8.1).
[fs.dev]
allow = [
    "/dev/null", "/dev/zero", "/dev/random", "/dev/urandom",
    "/dev/tty", "/dev/pts/**",
]
```

### Libraries


There is no library allowlist, by design. Execution is gated by Landlock FS_EXECUTE, which the kernel enforces only at execve(2): on the allowlisted binary AND its dynamic loader (PT_INTERP/ld.so, resolved by the compiler from each exec.allow binary). Shared libraries are mmap'd by the loader, which Landlock does NOT gate, so they load with READ alone (07-3-exec) — the fs.read grants above (/usr, /lib, /lib64) already make them readable. A library therefore cannot be "execute-gated" under Landlock; the kennel makes no such claim rather than ship an unenforceable filter. (To stop a workload running NEW programs, that is exec.allow — default-deny; to stop it loading code in-process, the workload must not be an interpreter you handed arbitrary input.)

### Network


All egress funnels through a per-kennel SOCKS5/HTTP proxy; the cgroup BPF denies direct connect() to anything but the proxy (fail-closed). The proxy resolves names via the OS resolver and vets the answers against the allowlist + the invariant denies (rebinding defence) — there is no configurable [net.dns].

```
[net]
mode = "constrained"
# Both families' proxy listeners are on by default in the proxied modes; a family
# is enabled iff its address resolves (no separate on/off flag).
# Listener address is computed from the kennel's <tag>/<ctx> (§7.3.2); override the
# host offset/port within the kennel's own subnet with proxy_listen_v4_address =
# "offset:port" (offset 1..=14, default "1:1080"). Project Kennel injects
# HTTPS_PROXY / HTTP_PROXY / ALL_PROXY pointing at the computed proxy address.
```

```
# Invariant denies — the destinations that are NEVER a legitimate egress target,
# enforced deny-first by the proxy (even in `open` mode) and non-removable by any
# derived template or leaf (T1.6). Deliberately NARROW: cloud metadata (the SSRF
# crown jewel) and link-local only.
```

```
# RFC1918 / CGNAT are intentionally NOT invariant denies. Making private space
# permanently unreachable is self-defeating — a kennel routinely needs a local dev
# server, a LAN database, an internal registry, or a corp service. In `constrained`
# mode (the default) nothing private is reachable anyway unless a `[[net.proxy.allow]]`
# names it; in `open` mode the operator has opted into arbitrary egress. Either way
# that is the policy author's call, not an immovable floor.
[[net.proxy.deny.invariant]]
cidr = "169.254.169.254/32"
reason = "cloud metadata IPv4 — never permitted from a kennel (mandatory invariant)"
[[net.proxy.deny.invariant]]
cidr = "fd00:ec2::254/128"
reason = "AWS IPv6 metadata — never permitted"
[[net.proxy.deny.invariant]]
cidr = "fe80::/10"
reason = "IPv6 link-local — no legitimate egress destination"
```

```
# Bind: a wildcard bind (0.0.0.0 / ::) is rewritten to the kennel's private
# loopback address (so dev servers work but are reachable only from inside the
# kennel's address space); host loopback is not bindable; no privileged ports.
[net.bind]
inaddr_any_policy = "rewrite"
in6addr_any_policy = "rewrite"
allow_host_loopback_v4 = false
allow_host_loopback_v6 = false
min_port = 1024
```

```
# Force IPV6_V6ONLY=1 so a dual-stack socket cannot escape the v4 rewrite (T1.6).
[net.ipv6]
force_v6only = true
```

```
# Per-kennel egress audit log (one JSONL record per request; denies at higher
# level). Written by the proxy; persists across runs.
[net.audit]
log_path = "~/.local/state/kennel/<kennel>/network.jsonl"
level = "summary"
```

### AF_UNIX sockets


Default-deny; the constructed view contains only granted sockets. Abstract- namespace sockets are denied categorically — enforced natively by Landlock scoping (ABI 6, §8.1), not the legacy seccomp/AppArmor fallback. (T1.6.)

```
[unix]
abstract = "deny"
```

### Process introspection


The PID namespace hides every process outside the kennel; hidepid backstops it. (Cross-boundary ptrace and signalling are already prevented by the PID/user namespace — there is no separate control the runtime enforces, so none is declared. The advisory [unsafe.ptrace]/[unsafe.signal] sub-sections exist to *express* intent but warn that scoping comes from PID-ns/seccomp; this template needs neither. T1.6.)

### Environment


The environment is SYNTHESISED, not filtered. The spawn clears the inherited env entirely (env_clear) and rebuilds it: the framework sets HOME, PATH, USER, LOGNAME, SHELL (and forwards the caller's TERM); `set` below adds fixed extras. There is no `pass`/`deny` here — a passthrough/denylist is fiction when nothing is inherited in the first place (the host's secrets, AWS_*, *_TOKEN, … never reach the kennel because the whole env is wiped, not because they were named in a denylist).

```
[env]
set = { TMPDIR = "/tmp", NO_PROXY = "" }
```

### Seccomp (defence in depth)


Most enforcement is at higher layers (Landlock for files, cgroup BPF for net); this filter denies a small set of syscalls with no legitimate use here and a history of exploit-chain involvement. Default action: errno (EPERM).

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

### Resource limits (off by default)


setrlimit(2) caps, applied in the seal. Nothing is set here; a derived template or leaf opts in. Names are the short rlimit resources (nofile, nproc, as, cpu, data, fsize, core, stack, memlock, …); values are "soft" or "soft:hard", each a number (optional K/M/G) or "unlimited". Example:

```
[ulimits]
```

```
nofile = "8192"
```

```
nproc  = "512"
```

```
core   = "0"
```

```
[signature]
algorithm = "sshsig"
key_id = "kennel-maint-2026"
signature = "...envelope elided in print..."
```

## `interactive (template)` — the floor made into a usable human shell

Template: interactive — a credible human-driven shell.

A confined but genuinely usable workstation shell: bash + the standard coreutils, text tools, editors, archives, process inspection, and the common network tools, with HOST egress (a human is at the keyboard; direct egress on the host stack, the cloud-metadata invariant still applies). Execution is deny-by-default — the toolset below is exactly what runs; the compiler resolves each tool's library closure (`[lib]`, inherited).

$HOME and /tmp are writable (ephemeral); grant a project dir + persistence in your own leaf. For an offline shell, derive base-confined instead (or set net.mode).

```
# run it directly:
kennel run interactive -- /bin/bash
# or derive it and add your project:
#   template_base = "interactive"
#   [[fs.write.add]] path = "~/work"
```

```
template_name = "interactive"
template_base = "base-confined"
```

Exec floor composed from the fragment catalogue (05-templates.md §5.10): the shells + POSIX userland + capability bundles, instead of hand-listing them.

```
include = ["core-shell", "core-coreutils", "core-file-mutation", "core-archive", "net-clients", "vcs-git"]
```

Host egress: a human-driven shell needs unmediated network (curl, git clone, ssh, …) on the host stack — no SOCKS proxy. This shares the host network namespace and so reinstates the host-recon residual (T1.6), which is why `host` requires a reason; the cloud-metadata invariant deny + the net.bpf allowlist are still enforced via BPF/Landlock.

```
[net]
mode = "host"
reason = "an interactive human shell needs direct, unmediated egress (git/ssh/curl) on the host network stack"
```

```
# Re-list base-confined's read baseline (a template's fs.read replaces, not adds) and
# widen /proc to the whole namespaced procfs so `ps`/`top`/`free` see this kennel's
# own processes (the PID namespace already hides everything else).
[fs]
read = [
    "/usr/**", "/lib/**", "/lib64/**",
    "/etc/ssl/**", "/etc/pki/**",
    "/etc/ld.so.conf", "/etc/ld.so.conf.d/**", "/etc/ld.so.cache",
    "/etc/alternatives/**",   # awk→gawk, vi, editor, pager … symlink farm (else dangles)
    "/proc/**",
    "/sys/devices/system/cpu/**",
]
```

```
[exec]
shell = "/bin/bash"
# Only the binaries no fragment provides stay inline here; the shell, the POSIX
# userland, and the toolchains come from the `include` above.
allow = [
    "/usr/bin/clear",
    "/usr/bin/df",
    "/usr/bin/du",
    "/usr/bin/free",
    "/usr/bin/hexdump",
    "/usr/bin/ip",
    "/usr/bin/kill",
    "/usr/bin/nano",
    "/usr/bin/netstat",
    "/usr/bin/od",
    "/usr/bin/pgrep",
    "/usr/bin/pidof",
    "/usr/bin/pkill",
    "/usr/bin/ps",
    "/usr/bin/python3",
    "/usr/bin/scp",
    "/usr/bin/ss",
    "/usr/bin/ssh",
    "/usr/bin/strings",
    "/usr/bin/sync",
    "/usr/bin/timeout",
    "/usr/bin/top",
    "/usr/bin/uptime",
    "/usr/bin/vi",
    "/usr/bin/vim",
    "/usr/bin/vim.basic",
    "/usr/bin/watch",
    "/usr/bin/xxd",
    "/usr/sbin/arp",
    "/usr/sbin/ifconfig",
    "/usr/sbin/route",
]
# net-tools (ifconfig/route/arp) live in /usr/sbin; put it on PATH so they resolve
# by name. Landlock EXECUTE is independent of PATH (the absolute allow entries above
# are what grant execution); this is purely so `ifconfig` is found.
path = ["/usr/bin", "/usr/local/bin", "/bin", "/usr/sbin", "/sbin"]
```

```
[lifecycle]
ttl = "12h"
ttl_action = "warn"
```

```
[signature]
algorithm = "sshsig"
key_id = "kennel-maint-2026"
signature = "...envelope elided in print..."
```

### `include = "core-shell"`

Fragment: core-shell  (POSIX shells)

A composable capability bundle (05-templates.md §5.10): The POSIX shells. base-confined denies all execution and sets `[exec].shell` without granting it, so every interactive or scripted kennel needs the shell explicitly; this is that grant, once, instead of in every template.

```
include = ["core-shell"]
```

Additive-only (§5.10): every entry is an `[[exec.allow.add]]` delta. Composing this widens the program menu only; `argv[0]` stays gated by the resolved `[exec].allow` under Landlock execve default-deny, and the cage (net/fs/ttl/ ceilings) is untouched.

Adds to the exec floor:

- `/bin/sh` (the POSIX shell, and base-confined's default `[exec].shell`)
- `/usr/bin/sh` (the POSIX shell on a merged-usr system)
- `/bin/bash` (GNU bash)
- `/usr/bin/bash` (GNU bash on a merged-usr system)
- `/usr/bin/dash` (the Debian Almquist shell (`/bin/sh` on Debian/Ubuntu))
- `/usr/bin/env` (the `#!/usr/bin/env <interp>` shebang interpreter (the kernel's execve target for env-shebang scripts))


### `include = "core-coreutils"`

Fragment: core-coreutils  (Read / compute / text userland)

A composable capability bundle (05-templates.md §5.10): The non-mutating POSIX userland: read, inspect, filter, and transform. The block every interactive and agent template repeats. Carries NO filesystem-mutating tool — compose `core-file-mutation` for that — so a read-only kennel includes this alone and cannot write.

```
include = ["core-coreutils"]
```

Additive-only (§5.10): every entry is an `[[exec.allow.add]]` delta. Composing this widens the program menu only; `argv[0]` stays gated by the resolved `[exec].allow` under Landlock execve default-deny, and the cage (net/fs/ttl/ ceilings) is untouched.

Adds to the exec floor:

- `/usr/bin/cat` (concatenate and print files)
- `/usr/bin/ls` (list directory contents)
- `/usr/bin/head` (print the first lines)
- `/usr/bin/tail` (print the last lines)
- `/usr/bin/wc` (count lines/words/bytes)
- `/usr/bin/sort` (sort lines)
- `/usr/bin/uniq` (filter adjacent duplicate lines)
- `/usr/bin/cut` (extract columns)
- `/usr/bin/tr` (translate characters)
- `/usr/bin/nl` (number lines)
- `/usr/bin/tac` (concatenate in reverse)
- `/usr/bin/rev` (reverse lines)
- ...and 36 more


### `include = "core-file-mutation"`

Fragment: core-file-mutation  (Filesystem-mutating userland)

A composable capability bundle (05-templates.md §5.10): The write-side coreutils: create, move, remove, link, change mode. Kept separate from `core-coreutils` so a read-only kennel cannot mutate while a scratch/build kennel adds it.

```
include = ["core-file-mutation"]
```

Additive-only (§5.10): every entry is an `[[exec.allow.add]]` delta. Composing this widens the program menu only; `argv[0]` stays gated by the resolved `[exec].allow` under Landlock execve default-deny, and the cage (net/fs/ttl/ ceilings) is untouched.

Adds to the exec floor:

- `/usr/bin/cp` (copy files)
- `/usr/bin/mv` (move/rename files)
- `/usr/bin/rm` (remove files)
- `/usr/bin/mkdir` (create directories)
- `/usr/bin/rmdir` (remove empty directories)
- `/usr/bin/ln` (create links)
- `/usr/bin/touch` (create/update timestamps)
- `/usr/bin/chmod` (change file modes)
- `/usr/bin/mktemp` (create a temporary file/dir)
- `/usr/bin/install` (copy and set permissions)


### `include = "core-archive"`

Fragment: core-archive  (Archive + compression)

A composable capability bundle (05-templates.md §5.10): Tar and the common compressors/archivers — unpack a source tarball, compress an artifact.

```
include = ["core-archive"]
```

Additive-only (§5.10): every entry is an `[[exec.allow.add]]` delta. Composing this widens the program menu only; `argv[0]` stays gated by the resolved `[exec].allow` under Landlock execve default-deny, and the cage (net/fs/ttl/ ceilings) is untouched.

Adds to the exec floor:

- `/usr/bin/tar` (tape archiver)
- `/usr/bin/gzip` (gzip compress)
- `/usr/bin/gunzip` (gzip decompress)
- `/usr/bin/zcat` (stream a gzip file)
- `/usr/bin/xz` (xz (de)compress)
- `/usr/bin/bzip2` (bzip2 (de)compress)
- `/usr/bin/zip` (zip archiver)
- `/usr/bin/unzip` (zip extractor)
- `/usr/bin/zstd` (zstandard (de)compress)


### `include = "net-clients"`

Fragment: net-clients  (HTTP(S) fetch clients)

A composable capability bundle (05-templates.md §5.10): The command-line fetch-client BINARIES. Distinct from `net-permissive`, which grants egress DESTINATIONS: this adds curl/wget to `exec.allow`; the leaf or `net-permissive` says where they may reach, and a `[net].mode = "constrained"` cage + the proxy bound that egress.

```
include = ["net-clients"]
```

Additive-only (§5.10): every entry is an `[[exec.allow.add]]` delta. Composing this widens the program menu only; `argv[0]` stays gated by the resolved `[exec].allow` under Landlock execve default-deny, and the cage (net/fs/ttl/ ceilings) is untouched.

Adds to the exec floor:

- `/usr/bin/curl` (transfer a URL)
- `/usr/bin/wget` (retrieve files over HTTP(S)/FTP)


### `include = "vcs-git"`

Fragment: vcs-git

A composable capability bundle (05-templates.md §5.10): git plus its per-subcommand helpers, and the system git config read-only. Include it for a kennel that does source control.

```
include = ["vcs-git"]
```

Additive-only (§5.10). This grants the git *binaries* and the *system* config; it deliberately does NOT grant network egress — git-over-HTTPS to a specific forge is a destination the leaf states (or `net-permissive` adds), and git-over-SSH goes through the per-kennel SSH bastion (`[ssh]`, §7.10), never a real key in the kennel.

Adds to the exec floor:

- `/usr/bin/git` (git version-control client)
- `/usr/lib/git-core/**` (git's per-subcommand helper binaries, re-exec'd by `git`)
- `/etc/gitconfig` (system-wide git configuration (read-only))


## `interactive (policy)` — the thin leaf that pins a workload

Reference policy: interactive — the permissive, ready-to-run confined human shell.

Maintainer-signed and shipped enabled: `kennel run interactive` drops you into a confined `/bin/bash` with a broad workstation toolset — the interactive base (shells, coreutils, file tools, editors, archives, net clients, git, python3) widened with the C toolchain and the development headers — and HOST egress. Deliberately permissive: a credible daily-driver shell, still inside the cage (no_new_privs, dropped caps, deny-setuid, shadowed $HOME, masked /etc, private /tmp, self-only procfs). Derive your own leaf to add a project dir or tighten the toolset.

```
name = "interactive"
template_base = "interactive"
```

Widen the inherited interactive toolset toward a full dev shell: the C toolchain (cc/make/…) and the development headers, on top of the base's shells/coreutils/editors/net-clients/git/python3. The language-registry fragments (lang-python/lang-node) are NOT included — they carry by-name proxy-egress rules host mode rejects; under host egress python3 (inherited) reaches registries directly.

```
include = [
    "toolchain-c",
    "dev-headers",
]
```

Host egress (also the interactive default): a human shell needs unmediated network.

```
[net]
mode = "host"
reason = "an interactive human shell needs direct, unmediated egress (git/ssh/curl) on the host network stack"
```

```
[workload]
argv = ["/bin/bash"]
```

```
[signature]
algorithm = "sshsig"
key_id = "kennel-maint-2026"
signature = "...envelope elided in print..."
```

### `include = "toolchain-c"`

Fragment: toolchain-c

A composable capability bundle (05-templates.md §5.10): the C/C++ build toolchain — compiler, assembler, linker, archiver, and make. Include it for a kennel that compiles native code; the project tree itself is granted by the leaf, so this fragment adds only the tools.

```
include = ["toolchain-c"]
```

Additive-only (§5.10). No network and no extra filesystem write: a build reads the toolchain (already on `fs.read` via base-confined's `/usr/**`) and writes only into the project tree the leaf made writable.

Adds to the exec floor:

- `/usr/bin/cc` (C compiler driver (the default `cc`))
- `/usr/bin/gcc` (GNU C compiler)
- `/usr/bin/g++` (GNU C++ compiler)
- `/usr/bin/cpp` (C preprocessor (invoked by the compiler driver))
- `/usr/bin/as` (GNU assembler)
- `/usr/bin/ld` (GNU linker)
- `/usr/bin/ar` (static-archive tool)
- `/usr/bin/make` (GNU make)
- `/usr/lib/gcc/**` (gcc's per-version backend binaries (cc1, cc1plus, collect2), re-exec'd by the driver)


### `include = "dev-headers"`

Fragment: dev-headers  (Development headers + kernel source)

A composable capability bundle (05-templates.md §5.10): Adds /usr/src and /usr/include back into the view (read-only). These are absent from the curated base (construction-by-absence) and only needed by build/compile workloads. Include this fragment in templates that compile C/C++/Rust code against system headers.

```
include = ["dev-headers"]
```

Additive-only (§5.10): every entry is an [[fs.read.add]] delta. Composing this widens the read view only; the cage (net/fs.write/exec/ceilings) is untouched.

Adds to the exec floor:

- `/usr/include/**` (C/C++ system headers (absent from the curated base))
- `/usr/src/**` (kernel headers and source trees (absent from the curated base))
