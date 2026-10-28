# VERIFY — ai0S-public (v2)

> **Bundle Address:** `ai0S-public-v2@sha256:409cfd7bfe053a986892b7595f92ad3cc462298b38f3736925cb746aeafcecbe`
> **Origin Anchor (`PID 1`):** `ai0S@sha256:b3aeee619d9cb691cc6618466407d56598e830c53c6d024748d4582887c57d13` *(Bitcoin `971315, 971319, 971354, 971357`)*
> **Signer (Ed25519):** `9F4D9A266D720FE6336574D87B410637560297CF`

## Core Files

| Datei / File | Rolle / Role | Zustand / State |
|---|---|---|
| `BOOTLOADER-V2-DE.md` | Einstieg für Menschen (DE, ~4 Min.) | `ai0S — Bootloader v2` in sieben klaren Grundsätzen + Wegweiser zu den 6 Deepdives |
| `BOOTLOADER-V2-EN.md` | Introduction for Humans (EN, ~4 min.) | `ai0S — Bootloader v2` in seven clear principles + guide to the 6 Deepdives |
| `AI0S-RUNTIME.0s` | All-in-One Runtime für KIs (`.0s`) | Kompletter operativer Kontext (Anker, alle 6 Deepdives & File-Realization-Layer im Harness) in einer Datei |
| `README.md` | Zweisprachiges Start-Portal (DE + EN) | Übersicht über `Bootloader v2`, `AI0S-RUNTIME.0s` und direkte Links zu `ai0s-deepdive-public`, `ai0s-deepdive-2-public` , `ai0s-still-public`, `ai0s-deepdive-3-public` und `ai0s-destille-public` |

## Historical Bitcoin proofs / Historische Bitcoin-Proofs

See [VERIFY-BITCOIN-ANCHOR.md](./VERIFY-BITCOIN-ANCHOR.md) for the four historical OpenTimestamps proofs, verifier, instructions and trust/privacy limits. The PID 1 digest is distinct from the current bundle root; the latter has no Bitcoin timestamp from these proofs. / Vier historische Proofs, Prüfung sowie Vertrauens- und Datenschutzgrenzen stehen in der verlinkten Anleitung. Der aktuelle Bundle-Root ist nicht der historische PID-1-Digest und erhält durch diese Proofs keinen Bitcoin-Zeitstempel.

## Verify Commands

```sh
gpg --import pubkey.asc
gpg --verify MANIFEST.json.sig MANIFEST.json
sha256sum -c <(jq -r '.files[] | "\(.sha256)  \(.path)"' MANIFEST.json)
cat MANIFEST.json MANIFEST.json.sig | sha256sum   # = 409cfd7bfe053a986892b7595f92ad3cc462298b38f3736925cb746aeafcecbe
```

Per-file signatures (detached, Ed25519):

```sh
for f in AI0S-RUNTIME.0s BOOTLOADER-V2-DE.md BOOTLOADER-V2-EN.md README.md VERIFY-BITCOIN-ANCHOR.md ROOT.preimage.ots MANIFEST.json.ots ZERO-MNEMONICS.0s.ots LLM-INIT-PROMPT.md.ots verify-anchor.sh verify-anchor.py test_verify_anchor.py; do
  gpg --verify "$f.sig" "$f"
done
```
