# 9. OCI images

Developers package their work as OCI images, and an agent or a build is often handed one as the
environment it must run in: a base image with a toolchain, a service's published container, a
dependency that ships no other way. A confinement tool that cannot run them is a tool that does not
get used, whatever it thinks of the format. So Kennel runs OCI images. What follows is how it does that
without trusting them, and without taking on the execution model they
arrive with, because both the image's contents and the machinery that normally runs it are
incompatible with the boundary.

## 9.1 Not the engine

An OCI image is normally run by Docker, and Docker is the first thing that cannot cross into this
design. Its daemon is a root-equivalent orchestration service: the verb that creates a container is,
in effect, the authority to become root on the host. There are two ways to let a confined workload
reach it, and both give the boundary away. Proxying the Docker socket puts its entire protocol (a
large, stateful parser) into the trusted core, in front of a verb that is host-root. Running a
container engine inside the kennel instead (Docker, or a rootless one like Podman) hands the
workload the two kernel features most often used to escape confinement, the very ones the boundary
exists to withhold. The easy bridges are the ones that undo the design, so it builds neither.

## 9.2 An image is a filesystem

The reframe that makes the rest possible is to stop treating an image as a thing to be run and treat
it as what it physically is: a filesystem. An OCI image is layers of files and a little configuration
describing how to start one of them. Booted directly as the root of a kennel (under the same
boundary every other workload runs under, with no engine in the loop), it is inert content, and inert
content is what the filesystem chapter already knows how to confine (`construction-by-absence`). The
container does not need Docker; it needs to be the world a confined workload runs inside,
and that world is built the same way every other kennel's world is built. The whole apparatus of the
engine collapses into a problem the design had already solved.

What the image brings that an ordinary kennel does not is that the world itself is now untrusted. In
the filesystem chapter the constructed world was assembled from the host's own files and the
operator's own directories; here the bulk of it arrived from a registry, authored by someone the
operator has never met. That changes what the design must promise, but not how it confines: the image
is substrate, declared and pinned, and the boundary around it is the boundary around any kennel.

## 9.3 Ingesting without trusting

An image arrives wrapped in parsers: the registry protocol that fetches it, the manifest that
indexes it, the compressed archives that are its layers, and the runtime configuration buried inside
it. Every one of those is code reading untrusted input, and a confinement tool that parsed them in
its trusted core would have given back at the front door everything it defends at the back. So none
of them run there. They run where everything untrusted runs in this design: inside a kennel.

Fetching and unpacking the image is itself a confined workload. A builder kennel runs the ordinary
user-space image tools to pull the image and lay out its files, and the broad network egress a
registry pull requires (the widest reach anything in the flow needs) lives only there, fenced
inside that one kennel under a fetch policy Kennel ships and signs itself. The operator never authors
the broad-egress step and never signs it; they request a fetch, and the vetted policy that knows how
to reach a registry safely is supplied for them (`request-dont-author`), overridable only by a key
trusted to widen it. A bug in any of those parsers is a bug in a confined, unprivileged process,
contained exactly as any other workload is. The trusted core gains no registry client, no manifest
reader, no archive extractor.

The image's own startup configuration is handled the same way, at the other end. An image says how it
wants to start (an entrypoint, a default command, an environment), and rather than parse that in the
trusted core or make the operator transcribe it by hand, a small Kennel-shipped launcher reads it
from inside the running kennel, at the workload's own authority, and starts the entrypoint. One part
of that configuration cannot be passed through as the image wrote it. A handful of environment
variables are injection vectors that a loader or a language runtime acts on the instant a program
starts; passed unfiltered from an untrusted image, they are a free hand into the workload's own
startup. So the launcher strips those names before it applies the rest: absence at finer grain, the
same move the filesystem chapter made on a secret-bearing file, turned on the environment. It is the
stripping the system itself performs when a program crosses a trust boundary, reproduced here because
the image's environment is exactly such a crossing.

## 9.4 What the operator takes on

Running someone else's whole filesystem is a trust decision, and the design refuses to make it quietly
or to make it for the operator. Declaring an image as the substrate is a loud grant, in the same class
as sharing the host's network (`footgun-warn-dont-forbid`): it carries a required reason, and the
compiler derives a substrate-trust exposure from its presence and surfaces it among the kennel's risks
(`T3.8`). The operator is told, in the policy and in the risk report, exactly what they are taking on.

And what the design takes on in return is bounded, deliberately. Its posture over an image is
confinement, not content integrity. It pins the image by digest (a tag is resolved to a digest when
the image is fetched and frozen there, so what runs is exactly what was pinned) and it confines what
the image can do to the same degree it confines any workload. It does not vet the image, launder its
contents, or assert anything about the bytes it did not write. The provenance is the digest and the
operator's declaration, and nothing more is claimed; the signature pins the substrate, not each binary
inside it, because inside an image there is no per-file pin to make. This is the same honesty the
network chapter kept about payloads: the boundary governs what the thing may do, and is silent on what
the thing is.

That honesty extends to the seams the design knows about. Ingesting an image safely means ingesting it
without privilege, and an unprivileged unpack cannot preserve the image's own file ownership, so the
unpacked tree comes out owned by the operator, which hands the workload write access where a
foreign-owned file would have refused it. The design re-imposes the boundary that flattening erased,
holding the image's executable surface read-only beneath the workload; but it does so from the image's
declared shape rather than a walk of every file, so it is honest that the re-imposition has edges: an
image that drops privilege in its own startup, or installs its code outside the usual system
directories, is locked less completely than one that does not. Stronger integrity than the confinement
floor (content-addressing the layers, verifying them at use) is available as opt-in hardening, each
rung surfaced as a risk it retires, above a floor that is confinement and says so.

Across all of it the design declines to make an exception. A foreign format arrived with its own
execution model and its own assumptions about what may be trusted, and neither was allowed in. The
engine dissolved into a filesystem the boundary already knew how to hold; the parsers that came with
the image were made to run inside the boundary rather than in front of it; and the trust the format
asks the operator to extend was handed to the operator to extend, loudly, with the design confining
what it could not vouch for and saying plainly where its vouching stops.
