"""Generate test CA, server and client certificates for mTLS testing.

Outputs (default under _dev/mtls_test/):
- ca.key.pem, ca.cert.pem
- server.key.pem, server.cert.pem
- client.key.pem, client.cert.pem

Usage:
    python scripts/gen_mtls_test_certs.py --out _dev/mtls_test

This uses `cryptography` and is intended for test/staging only.
"""
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import BestAvailableEncryption, NoEncryption
from datetime import datetime, timedelta
from pathlib import Path
import argparse

DEFAULT_OUT = Path(__file__).resolve().parent.parent / '_dev' / 'mtls_test'

def write_pem(path: Path, data: bytes, mode: int = 0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        f.write(data)
    try:
        path.chmod(mode)
    except Exception:
        pass


def gen_rsa_key(bits: int = 2048):
    return rsa.generate_private_key(public_exponent=65537, key_size=bits)


def make_ca(subject_name: str, key, days=3650):
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, subject_name),
    ])
    now = datetime.utcnow()
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=days))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )
    return cert


def make_cert(subject_name: str, key, ca_cert, ca_key, san_names=None, is_client=False, days=365):
    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, subject_name),
    ])
    now = datetime.utcnow()
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=days))
    )
    # SANs
    if san_names:
        san = x509.SubjectAlternativeName([x509.DNSName(n) for n in san_names])
        builder = builder.add_extension(san, critical=False)

    # Extended usage
    eku = x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]) if is_client else x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH])
    builder = builder.add_extension(eku, critical=False)

    # Key usage
    builder = builder.add_extension(
        x509.KeyUsage(digital_signature=True, key_encipherment=True, content_commitment=False,
                      data_encipherment=False, key_agreement=False, key_cert_sign=False, crl_sign=False,
                      encipher_only=False, decipher_only=False), critical=True
    )

    cert = builder.sign(private_key=ca_key, algorithm=hashes.SHA256())
    return cert


def serialize_key(key, password=None):
    if password:
        enc = BestAvailableEncryption(password.encode())
    else:
        enc = NoEncryption()
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=enc
    )


def serialize_cert(cert):
    return cert.public_bytes(serialization.Encoding.PEM)


def main(out_dir: Path, passphrase: str = None):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ca_key = gen_rsa_key(4096)
    ca_cert = make_ca('cthulu-test-ca', ca_key)

    server_key = gen_rsa_key(2048)
    server_cert = make_cert('cthulu-rpc-server', server_key, ca_cert, ca_key, san_names=['127.0.0.1', 'localhost'])

    client_key = gen_rsa_key(2048)
    client_cert = make_cert('cthulu-client', client_key, ca_cert, ca_key, is_client=True)

    # Write files
    write_pem(out_dir / 'ca.key.pem', serialize_key(ca_key, passphrase))
    write_pem(out_dir / 'ca.cert.pem', serialize_cert(ca_cert))

    write_pem(out_dir / 'server.key.pem', serialize_key(server_key))
    write_pem(out_dir / 'server.cert.pem', serialize_cert(server_cert))

    write_pem(out_dir / 'client.key.pem', serialize_key(client_key))
    write_pem(out_dir / 'client.cert.pem', serialize_cert(client_cert))

    print('Generated test certs under', str(out_dir))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=str, default=str(DEFAULT_OUT))
    parser.add_argument('--password', type=str, default=None, help='Optional passphrase for CA key')
    args = parser.parse_args()
    main(Path(args.out), passphrase=args.password)
