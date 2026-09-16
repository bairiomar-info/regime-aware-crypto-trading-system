"""Serializable, fingerprint-linked research experiment results."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
import hashlib
import json

from .alpha_evidence import AlphaEvidence
from .experiment_manifest import ExperimentManifest


@dataclass(frozen=True)
class ExperimentResult:
    manifest_fingerprint: str
    alpha_evidence: AlphaEvidence


def _json_default(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(f"unsupported result value: {type(value).__name__}")


def serialize_experiment_result(result: ExperimentResult) -> str:
    """Serialize an experiment result deterministically for archival/reporting."""
    payload = asdict(result)
    return json.dumps(payload, default=_json_default, sort_keys=True, separators=(",", ":"))


def fingerprint_experiment_result(result: ExperimentResult) -> str:
    """Return a stable SHA-256 fingerprint of the serialized result."""
    return hashlib.sha256(serialize_experiment_result(result).encode("utf-8")).hexdigest()


def bind_result_to_manifest(manifest: ExperimentManifest, evidence: AlphaEvidence) -> ExperimentResult:
    """Bind evidence to the exact experiment manifest that produced it."""
    return ExperimentResult(manifest_fingerprint=manifest.fingerprint(), alpha_evidence=evidence)
