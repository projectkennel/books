# 9. Local services

The network chapter brokered a kennel's reach to remote services through a facade in the kennel and a delegate
on the host. The services already running on the workstation, the agent sockets and the session bus, are
reached the same way, and they are a denser authority surface than the network is. A remote endpoint has to be
found and connected to; a local agent socket sits at a known path, holds the operator's signing key or stored
passwords, and answers anyone who can open it. The same broker pattern carries this resource class, and two of
its members sit at opposite ends of a spectrum the previous chapter drew: a socket connection is a decision
made once, at connect, while the session bus is a decision made on every message that crosses it.

## 9.1 The ambient surface

A normal user session is full of Unix-domain sockets that are pure capability. The ssh-agent socket signs
challenges; the gpg-agent socket signs and decrypts; the keyring socket hands back stored passwords; the
session bus socket reaches every service the desktop runs; the Wayland and PipeWire sockets carry the screen,
the clipboard, the microphone, the camera; the Docker socket is root-equivalent. Many of them are
unauthenticated by design: the access control is the socket file's permissions, so anything that can open the
socket has the whole of what it offers. Inside a kennel that runs as the operator's own uid, those file
permissions grant access rather than withholding it, and a confined workload that could open these sockets
would have, silently, the operator's keys and the operator's session.

The session bus is the sharpest case, because a single grant of it is the whole session. A workload that can
speak to the user's D-Bus can ask the file manager to read and write files, ask `systemd` to start an
unconfined process in the session and so step entirely outside the kennel, read the operator's saved
credentials from the secret service, send notifications that impersonate any application, and reconfigure the
network. A bare socket grant for the bus is therefore not a small convenience, it is a grant of nearly
everything the unconfined user can do, requested by proxy. The resource class exists to give a workload the
specific local service it needs without giving it the socket that would carry all the rest.

## 9.2 The brokered-connect facade

A Unix socket is reached, like a remote host, through a facade rather than through a path. The workload asks
the `IAfUnix` node on its binder bus for a socket by the policy name it was granted, kenneld checks the name
against the allowlist, performs the `connect` on the host side, and returns the connected descriptor into the
kennel. The workload then speaks to the agent or service over an ordinary fd and never learns where the socket
lives. No host socket path appears in the kennel's view at all, which is the property that matters: there is
nothing to enumerate, nothing to probe, and nothing to connect to out of band, because the only way to reach a
local socket is to name a grant and be handed the result (`mediate-use-not-reach`). A name the policy did not
grant cannot be asked for, so default-deny is structural rather than a rule that has to remember every
dangerous socket, and the decision and its audit land at the connect, on the call, not inferred from what the
view happens to contain. This is the connect-time shape of the proxy from chapter 8: broker the connection
once, hand back the descriptor, and step out of what flows over it (`control-not-data-plane`).

```
[[unix.allow]]
name = "gpg-agent"
real = "/run/user/1000/gnupg/S.gpg-agent"
shim = "~/.gnupg/S.gpg-agent"
reason = "decrypt and sign with the operator's own gpg key; no key material enters the view"
```

The grant names a host socket at `real` and the path the workload finds it at under `shim`, and the workload
opens the shim and learns nothing of the host side. The name is the whole interface: the policy grants
`gpg-agent` and the broker resolves the rest, so a socket the policy did not name has no shim to open.

One high-value socket is deliberately not served this way. An ssh-agent reached through the facade would be a
signing oracle: the workload could not read the key, but it could ask the agent to sign anything, for any
destination, which is most of what holding the key would buy. Per-kennel SSH is routed through a
re-origination bastion that binds each signature to an intended destination instead, so the agent socket is
never the thing brokered. The facade carries the agent-shaped services where a blind connection is acceptable,
the keyring and gpg-agent and the display and audio sockets, and the signing case is handled where the
delegation can be made specific. What the facade does for these is a dumb connect: it resolves a name to a
host socket, performs the `connect`, and hands back the fd without parsing or filtering a byte of the
protocol that then rides it. It vouches for nothing. A raw keyring or gpg-agent grant is therefore an
operator's choice the operator owns, not a channel the framework stands behind, which is the line §9.4
draws: the framework refuses to *mediate* such a service and will not *build* a facade that parses and
passes its messages, but a bare connect it did not have to parse is the operator's to make, loudly and
against a warning.

Beneath the path-named sockets sits a second Unix-domain namespace the path rules do not touch. Abstract-namespace sockets are addressed by a name in kernel memory rather than a file, so no filesystem ACL applies to them, and a workload could otherwise reach a host service bound there with no path to deny. Landlock scoping
closes them: a kennel's domain is scoped so a `connect` to any abstract socket bound outside it is refused by
the kernel, with no inspection of the address and no userspace dependency. The scope is defence-in-depth on
top of the network namespace, which is the structural control, since a kennel that owns its own network
namespace has an empty abstract namespace to begin with, nothing host-side having bound there. The two compose
in one direction only: a kennel that asks to allow abstract sockets and to share the host's network namespace
is a compile error, not a warning, because sharing the host stack puts the host's abstract sockets back within
reach and the scope would be carrying a load the namespace was supposed to carry (T1.13).

## 9.3 The session bus is not a socket grant

D-Bus is brokered, never handed over as a socket, and the reason it cannot reuse the connect-and-stream shape
of the proxy is the heart of the chapter. The proxy makes one decision, at connect, and afterwards the kennel
holds an established socket it may stream over freely, because the security question was answered when the
destination was approved. The session bus has a security question on every message: which service, which
object, which interface, which method. The channel never becomes a post-decision stream, it stays
security-relevant for its whole life, and a raw descriptor to the thing on the other end would hand the
workload everything reachable through it. So a D-Bus message is mediated message by message, and the mediation
is split across the trust boundary so that no trusted component ever parses a byte the workload controls.

