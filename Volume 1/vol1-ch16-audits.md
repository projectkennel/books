# 16. Audits

A reference monitor decides. By the same property that lets it decide every use, it can record every
decision it makes. Auditing is not a feature bolted onto the design; it is what complete mediation looks
like written down. A boundary that sees every crossing can keep an account of them, and a boundary worth
trusting keeps that account on the side the workload cannot reach.

## 16.1 The record of mediation

Mediation happens at the interposition limb, where a use is presented and a decision returned
(`interpose-as-transaction`). That is the point at which there is something to record: a request was
made, a rule applied, an answer given. The construction limb leaves little to log, because what was made
absent is never reached and so never refused; a workload does not attempt what is not in its world
(`construction-by-absence`). The audit is mostly the diary of interposition, the running account of the
decisions the monitor was asked to make and the answers it gave.

Because mediation is complete, the account can be complete in the same sense (`reference-monitor`).
There is no mediated decision that escapes the possibility of being recorded, since recording is one
more step the monitor takes at a point it already controls. The audit inherits the reach of the thing it
watches. A boundary that mediated only some uses could account for only some; a boundary that mediates
all of them can account for all of them, and the completeness of the record is not a separate
achievement but the same one seen from another angle.

## 16.2 Written by the trusted side

The account is worth keeping only if the subject of it cannot edit it. So the framework writes the
audit, and the workload never does. The workload is what the record is about, not what produces it.
Every event is emitted on the trusted side, by the monitor that made the decision, not by the process
the decision was made against.

This closes the obvious attacks before they begin. A workload cannot forge an event, because it does not
hold the pen. It cannot suppress one, because it does not control the writer. And by default it cannot
even read the account kept of it (`T1.1`), because the audit is not placed in its constructed view: the
log is simply absent from the workload's world, in the same way the first limb makes other things
absent. A workload that tried to learn what had been observed of it, or to write a misleading entry into
the record (`T2.2`), would find nothing there to read and nothing to write to. The audit is tamperproof
from the side that would have reason to tamper with it, which is the property the enforcer has and for
the same reason: the thing under watch holds no authority over the watching.

## 16.3 Decisions, not contents

What the record holds is the shape of each decision and no more: which resource was reached for, which
target, whether it was allowed or denied, at what time, in which kennel, and under which rule. The rule
brings its reason with it, the same reason the policy was made to carry, so a denial does not merely say
no; it says which line said no and why that line exists. The record is legible because the policy that
produced it was made legible first (`tell-me-why`).

Denials are always kept, because a denial is the security event: something attempted a crossing and was
stopped, and the operator needs to be able to ask what their workload tried to do that the boundary
refused. Allowances are kept more sparingly. A working kennel produces a great many of them and most are
the dull expected case, so the record summarises them rather than drowning the denials beneath them. How
much is kept is the operator's to set, but the default leans toward signal.

One class of thing is never written, at any level. The audit does not record secrets, credentials, keys,
or the contents of the files the kennel exists to keep in. It records that a secret-bearing file was
read, never the secret on the line below. This is not an omission to be fixed by a verbose mode but a
rule the design holds on purpose, because an audit that copied the protected payload into a second file
would be a leak wearing the dress of accountability. The record is of the decision, never of the thing
the decision protected. It stays, in this, on the same side of the line the network chapter drew: the
boundary accounts for the channel it mediates, not for the payload it was never reading.

## 16.4 A record made to be used

A record kept on the trusted side and never polluted with payload is worth building on, and the design
treats it as an interface rather than as a heap of text. The events have a stable, structured,
documented shape, so that something downstream can read them years apart and rely on what it finds. That
stability is what turns the account from a curiosity into a tool.

The plainest use is the daily one. An operator puzzled by a workload that cannot reach some service
reads the denials and is told, in as many words, which rule refused the connection and why. Past that
lie heavier uses the same record supports without being changed for them: a forensic reading of what a
workload touched within some window; a compliance demonstration that a kennel never reached a resource
it was forbidden, evidenced by the refusal of each attempt rather than by a promise; and the feedback
into authoring, where the record of what a workload kept trying to do shows the operator where a grant
is too tight or too loose. Defining confinement was described as where the reasons go. This is where
they arrive.

## 16.5 What the record does not claim

Two honest limits close the account. The first is on the record's own integrity once it has left the
framework's hands. The audit is append-only from the side that writes it, and the workload cannot touch
it, but stronger guarantees against a compromised host, such as segments signed as they are written or
an external transparency log, are a layer above this one. Kennel makes them possible without providing
them itself (`do-less`). It yields a record trustworthy against the workload; sealing that record
against the machine is a further thing, and a downstream one.

The second is on what a record of mediation can ever contain. It holds the crossings, not the reasoning
behind them: what a workload reached for, never what it meant to do with what it reached. A monitor sees
its boundary and accounts for it faithfully, and it sees nothing of the workload's inner life, which was
never its to mediate or to know. The account is complete about the boundary and silent about the mind
behind it, and it is honest in being both.

With that, the design is laid out. A kennel confines by constructing a small world and mediating the few
seams it leaves; it declares that confinement in a signed and reasoned grant; it enforces the grant
behind a floor no signature can lower; and it keeps an account of every decision on the side the
workload cannot reach.
