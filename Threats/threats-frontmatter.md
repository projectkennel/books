# Threat Catalogue for User-Level Workload Confinement

A standalone, citable catalogue of the threats posed by unvetted code running at the interactive user level of a developer workstation, and of the confinement approaches that address them.

Version 0.5 · 2026

This catalogue was written and maintained as part of the design of Project Kennel, and can be used independently of it. It is written to be cited on its own: security teams may reference the threat identifiers in their own policy documents, auditors may use the catalogue to evaluate controls, and other tools in the user-level-workload-confinement space may adopt the identifiers as a shared vocabulary, regardless of which enforcement mechanisms they choose. Where an entry describes how a threat is addressed, it describes the confinement *approach* — the property a user-level reference monitor must hold — not the internals of Project Kennel or any other system.

The catalogue is in two parts. Part 1 is the in-scope families: reconnaissance and exfiltration, posture degradation, workload-class-specific threats, and threats against a confinement's own boundary-crossing mechanism. Part 2 is the out-of-scope set, named deliberately, because an approach honest about its limits is easier to trust than one that implies total coverage. Four appendices follow: a register of the public incidents that motivated specific entries, a reconnaissance-target enumeration, a MITRE ATT&CK mapping summary, and a preliminary crosswalk to common compliance control frameworks.
