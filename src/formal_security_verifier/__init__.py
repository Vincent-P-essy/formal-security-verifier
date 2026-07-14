"""Self-contained explicit-state and relational security verification."""

from .models import Method, Verdict, VerificationResult
from .verifier import verify, verify_all

__all__ = ["Method", "Verdict", "VerificationResult", "verify", "verify_all"]
__version__ = "0.2.0"
