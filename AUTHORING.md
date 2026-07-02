# Project Kennel: Authoring Conventions

These are the conventions the two volumes are written under, in three small categories: Voice, Grounding,
and Figures. Where the design register states what the system is and the construction register states how
its code is built, these state how the prose about it is made. They are pulled here from standing
instruction into a committed register so that they outlast any one writing session, and so a stranger
could hold the prose to them with the author absent.

Unlike a design or construction slug, a convention here is not cited in the text. These are the rules the
text obeys, not handles it reaches for. The postures a chapter cites live in `PRINCIPLES.md` and
`CONSTRUCTION.md`, the threats in `THREATS.md`; this register holds only how the writing is done.

## Voice

### plain-prose

The sentence carries its own weight and the punctuation stays out of its way. No em-dashes; a clause that
wants one wants a comma, a colon, or a full stop instead. No colon-then-payoff cadence, where a line is
bent so a phrase can land after a colon. A statement is affirmative before it is contrastive, naming the
thing for what it is rather than first for what it is not. Formatting is prose by default, a list or a
bold lead used only where it carries something a sentence cannot, because a page that reaches for
structure to seem organised reads as less organised, not more.

### no-tells

The marks of an author performing rather than explaining are cut. No "genuinely," "actually," or
"honestly," which assert sincerity in place of earning it. No boosterish or salesy line; the work is
described, never sold. No signposting, none of the "this chapter" or "this section" that announces what
the reader can already see they are reading. The prose explains and gets out of the way, and the absence
of the tell is part of what lets the explanation be trusted.

## Grounding

### cite-only-the-real

A slug in backticks names a real entry in a register: a design posture from `PRINCIPLES.md` in the first
volume, a construction posture from `CONSTRUCTION.md` in the second. A threat tag names a real entry in
`THREATS.md`. Neither is invented to fill a sentence; a slug or tag that does not resolve is a fault, not
a flourish. The two volumes hold an altitude line between them, the first naming no mechanism so its
claims read the same on any port, the second naming the mechanism throughout, and a citation is checked
against the register at its own altitude.

### claims-carry-receipts

Every figure, tag, and mechanism on the page is verified against the repository tree before it is written,
not recalled and trusted. The tree is authoritative over the frozen design documents, over memory, and
over the prose itself; where they disagree the tree wins and the prose is corrected. A number with no
source in the tree does not go on the page. When a receipt proves a written claim wrong, the claim is
retracted in full rather than patched quietly, because a reader who finds one buried correction stops
trusting the rest.

### as-built-only

The prose documents the decision that shipped, never the deliberation that produced it. No "this was once
X," no account of the path not taken, no history of how the design arrived where it stands. A chapter
describes what is, so that it reads the same whether or not the reader knows what came before, and so that
the next change has one state to update rather than a narrative to reconcile.

## Figures

### code-follows-the-narrative

A code block appears at the beat the narrative reaches for it, set up by the prose before and walked by
the prose after; a block the surrounding prose does not arrive at is cut. The mould is TCP/IP Illustrated
Volume 1: motivate the thing, show its observable form, read it. The cadence is an artifact every few
hundred words, two to five in a chapter of fifteen hundred to two thousand, prose between each and most of
the page still prose. The target shapes the writing toward the artifacts the mechanism already has; it
does not licence a block the narrative never reaches.

### show-the-artifact-not-the-source

A block shows the observable artifact: a config stanza, a command, an on-disk layout, a manifest or wire
fragment, the thing an operator authors or a reader inspects, and never the daemon's own source. The
implementation is the repository's to hold, the prose carries the mechanism, and source dates faster than
the book. The excerpt is the minimal load-bearing one, the rest elided. Code is a second-volume device;
the first volume names no mechanism and shows none.
