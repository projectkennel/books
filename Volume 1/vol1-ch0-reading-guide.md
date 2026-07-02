# 0. Reading guide

Project Kennel is a userspace reference monitor for the interactive user level: a way to run code
under your own account without granting it your own authority. This is the first of two volumes. This
one sets out the design, stated without reference to any operating system; the second realises that
design on Linux. The division is not cosmetic. A claim belongs in this volume if it would read the
same on a Linux, a macOS, or a Windows port, and in the second if it names the mechanism that makes
the claim true on one of them. The design is the contract; the realisation is one way of keeping it.

The volume is in three parts. The first builds the model: what a reference monitor is, the properties
it must have, and the two ways it achieves them: by removing a resource so there is nothing to
mediate, and by interposing on the uses it cannot remove. The second applies that model to each class
of thing a workload touches, a chapter at a time, from the filesystem through the network to the local
and cryptographic services a session depends on, and on to the cases where one confined workload
spawns or reaches another. The third turns to the grant itself: how a confinement is written, how the
written form becomes the enforced one, who is trusted to vouch for what, and how the monitor keeps an
account of every decision it makes.

Two companion documents stand behind the prose. The threat catalogue (`THREATS.md`) lists the concrete
threats the design answers, each with an identifier of the form `T1.1`; where a decision closes one,
the text names it. The principle register (`PRINCIPLES.md`) states the postures the design holds to,
each with a short name such as `construction-by-absence`; where a decision follows from one, the text
names that. A citation in either form is a pointer into the companion, not an aside to read past.
Literature is cited by name in brackets, as `[Anderson]`, and resolved in the references at the end.

The chapters are meant to be read in order, but each resource-class chapter stands largely on its own
once the model of the first part is in hand. A reader who wants the argument can follow it straight
through; one who wants a particular boundary can turn to its chapter and follow the citations back to
the model and to the threats behind it.

## Contents

**Part I. The model**

1. The premise
2. The reference monitor
3. The two limbs

**Part II. The resource classes**

4. Filesystem
5. Execution
6. Network egress
7. Local services
8. Cryptographic services
9. OCI images
10. Delegation
11. The capability mesh

**Part III. The declared grant**

12. Defining confinement
13. The settled policy
14. Trust and consent
15. Audits
