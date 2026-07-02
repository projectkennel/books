# 18. The keys

A signature is only as good as the key behind it, and the previous two chapters leaned on signatures without
saying where the keys live or what trusting one means. Every signed artefact in the system carries the same
kind of signature: a source template, an included fragment, and a settled policy each bind their content to a
key identity with a signature, and that identity resolves against a trust store the operator owns.
What follows is the store, how trust moves through it, and the bound on what a signature can be asked to prove.

## 18.1 The key and its identity

A key is an ed25519 keypair, and a key identity is at once a filename and a signature-envelope record. The
identity is the stem of a `.pub` file in the trust store, the private key sits beside it, and the signature on
an artefact records which identity signed it; the verifier looks that identity up and checks the signature
against the matching public key. The identity is a short filesystem-safe string, legible in `policy show`
output and unambiguous as a filename on any target.

The on-disk form is the OpenSSH one. A public key is the familiar `ssh-ed25519` line, the base64 wire blob with
the key identity carried in its trailing comment, so the keys the trust store holds are the keys `ssh-keygen`
prints and lists and the identity shows up in an ordinary key listing; a private key is the unencrypted
`OPENSSH PRIVATE KEY` envelope, with an encrypted key refused and the operator pointed at `ssh-keygen -p` to
strip the passphrase rather than have the framework grow a passphrase-prompt path.

```
# ~/.config/kennel/keys/alice-laptop-2026.pub
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... alice-laptop-2026
```

```
[signature]
algorithm = "sshsig"
key_id = "alice-laptop-2026"
signature = "-----BEGIN SSH SIGNATURE-----\n...\n-----END SSH SIGNATURE-----\n"
```

The `.pub` file's stem is the identity, `alice-laptop-2026`, and the same string is the `key_id` the signature
records, so verification is a lookup: read the identity off the envelope, find the `.pub` whose name matches,
check the SSHSIG against the key it holds. The parser for this is small,
the unencrypted ed25519 layout being fixed-width with no ASN.1 and no variable-length structure to speak of. The
adoption of the OpenSSH format does not retire what came before it: a key is fundamentally its thirty-two public
bytes, the signature scheme is ed25519 either way, and a key recorded in the prior base64 representation remains
valid in the store, decoding to the same key the OpenSSH line would. The format is a more legible and more
interoperable envelope over an unchanged key, not a new key system, so existing keys and the tooling around them
keep working.

The keys are SSH keys, and so are the signatures over what they vouch for. A signature on an artefact is an
SSHSIG, the same detached signature `ssh-keygen -Y sign` produces and `ssh-keygen -Y verify` checks, so an
operator who trusts none of the framework's own code can verify a settled policy with the SSH toolchain they
already have. Signing reaches the private key the way any SSH client does, so a key in a file, a key in an
agent, or a key on a hardware token are alike to the framework, which writes no agent client of its own and
asks the operator's existing one for a signature. Each SSHSIG is bound to a fixed namespace that marks it a
kennel-policy signature, which is what keeps the convenience honest once the signing key is an ordinary SSH key:
a signature made to authenticate a session or vouch for a commit carries a different namespace and cannot be
lifted into a policy context, so a key may be reused across roles without the roles blurring. A signer held on
a hardware token is recognised and declined for now, its signature being one the framework cannot reconstruct in
process, with out-of-process verification for that case owed.

## 18.2 The three tiers

The store is three flat directories, searched as one. A vendor tier under `/usr/lib/kennel/keys` carries the
project's own keys and is the authority for the reserved `org.projectkennel.*` namespace; a host tier under
`/etc/kennel/keys` carries an administrator's fleet keys; a user tier under `~/.config/kennel/keys` carries a
user's own. None of the tiers is a single key. Each is a directory of `.pub` files, any number may coexist in a
layer, and every key in a layer is equally able to verify, so an organisation runs a host key per team or per
pipeline and a user holds several of their own without any of them being privileged over the others. A
signature verifies if its named identity matches any `.pub` in any searched directory.

