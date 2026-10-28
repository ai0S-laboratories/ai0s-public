#!/usr/bin/env python3
"""Verify all Bitcoin attestations in the four staged OTS proofs via an explorer.

This does not validate Bitcoin's consensus chain or prove an owner's identity.
"""
import argparse
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

try:
    from opentimestamps.core.notary import BitcoinBlockHeaderAttestation
    from opentimestamps.core.op import OpSHA256
    from opentimestamps.core.serialize import BytesDeserializationContext
    from opentimestamps.core.timestamp import DetachedTimestampFile
except ImportError as exc:
    sys.exit(f"FEHLER: OpenTimestamps-Bibliothek fehlt ({exc}); siehe Anleitung.")

EXPECTED = {
    'ROOT.preimage.ots': 'b3aeee619d9cb691cc6618466407d56598e830c53c6d024748d4582887c57d13',
    'MANIFEST.json.ots': '244aaceb16c69fc6beeb47c3861fae9bcb8fb6b96e94091d047f61323f46d2f8',
    'ZERO-MNEMONICS.0s.ots': '4b80e7493bf1523a76156f9ae16abc71952003a0d7d2889ebccc34492abdc8b3',
    'LLM-INIT-PROMPT.md.ots': '179688251bc2569270922f4cadfc79e138ce688963df951946c74eabde44dbfd',
}
EXPLORERS = ('https://mempool.space/api', 'https://blockstream.info/api')
HEX256 = re.compile(r'[0-9a-f]{64}\Z')
MAX_RESPONSE = 131072


class VerificationError(Exception):
    pass


def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'ai0s-ots-verifier/1.0'})
    with urllib.request.urlopen(request, timeout=20) as response:
        data = response.read(MAX_RESPONSE + 1)
    if len(data) > MAX_RESPONSE:
        raise ValueError('Explorer-Antwort zu groß')
    return data.decode('utf-8')


def explorer_merkle(height):
    """Use one provider per attempt; fallback only if an entire attempt fails."""
    errors = []
    for base in EXPLORERS:
        try:
            block_hash = fetch(f'{base}/block-height/{height}').strip()
            if not HEX256.fullmatch(block_hash):
                raise ValueError('ungültiger Block-Hash')
            block = json.loads(fetch(f'{base}/block/{block_hash}'))
            if not isinstance(block, dict) or block.get('id') != block_hash or block.get('height') != height:
                raise ValueError('Block-ID oder Höhe stimmen nicht')
            root = block.get('merkle_root')
            if not isinstance(root, str) or not HEX256.fullmatch(root):
                raise ValueError('ungültige Merkle-Root')
            print(f'   Explorer: {base} (Block {height}, Hash {block_hash})')
            return root
        except (OSError, ValueError, TypeError, UnicodeError) as exc:
            errors.append(f'{base}: {exc}')
    raise VerificationError(f'Block {height}: kein Explorer lieferte gültige Daten: ' + '; '.join(errors))


def verify_proof(path, expected_digest, resolve_root, original=None):
    """Raise VerificationError unless the digest and every Bitcoin attestation match."""
    try:
        proof = DetachedTimestampFile.deserialize(BytesDeserializationContext(path.read_bytes()))
        if not isinstance(proof.file_hash_op, OpSHA256):
            raise VerificationError('Proof nutzt nicht SHA-256')
        if proof.file_digest.hex() != expected_digest:
            raise VerificationError('Proof-Digest stimmt nicht mit erwartetem SHA-256 überein')
        if original is not None:
            h = hashlib.sha256()
            with original.open('rb') as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b''):
                    h.update(chunk)
            if h.digest() != proof.file_digest:
                raise VerificationError('Originaldatei stimmt nicht mit Proof-Digest überein')
        pairs = [(att.height, msg[::-1].hex()) for msg, att in proof.timestamp.all_attestations()
                 if isinstance(att, BitcoinBlockHeaderAttestation)]
        if not pairs:
            raise VerificationError('keine Bitcoin-Attestation vorhanden')
        for height, root in sorted(pairs):
            if not isinstance(height, int) or height < 0 or not HEX256.fullmatch(root):
                raise VerificationError('ungültige Attestation (Höhe oder Root)')
            chain_root = resolve_root(height)
            if not isinstance(chain_root, str) or not HEX256.fullmatch(chain_root):
                raise VerificationError(f'Block {height}: keine gültige Explorer-Root')
            if root != chain_root:
                raise VerificationError(f'Block {height}: Root stimmt nicht (Proof {root}, Explorer {chain_root})')
            print(f'   OK: Block {height}, Merkle-Root {root}')
        return len(pairs)
    except VerificationError:
        raise
    except Exception as exc:
        raise VerificationError(f'Proof/Original/Explorer nicht auswertbar: {type(exc).__name__}: {exc}') from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--original-dir', type=Path, help='Verzeichnis mit allen vier Originaldateien (optional)')
    args = parser.parse_args(argv)
    directory = Path(__file__).resolve().parent
    cache = {}
    def resolve(height):
        if height not in cache:
            cache[height] = explorer_merkle(height)
        return cache[height]
    failed = 0
    for name, digest in EXPECTED.items():
        print(f'── {name}')
        original = args.original_dir / name[:-4] if args.original_dir else None
        try:
            count = verify_proof(directory / name, digest, resolve, original)
            print(f'   PASS: Digest und {count} Bitcoin-Attestation(en)' + ('; Originaldatei stimmt' if original else '; Originaldatei nicht geprüft'))
        except VerificationError as exc:
            print(f'   FAIL: {exc}', file=sys.stderr)
            failed += 1
    print(f'Ergebnis: {len(EXPECTED) - failed} bestanden, {failed} fehlgeschlagen.')
    print('Explorer-Abgleich; keine lokale Bitcoin-Chain-Verifikation und kein Identitätsnachweis.')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
