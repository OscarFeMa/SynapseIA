"""
Synapse Security: TLS/SSL Configuration and Enforcement
Provides secure communication channels between Master and Workers.
"""
import ssl
import os
import socket
import logging
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class TLSConfig:
    """Manages TLS certificates and SSL context creation."""
    
    def __init__(self, 
                 cert_dir: str = "certs",
                 require_tls: bool = False):
        self.cert_dir = Path(cert_dir)
        self.require_tls = require_tls or os.getenv("SYNAPSE_REQUIRE_TLS", "false").lower() == "true"
        
        self.cert_file = self.cert_dir / "server.crt"
        self.key_file = self.cert_dir / "server.key"
        self.ca_file = self.cert_dir / "ca.crt"
        
        # Ensure directory exists
        if self.require_tls:
            self.cert_dir.mkdir(parents=True, exist_ok=True)

    def generate_self_signed(self, days: int = 365):
        """
        Generate self-signed certificates for development/testing.
        In production, use Let's Encrypt or a corporate CA.
        """
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.backends import default_backend
            
            logger.info("Generating self-signed certificates...")
            
            # Generate private key
            key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            
            # Generate certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "California"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "San Francisco"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Synapse Council"),
                x509.NameAttribute(NameOID.COMMON_NAME, "synapse.local"),
            ])
            
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                x509.datetime_utcnow()
            ).not_valid_after(
                x509.datetime_utcnow() + datetime.timedelta(days=days)
            ).add_extension(
                x509.SubjectAlternativeName([x509.DNSName("localhost")]),
                critical=False,
            ).sign(key, hashes.SHA256(), default_backend())
            
            # Write files
            with open(self.key_file, "wb") as f:
                f.write(key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            with open(self.cert_file, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            # Create a dummy CA file (self-signed acts as its own CA)
            with open(self.ca_file, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            
            # Set restrictive permissions
            os.chmod(self.key_file, 0o600)
            os.chmod(self.cert_file, 0o644)
            os.chmod(self.ca_file, 0o644)
            
            logger.info(f"Certificates generated in {self.cert_dir}")
            return True
            
        except ImportError:
            logger.error("cryptography library not installed. Run: pip install cryptography")
            return False
        except Exception as e:
            logger.error(f"Failed to generate certificates: {e}")
            return False

    def create_ssl_context(self, server_mode: bool = True) -> Optional[ssl.SSLContext]:
        """Create an SSL context for secure connections."""
        
        if not self.require_tls:
            logger.warning("TLS is disabled. Connections will be unencrypted.")
            return None
        
        # Check if certs exist
        if not self.cert_file.exists() or not self.key_file.exists():
            logger.warning("Certificates not found. Attempting to generate self-signed...")
            if not self.generate_self_signed():
                logger.error("Failed to generate certificates. TLS disabled.")
                return None
        
        try:
            if server_mode:
                context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                context.load_cert_chain(str(self.cert_file), str(self.key_file))
                
                # Client verification optional by default
                context.verify_mode = ssl.CERT_OPTIONAL
                if self.ca_file.exists():
                    context.load_verify_locations(str(self.ca_file))
            else:
                context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
                context.check_hostname = False  # Disable for self-signed dev certs
                context.verify_mode = ssl.CERT_REQUIRED
                if self.ca_file.exists():
                    context.load_verify_locations(str(self.ca_file))
                elif self.cert_file.exists():
                    # Use server cert as CA for self-signed
                    context.load_verify_locations(str(self.cert_file))
            
            # Modern security settings
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            context.set_ciphers('ECDHE+AESGCM:DHE+AESGCM:ECDHE+CHACHA20:DHE+CHACHA20')
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to create SSL context: {e}")
            return None

    def wrap_socket(self, sock: socket.socket, server_mode: bool = True) -> Optional[socket.socket]:
        """Wrap a socket with SSL."""
        context = self.create_ssl_context(server_mode)
        if not context:
            return None
        
        try:
            return context.wrap_socket(sock, server_side=server_mode)
        except Exception as e:
            logger.error(f"Failed to wrap socket: {e}")
            return None

# Global instance
tls_config = TLSConfig()