```
[dbus.session]
enabled = true

[dbus.session.allow]
talk = ["org.freedesktop.Notifications"]
call = ["org.freedesktop.portal.Desktop=org.freedesktop.portal.FileChooser.OpenFile"]
broadcast = ["org.freedesktop.Notifications"]
```

The grant is at the granularity of the question. A `talk` entry names a whole destination; a `call` entry
narrows to one `destination=interface.member`, so a workload may reach the file-chooser portal without reaching
the rest of the portal service; and `broadcast` admits a signal only from a sender the kennel may already talk
to. What the policy does not list, the table does not pass.

The in-kennel facade is the sole parser of the adversarial wire. It terminates the workload's bus connection,
parses each method call, and emits a typed transaction carrying the vetted-able fields, destination and object
path and interface and member and body, across the binder gateway. A delegate in the operator's own context
holds the real bus connections, matches that typed transaction against the table the compiler built from the
policy, and on a pass reconstructs a fresh, well-formed message from the typed fields and sends it. It never
re-parses the workload's bytes, only reads the fields the facade already parsed. kenneld sits between them as
the membrane and does the least of all: it neither parses the frame, so the D-Bus engine never enters its
trusted base, nor applies the filter, which is the delegate's mechanical job, binding each connection to the
in-kennel caller that opened it and relaying. This is the parse-into-typed-form discipline carried across a
boundary (`parse-dont-validate`): the hostile-protocol parser is quarantined on the untrusted side, the
authority that acts is on the trusted side, and only structured, already-parsed data crosses between them
(`quarantine-the-unsafe`). Growth of the trusted base here is a decision point, not a parser.

## 9.4 Asymmetry, and the refused set

Outbound and inbound are not the same path, and keeping them separate is what makes the no-trusted-parser claim
hold. Outbound method calls are adversarial and are parsed in the kennel as above. A reply to an approved call
is trusted-origin, coming from the operator's own bus, so the delegate reads it and returns it and the facade
hands the body to the workload as data, with no trusted component having parsed kennel-controlled bytes to
produce it. Signals are broadcast by host services and are delivered only under a match-rule allowlist: a
kennel receives a signal only from a service it is already allowed to talk to and only where it registered a
matching subscription, so the delegate filters the bus's signal stream down to that set before forwarding. A
signal from a service the kennel may not talk to never arrives, which is what stops a workload from watching
the bus to learn what the operator is running. Conflating the two directions into one bidirectional filter
would have smuggled an adversarial-wire parser into the trusted delegate, which is the thing the split exists
to prevent.

Some services are not default-denied but refused outright. Everything a policy does not grant is already
denied, and a user may override that denial for a service that is dangerous but conceivably legitimate, a
connectivity query or a mount for a media workload, with a loud warning and a threat tag
(`footgun-warn-dont-forbid`). Above that sits a small, named set the facade refuses regardless of policy, where
naming the service in an allow list is a compile error rather than a warning. What puts a service on it is not
the danger of the capability but the act the facade would have to perform to broker it. A `talk` or `call`
grant is not a dumb connect: the facade parses the protocol, matches each message against the table, and
passes the ones that clear it, which is the framework vouching that a given retrieval or call is a legitimate
one. For a secrets protocol that vouching is attestation the framework cannot back
(`authentication-never-attestation`): to mediate `org.freedesktop.secrets` is to stand behind which password
fetch the workload may make, and the monitor has no ground to stand on. So the secret service is refused at
compile, not because the passwords are dangerous but because brokering the protocol means vouching for its
use. Session and process control are on the set for the same mechanism reason read the other way: to mediate
them is to broker a spawn escape or session takeover, which would defeat the monitor's reason to exist. A
framework that claimed confinement while mediating either would be theatre. The set is deliberately small and
deliberately closed.

The rule under it is the line §9.2 named from the other side, and it is worth stating plainly because it does
not fall where a reader expecting a capability-scoped refusal would put it. The framework refuses to *mediate
or vouch*: it will not build a facade that parses a secrets or signing protocol and passes selected messages,
because parsing-and-passing is vouching. It *warns* where it merely *connects and steps out*, because a bare
connected fd carries no claim the framework made. The consequence is an asymmetry the text will not paper
over: the D-Bus secret service is refused at compile, while a raw connect to the same secrets daemon's own
socket is a warned `[[unix.allow]]` grant the operator may write. The two are not in tension once the refusal
is read for what it is, a bound on what the framework will *build and stand behind*, never a bound on what the
operator can *reach*. An operator who wires the raw socket has the passwords; the framework simply did not
hand them over under a claim that the transfer was safe. Holding the operator's own expression of intent above
a fully safe posture is the deliberate trade (`footgun-warn-dont-forbid`), and the raw route is loud, tagged,
and surfaced in the risk report precisely so the choice is made in the open.

```
[dbus.session.allow]
talk = ["org.freedesktop.*"]

# the compiler refuses this: `org.freedesktop.*` reaches
# `org.freedesktop.secrets`, which cannot be brokered to a kennel
```

A wildcard reaches the refused set as readily as an exact name, so the check is on what the pattern admits, not
on what it spells. The operator cannot widen into the closed set by writing it broadly, and the refusal is a
compile error rather than a runtime denial, caught before the policy is ever signed.
