# Historischen Bitcoin-Anker prüfen / Verify the historical Bitcoin anchor

## Deutsch

Die vier OpenTimestamps-Proofs ermöglichen einen **Explorer-basierten Abgleich** historischer SHA-256-Fingerabdrücke mit Bitcoin-Block-Merkle-Roots, ohne die Originaldateien zu veröffentlichen. `ROOT.preimage.ots` gehört zum historischen PID-1-Anker; der **aktuelle Bundle-Root ist davon verschieden und nicht automatisch Bitcoin-zeitgestempelt**. Die drei weiteren Proofs beziehen sich auf andere historische Dateien. Kein Proof beweist Urheberschaft, Identität oder Wahrheit des Inhalts. Ohne Originaldatei ist nicht nachgewiesen, dass eine bestimmte Datei zum Hash passt.

| Historische Originaldatei | Erwarteter SHA-256 | Blockhöhen im Proof |
|---|---|---|
| `ROOT.preimage` | `b3aeee619d9cb691cc6618466407d56598e830c53c6d024748d4582887c57d13` | 971315, 971319, 971354, 971357 |
| `MANIFEST.json` | `244aaceb16c69fc6beeb47c3861fae9bcb8fb6b96e94091d047f61323f46d2f8` | 971315, 971319, 971354, 971357 |
| `ZERO-MNEMONICS.0s` | `4b80e7493bf1523a76156f9ae16abc71952003a0d7d2889ebccc34492abdc8b3` | 971460, 971462, 971480, 971484 |
| `LLM-INIT-PROMPT.md` | `179688251bc2569270922f4cadfc79e138ce688963df951946c74eabde44dbfd` | 971460, 971462, 971480, 971484 |

Die Höhen liest das Skript aus den Proofs; die Tabelle ist keine zusätzliche Vorgabe. Es verlangt mindestens eine Bitcoin-Attestation und prüft alle gefundenen: Es berechnet für jeden Proof-Zweig die Merkle-Root und vergleicht sie mit dem Block derselben Höhe. Ein gültig aussehender, aber abweichender Explorer-Wert führt zum Fehler. `mempool.space` ist die primäre Quelle, `blockstream.info` nur Fallback bei Abruf- oder Formatfehlern; beide werden nicht systematisch verglichen. Der Explorer erfährt IP-Adresse und Blockhöhen. Das Skript validiert **weder Header noch Proof-of-Work oder Bitcoin-Konsens**; ein eigener synchronisierter Node bietet eine andere Vertrauensbasis.

Im Paketverzeichnis, mit Python 3, Internet und z. B. einer virtuellen Umgebung:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install 'opentimestamps==0.4.5'
./verify-anchor.sh
python test_verify_anchor.py
```

Exit-Code 0 der ersten Prüfung bedeutet: Alle vier erwarteten Digests und alle gefundenen Bitcoin-Attestationen stimmen mit den Explorer-Antworten überein. Ein anderer Exit-Code bedeutet **keine vollständige Bestätigung**, auch bei Netzwerk- oder Bibliotheksfehlern. Die Tests verwenden gespeicherte Vergleichswerte und Mocks, keine aktuelle Blockchain-Abfrage. Optional prüft `./verify-anchor.sh --original-dir /pfad/zu/historischen-originalen` zusätzlich alle vier Originaldateien lokal; dabei werden diese nicht an Explorer gesendet. Die gleichnamigen aktuellen Bundle-Dateien sind nicht die historischen Originale.

Für eine alternative Node-basierte Prüfung, mit installiertem `opentimestamps-client` und korrekt konfiguriertem synchronisiertem Bitcoin-Node, zum Beispiel:

```sh
ots --no-cache verify -d b3aeee619d9cb691cc6618466407d56598e830c53c6d024748d4582887c57d13 ROOT.preimage.ots
```

Eine fehlende Node-Verbindung ist keine Bestätigung; je nach Client ist die erste erfolgreiche Attestation nicht die Prüfung aller Attestationen. Bitcoin-Blockzeiten sind keine sekundengenaue Wanduhr. Herkunft und Vertrauenswürdigkeit des öffentlichen Schlüssels, der erwarteten Hashes, der Proofs und des Skripts müssen unabhängig beurteilt werden.

**Datenschutz:** Proofs enthalten Hashes und können Blockhöhen, Verzweigungen und Calendar-URLs enthalten. Erratbare Originale können durch Kandidatenvergleiche identifiziert werden; Metadaten erlauben weitere Verknüpfungen. Keine pauschale Anonymitätsgarantie.

## English

The four OpenTimestamps proofs allow an **explorer-based comparison** of historical SHA-256 fingerprints with Bitcoin block Merkle roots without publishing the original files. `ROOT.preimage.ots` corresponds to the historical PID 1 anchor; the **current bundle root is different and is not automatically Bitcoin-timestamped**. The other three proofs concern other historical files. None proves authorship, identity, or truth. Without the original file, the proof does not establish that a particular file matches the digest. Expected digests and historical block heights are listed in the table above.

The verifier reads heights from the proofs, requires at least one Bitcoin attestation and checks every one: it computes each proof branch's Merkle root and compares it with the block at that same height. A valid-looking but mismatching explorer response fails verification. `mempool.space` is primary; `blockstream.info` is a fallback only on fetch or format errors, not a systematic cross-check. The explorer sees your IP address and requested heights. The script validates **neither headers, proof of work nor Bitcoin consensus**; a synchronized node provides a different trust basis.

From the package directory, run the installation and verification commands above. Exit code 0 for `./verify-anchor.sh` means all four expected digests and all Bitcoin attestations found match explorer responses. Any other exit code is **not a full confirmation**, including network and dependency failures. The offline tests use fixed comparison data and mocks, not a current blockchain query. Optionally, `./verify-anchor.sh --original-dir /path/to/historical-originals` additionally checks all four original files locally, without sending them to explorers. Current bundle files with the same names are not the historical originals.

For a node-based alternative, install `opentimestamps-client`, configure a synchronized Bitcoin node and run the `ots` command above. A missing node connection is not confirmation; depending on the client, the first successful attestation is not a check of all attestations. Bitcoin block times are not second-accurate wall clocks. Independently assess the provenance and trustworthiness of the public key, expected hashes, proofs and script.

**Privacy:** Proofs contain hashes and may contain block heights, branches and calendar URLs. Guessable originals can be identified through candidate comparisons, and metadata may enable further correlations. There is no blanket anonymity guarantee.
