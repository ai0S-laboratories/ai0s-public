#!/usr/bin/env python3
"""Offline regression tests; use copies of real proofs, never modify originals."""
import contextlib
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from opentimestamps.core.notary import BitcoinBlockHeaderAttestation, PendingAttestation
from opentimestamps.core.serialize import BytesDeserializationContext, BytesSerializationContext
from opentimestamps.core.timestamp import DetachedTimestampFile, Timestamp

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('verify_anchor', HERE / 'verify-anchor.py')
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)

# Fixed explorer roots, independent of the proof parser under test.
ROOTS = {
    971315: 'c0757f1deafecc2af78ca090bd3be81aec20081b338fb899dd8d559f6ec33be2',
    971319: 'b446c3cfddd1d36d3f7d71e7e80a404e82597177e2dd1d213c72f715c8ee6758',
    971354: '6d498b0ede92db1ba6d70293479a8e2a111c5ddaed3125a79f75e7820dd15897',
    971357: '54b7335b497613149a074d33593153fc25096eb0ba5a1bc29fce0da755296838',
    971460: 'e9ba5670bae75eeeb4d3b8e193f5f690c31b006b6b3a5821f16872e208932bc7',
    971462: '6a0dc7ec15a54a7cca663cfe3c1c336471196a72862a970aac5db3b204887b1f',
    971480: 'e290c76ddcb9ef1ec0b6dd4cf2dff983432ac83eee17cf7b915f68159f942ddb',
    971484: '3ca7dea0b874c13e9b74cd90a91cebb421f4449006b168fc5967af030349ac34',
}


def load(name):
    return DetachedTimestampFile.deserialize(BytesDeserializationContext((HERE / name).read_bytes()))


def save(proof, path):
    ctx = BytesSerializationContext()
    proof.serialize(ctx)
    path.write_bytes(ctx.getbytes())


def nodes(stamp):
    yield stamp
    for child in stamp.ops.values():
        yield from nodes(child)


class VerifyAnchorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.copy = Path(self.tmp.name) / 'ROOT.preimage.ots'
        self.copy.write_bytes((HERE / self.copy.name).read_bytes())
        self.digest = verifier.EXPECTED[self.copy.name]
        self.roots = ROOTS

    def check(self, original=None):
        return verifier.verify_proof(self.copy, self.digest, self.roots.__getitem__, original)

    def test_original_proofs_all_attestations(self):
        for name, digest in verifier.EXPECTED.items():
            proof = load(name)
            attestations = [(msg, a) for msg, a in proof.timestamp.all_attestations()
                            if isinstance(a, BitcoinBlockHeaderAttestation)]
            self.assertEqual(len(attestations), 4)
            self.assertEqual(verifier.verify_proof(HERE / name, digest, ROOTS.__getitem__), 4)

    def test_swapped_heights_rejected(self):
        proof = load(self.copy.name)
        for node in nodes(proof.timestamp):
            node.attestations = {BitcoinBlockHeaderAttestation({971315: 971354, 971354: 971315}.get(a.height, a.height))
                                 if isinstance(a, BitcoinBlockHeaderAttestation) else a for a in node.attestations}
        save(proof, self.copy)
        with self.assertRaises(verifier.VerificationError):
            self.check()

    def test_parseable_path_change_rejected(self):
        data = bytearray(self.copy.read_bytes())
        data[129] ^= 1
        self.copy.write_bytes(data)
        load_from_copy = DetachedTimestampFile.deserialize(BytesDeserializationContext(bytes(data)))
        self.assertEqual(load_from_copy.file_digest.hex(), self.digest)
        with self.assertRaises(verifier.VerificationError):
            self.check()

    def test_wrong_expected_digest_rejected(self):
        with self.assertRaises(verifier.VerificationError):
            verifier.verify_proof(self.copy, '00' * 32, self.roots.__getitem__)

    def test_truncated_and_trailing_proof_rejected(self):
        original = self.copy.read_bytes()
        for data in (original[:30], original + b'garbage'):
            self.copy.write_bytes(data)
            with self.subTest(length=len(data)), self.assertRaises(verifier.VerificationError):
                self.check()

    def test_no_bitcoin_attestation_rejected(self):
        proof = load(self.copy.name)
        stamp = Timestamp(proof.file_digest)
        stamp.attestations.add(PendingAttestation('https://example.org'))
        proof.timestamp = stamp
        save(proof, self.copy)
        with self.assertRaises(verifier.VerificationError):
            self.check()

    def test_missing_or_invalid_root_rejected(self):
        for resolver in (lambda h: '', lambda h: None, lambda h: 'zz' * 32,
                         mock.Mock(side_effect=OSError('unavailable'))):
            with self.subTest(resolver=resolver), self.assertRaises(verifier.VerificationError):
                verifier.verify_proof(self.copy, self.digest, resolver)

    def test_original_file_must_match(self):
        original = Path(self.tmp.name) / 'original'
        original.write_bytes(b'not the original')
        with self.assertRaises(verifier.VerificationError):
            self.check(original)
        with self.assertRaises(verifier.VerificationError):
            self.check(original.parent / 'missing')

    def test_original_file_success_using_synthetic_proof(self):
        original = Path(self.tmp.name) / 'original'
        original.write_bytes(b'known content')
        proof = load(self.copy.name)
        stamp = Timestamp(hashlib.sha256(original.read_bytes()).digest())
        stamp.attestations.add(BitcoinBlockHeaderAttestation(7))
        proof.timestamp = stamp
        save(proof, self.copy)
        digest = hashlib.sha256(original.read_bytes()).hexdigest()
        self.assertEqual(verifier.verify_proof(self.copy, digest, lambda h: bytes.fromhex(digest)[::-1].hex(), original), 1)

    def test_main_exit_status_for_success_and_failure(self):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            with mock.patch.object(verifier, 'verify_proof', return_value=4):
                self.assertEqual(verifier.main([]), 0)
            with mock.patch.object(verifier, 'verify_proof', side_effect=verifier.VerificationError('failed')):
                self.assertEqual(verifier.main([]), 1)

    def test_explorer_fallback_uses_same_provider_for_both_requests(self):
        block_hash, root = '12' * 32, '34' * 32
        class Response:
            def __init__(self, data): self.data = data
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, size): return self.data
        calls = []
        def get(req, timeout):
            url = req.full_url
            calls.append(url)
            if 'mempool.space' in url: raise OSError('offline')
            if '/block-height/' in url: return Response(block_hash.encode())
            return Response(json.dumps({'id': block_hash, 'height': 7, 'merkle_root': root}).encode())
        with mock.patch.object(verifier.urllib.request, 'urlopen', side_effect=get):
            self.assertEqual(verifier.explorer_merkle(7), root)
        self.assertEqual(len(calls), 3)
        self.assertTrue(all('blockstream.info' in url for url in calls[1:]))

    def test_explorer_malformed_response_and_all_down_fail(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, size): return b'not-a-block-hash'
        with mock.patch.object(verifier.urllib.request, 'urlopen', return_value=Response()):
            with self.assertRaises(verifier.VerificationError): verifier.explorer_merkle(7)
        with mock.patch.object(verifier.urllib.request, 'urlopen', side_effect=OSError('down')):
            with self.assertRaises(verifier.VerificationError): verifier.explorer_merkle(7)


if __name__ == '__main__':
    unittest.main(verbosity=2)