```
/usr/lib/kennel/keys/       vendor tier, authority for org.projectkennel.*
  projectkennel-2026.pub
/etc/kennel/keys/           host tier, the fleet's signing keys
  ops-fleet-2026.pub
  ci-pipeline-2026.pub
~/.config/kennel/keys/      user tier, the operator's own
  alice-laptop-2026.pub
```

Each tier is a directory, each holds any number of `.pub` files, and every key in a searched tier verifies
equally, so a fleet runs one key per team or pipeline and a user keeps several of their own.

The tiers are not searched identically, and the difference is the security baseline. When the compiler resolves
a template's inheritance chain, it verifies each ancestor against the system tiers alone, the vendor and host
directories and never the user one, so a user template that extends `base-confined` narrows within the
invariants that ancestor re-asserts but cannot weaken them, because the key that signed the ancestor it builds
on had to be a host or vendor key. Settled-policy verification spans all three tiers, vendor first, then host,
then user, and an earlier directory wins a clash of identity, so a vendor or host key is unshadowable by a user
key that happens to share its name. The asymmetry is the point: a user may author and sign their own leaf
freely, but the floor they build on is anchored in keys only the administrator and the package manager can
place.

## 18.3 Rotation and revocation

Rotation is additive and lazy. A new key is placed in the store beside the old one and both verify at once;
there is no expiry clock, no revocation list, and no online ceremony (`do-less`). New artefacts are signed with the new
key, artefacts already signed with the old one stay valid until they are next recompiled, and the old key is
removed once nothing anyone cares about still references it. This is the `authorized_keys` model exactly: add
the new, retire the old on your own schedule. Because the store is re-read on every construction request rather
than frozen when the daemon started, a key added or removed after the daemon came up is honoured on the next
request without a restart.

Revocation is the same act of removal, and its reach is deliberately bounded to construction. Deleting a `.pub`
from the store revokes that identity: the next run or construction request refuses any artefact it signed (`refuse-to-start`). There
is no mechanism to reach into a kennel already running and kill it because its signing key was just revoked, and
that absence is by design rather than an omission. A running kennel is already confined by the policy it was
constructed with, the daemon verified that policy once at construction and the running kennel holds the
resulting trusted structure in memory rather than a live reference to the key, so revoking the key changes what
may be built next and changes nothing about what is already running. Stopping a running kennel is a separate and
direct act, `kennel kill`, not a side effect of pulling a key.

## 18.4 The honesty bound

The trust boundary under all of this is the filesystem, and naming what each tier rests on is what keeps the
guarantee honest. The vendor directory is protected by the package manager and root, the host directory by root
ownership, the user directory by the user's own ownership, and each tier's integrity is exactly the integrity of
whoever owns its directory: a vendor key vouches that the reference templates are the ones the project
maintainer signed and only a package update changes them, a host key vouches that the fleet artefacts were
placed by the administrator and only root adds a new host signer, and a user key vouches that the user's own
policies were compiled by the user. That last tier is wide on purpose, since any process the user runs can sign
with a user key, and it is not a weakness, because the threat model confines the workloads the user runs and not
the user's own tools. There is no promotion across the line: a user key cannot sign something that verifies as a
system key, is never consulted when an ancestor is checked, and a user who needs fleet trust has the
administrator install their public key into the host tier rather than elevating it themselves.

What a signature proves is narrow, and the narrowness is the honest part. The key proves who compiled an
artefact, never what the policy inside it does. The grants are readable prose a reviewer reads for themselves;
the signature only proves they were not altered between the compile that produced them and the construction that
enforces them. The key confers no authority of its own and is checked, not exercised: the daemon verifies the
signature and then trusts the in-memory structure, and the identity behind the key attests provenance and
grants nothing. This is the same line the settled artefact drew when its signature was shown to be no proof of
safety, seen now from the side of the key: the runtime re-asserts the framework invariants precisely because a
trusted signer is not trusted to have upheld them, and the key's whole job ends at saying who vouched for the
bytes.
