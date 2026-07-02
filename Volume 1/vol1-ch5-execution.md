# 5. Execution

A workload is not only the code it starts with. It is everything that code goes on to launch. A build
tool shells out to a compiler; a test runner starts a browser; an agent reaches for a download tool
to pull a binary, or an interpreter to read the world. Confine what the first process can touch on
disk but let it launch anything else on the machine, and the confinement is trivial to step out of:
the workload simply runs a program that was not confined.

So execution is its own boundary, and the danger it answers is not only what the workload chooses to
launch but what it can launch that the system left lying around: a privilege-escalation tool, an
unrestricted shell, a network utility (`T1.4`), any of which is a way out of the box for a workload
that was never meant to hold it.

## 5.1 The right to launch

Execution could be policed at runtime: a guard in the path of every launch, asked each time whether
to allow it. The design does not. It reaches instead for absence (`construction-by-absence`), the
same limb the filesystem leans on. The right to launch a program is stripped from everything in the
workload's world and handed back only to the paths the policy names.

A workload that tries to run a program it was not granted does not meet a monitor that weighs the
request and refuses. It meets a program it cannot start, because the right to start it was never in
its world. The decision was made when the world was built, not when the launch was attempted, and it
costs nothing to hold.

## 5.2 The contract

The contract is default-deny. An empty policy launches nothing; every program the workload needs to
run is named, and only the named programs run.

This closes the ordinary escalation routes without a word about them. A privilege-escalation helper,
an unrestricted shell, a tool for reaching the network: none is named in a workload's policy, so
none runs, not because the framework recognises them as dangerous but because it grants nothing it
was not asked to. The design keeps no list of forbidden programs. Under default-deny a denylist would
be reassurance theatre: a roster of known-bad binaries, maintained forever, pretending to hold a line
that the absence of a grant already holds. A program not named does not run, whatever it is.

The boundary does not depend on how a program is named, either. An absolute path to an unnamed program
fails exactly as a bare name does, because what is enforced is the right to launch, not the way the
launch is spelled. A policy may set where the workload looks for its programs, but that is a
convenience (it turns a missing tool into a clear answer rather than a silent failure) and never
the enforcement.

There is one way out, and it is deliberate. An operator can invert the posture, granting the right to
launch anything the workload can read. This drops the execution boundary, and the design treats it as
the boundary-dropping move it is: warned at build time and visible in the diff, never a quiet default
(`footgun-warn-dont-forbid`).

## 5.3 The launch, not what runs after

The boundary governs the launching of a new program. It does not govern what a program does with code
it reads once it is running, and that line is where the launch's concern ends and the other resources' begin.

An interpreter makes the line plain. A workload granted the right to run an interpreter may run any
script that interpreter can read, because a script is data: it is read, not launched. The framework
does not try to sit between the interpreter and its scripts, vetting each one. To do that it would
have to judge what a given script intends, and intent is the thing the design refuses to judge
(`good-boy`). The grant says the interpreter may run; what it then does is answered elsewhere: by the
files it can read, the destinations it can reach, the services it can call. Execution settles what may
launch. The other resource classes settle what the launched thing may do. This has a consequence worth
stating outright rather than leaving between the lines: for the flagship case, an agent granted a shell
and an interpreter, the execution allowlist does little of the confining work. A shell and a Python are
each an open-ended executor of whatever they can read, so once they are on the allowlist the exec grant
has largely spent itself, and the filesystem, network, and local-service classes carry nearly the whole
of the containment. The allowlist still earns its place by keeping a compiled escalation binary off the
menu, but the reader who expects it to be the primary control for an interpreted workload has the
weight in the wrong class.

The same line runs through a program and its libraries. A dynamically linked program needs the right
to launch, and so does the loader that starts it; both are launches. But the libraries the loader then
pulls in are not launched: they are read into the running program's own memory, which a read grant
already covers. A library loads on the right to read it, not the right to run it. Governing that as
execution would mean watching what a running program loads into itself, which is the interpreter
problem again under another name.

## 5.4 The non-escalation guarantee

Underneath the allowlist sit guarantees the allowlist cannot weaken, and they all say one thing: a
launch is not a way to gain authority the workload did not already have.

On most systems, launching certain programs is itself a privilege transition: the program runs with
the authority of whoever owns it, not whoever ran it, which is how an unprivileged process has long
reached for more (`T3.1`). The design closes this from both sides. A program that would gain authority
on launch is refused the right to run at all, even if a policy names it; the floor overrides the
grant, the way the filesystem's categorical denials do. And should such a program run regardless, the
launch is sealed against the transition: no program a workload starts comes away with more authority
than the workload had. The identity stays put, and the authority with it (`split-the-uid`). Two locks
on one door: the privilege-gaining program cannot launch, and the launch cannot grant privilege.

The sharpest of the guarantees is the simplest. The right to write a path and the right to launch a
path are never held over the same path. Without that, a workload allowed to write its working
directory and to run a compiler could write itself a program and run it, minting its own entry on the
allowlist and stepping around the whole contract. So the two sets are kept disjoint by construction:
nothing the workload can write is anything it can run, and a binary it compiles or drops into a
directory it controls is, in its world, an inert file.

These hold beneath the policy, and beneath the escape hatch too. An operator who inverts the posture
to allow-anything-readable widens what may launch; the operator does not thereby grant a path to
privilege. A workload with every readable file launchable still cannot run a program that escalates,
and still cannot raise its authority by launching one. The boundary an operator can drop is the
allowlist. The non-escalation guarantee is not theirs to drop (`reference-monitor`).

Execution, like the filesystem, is mostly the first limb: the right to launch is absent until the
policy grants it, and granted narrowly. What execution adds to absence is a floor: that no launch,
named or not, allowed or inverted, is a step up in authority. The workload runs the programs it was
given, as the unprivileged thing it already was, and the programs it was not given are not there to
run.
