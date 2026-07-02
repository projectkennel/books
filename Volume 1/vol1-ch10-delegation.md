# 10. Delegation

Delegation here does not mean one person handing work to another. It means the framework handing a
workload one of its own powers (the power to bring a kennel into being) so that a confined,
untrusted workload can cause a second kennel to exist. Instantiating a kennel is normally the
operator's act; here that act is lent to a workload the operator has explicitly
granted it. And what the workload brings into being is not a child it owns but a sibling it cannot
reach into: kennels have no hierarchy, and a spawned kennel is no more the spawner's than any other on
the machine.

Why lend a workload such a power at all is the lethal trifecta, and answering that is what follows.

## 10.1 The trifecta

An agent earns its keep only when it can both run code and reach the network: read the repository and
fetch the dependency, run the test and call the API. But a single workload that can do both is the
lethal trifecta in one box: code that can be steered by a prompt injection (an agent is exactly that,
`T3.7`), private data within its reach, and a path out to carry that data away. Confining such a
workload tightly does not dissolve the danger, because the danger is not what it might escape to but
what it was openly granted: both halves, in one place, under one compromise.

The industry's answers are a full virtual machine for each task (Firecracker and the like), which is
heavy and elaborate to orchestrate, or a container engine nested inside another (Docker-in-Docker),
which is root-equivalent and leaks. Kennel already holds a lighter primitive. A workload can be given
neither half (no code execution it can aim at the network, no network it can hand code) and still
get its work done, by asking for a sibling kennel that holds exactly one half and speaking to it
through a channel. The agent runs no untrusted code and reaches no network; the tool it spawns runs
the code with no network, or reaches the network with no code to run. Each kennel holds one leg of the
trifecta. The dangerous combination is assembled in no single kennel, because the thing that would
assemble it holds none of it. That is the claim in its exact form, and it is worth stating precisely
rather than as a slogan, because it holds per kennel and not per session: an agent that brokers between
two complementary siblings can still route data from one to the other across the channel it holds to
each, reassembling the trifecta with an extra hop in it. The residual is real and named later in this
chapter; the headline is that no one kennel is ever handed the whole, not that the whole can never be
composed by a workload wiring siblings it was granted.

## 10.2 Request, don't author

The rule that makes delegation safe is that the workload never writes policy. It cannot author a
grant, invent a capability, or compose a kennel of its own design. What it can do is name a template
the operator has already signed and installed, and fill in the few fields that template marks as
fillable. Everything else in the template is frozen and inherited exactly as signed
(`request-dont-author`).

This is why lending the power to instantiate does not lend the power to grant. The capability floor of
every spawn is the signed template's, and nothing the workload does raises it: a template that fixes
its network off stays off, whatever the workload writes, because the only writes that take are the
ones the template opened, each within the bound the template set. The operator consented once, when
they signed the template into the store; every spawn from it is a reference to that consent, not a new
one. So the entire surface a workload controls is the handful of blanks the template left for it: not
the policy, only the values in fields the policy already fenced.

A workload should not have to discover that surface by trial, firing speculative requests to learn
what the framework will accept. The grant is open to inspection: a workload can ask the framework for
its own delegation grant and be told which templates it may instantiate, which fields of each it may
fill and within what bounds, and how many siblings it may have at once. It learns the shape of the
fenced blanks before it fills them: the reading side of requesting rather than authoring. And the
grant is loud: holding the power to instantiate siblings is an exposure the operator declares
deliberately and sees surfaced among the kennel's risks (`T3.9`).

## 10.3 Siblings, not children

What the workload brings into being, it does not command. The framework is the spawner; the requesting
workload and the spawned kennel are siblings, joined by the channel between them and nothing else. The
requester cannot trace the sibling's execution, send it signals, or reach into its memory, and that
absence is not an oversight but the whole point. A spawn exists to create an isolation that did not
exist before; if the spawner could reach into what it spawned, that isolation would be defeated at the
instant of its creation. So the spawned kennel runs under its own boundary, as separate from its
requester as from any other kennel on the machine.

The framework that does the spawning stays where it always does: out of the byte path. It checks the
grant, fills the template's blanks with the workload's values, builds the sibling, and hands back the
ends of a channel; it does not sit in the conversation that follows. When the sibling is an agent's
tool (a tool server speaking the Model Context Protocol over that channel), the protocol is the two
kennels' business, parsed by neither the framework nor anything in its trusted core
(`control-not-data-plane`). And the power to delegate does not spread on its own: a spawned kennel can
spawn further siblings only if its own template grants it that, so a single delegation does not open
an unbounded chain, and a ceiling on concurrent siblings bounds the rest.

## 10.4 The residual

What delegation cannot do is make the workload's two controlled inputs safe on the operator's behalf.
The first is the values it writes into the template's open fields. A field the operator left too wide
(a destination pool that admits more than it should, a pattern that lets a path slip through) is a hole
the operator signed, and no machinery downstream closes it, because the template said those values were
the workload's to choose. The bound is only as good as the operator drew it.

The second is sharper, because it is the trifecta returning by the back door. An agent granted the
power to spawn a tool that reaches the network, and also a tool that touches the filesystem, holds no
dangerous combination in any single kennel, but it holds a channel to each, and it can wire those two
channels together itself. The leg that reads private data and the leg that reaches the network are
reunited not inside a kennel but in the agent that brokers between them. The decomposition holds per
kennel and can be undone across kennels, by the one party with a channel to both. So the grant that
matters is not only which templates a workload may spawn but which it may spawn together: complementary
halves within one workload's reach are the whole trifecta with an extra hop in it. The design makes the
assembly visible and deliberate; it does not pretend a workload handed both halves cannot put them back
together.

Delegation is the framework lending a workload a power that was the operator's, and getting back the
usefulness of an agent that can reach beyond itself without ever holding, directly, the danger of doing
so. It is made safe by three things at once: the workload requests from signed templates rather than
authoring policy, so it can instantiate only what the operator already consented to; what it
instantiates is a sibling beyond its reach rather than a child under its hand, so the isolation
survives its own creation; and the capabilities dangerous together are handed out apart, so no single
confinement holds the combination. What remains is the operator's to weigh (how wide the blanks, and
which halves to place within one workload's reach), and the design's part is to keep that weighing
honest and in view.
