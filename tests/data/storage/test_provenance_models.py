from datetime import UTC, datetime

import pytest

from trading_system.data.storage import (
    AcquisitionRun,
    ArtifactAcquisition,
    ChecksumStatus,
    RawArtifact,
)


def test_raw_artifact_is_immutable_content_identity():
    artifact = RawArtifact(
        artifact_id="sha256:abc123",
        sha256="a" * 64,
        byte_size=1024,
        media_type="application/zip",
        compression="zip",
    )
    assert artifact.sha256 == "a" * 64
    with pytest.raises((TypeError, ValueError)):
        artifact.byte_size = 1


def test_raw_artifact_rejects_invalid_sha256():
    with pytest.raises(ValueError):
        RawArtifact(artifact_id="artifact-1", sha256="not-a-sha256", byte_size=1)


def test_artifact_acquisition_records_provider_checksum_separately():
    acquisition = ArtifactAcquisition(
        acquisition_id="acq-1",
        artifact_id="sha256:abc123",
        provider="binance",
        source_locator="https://example.test/file.zip",
        retrieved_at=datetime(2026, 9, 2, tzinfo=UTC),
        provider_checksum="a" * 64,
        checksum_status=ChecksumStatus.VERIFIED,
        retrieval_status="completed",
    )
    assert acquisition.checksum_status is ChecksumStatus.VERIFIED
    assert acquisition.provider_checksum == "a" * 64


def test_artifact_acquisition_requires_utc_timestamp():
    with pytest.raises(ValueError):
        ArtifactAcquisition(
            acquisition_id="acq-1",
            artifact_id="artifact-1",
            provider="binance",
            source_locator="https://example.test/file.zip",
            retrieved_at=datetime(2026, 9, 2),
            retrieval_status="completed",
        )


def test_acquisition_run_links_artifact_acquisitions_and_code():
    run = AcquisitionRun(
        run_id="run-1",
        started_at=datetime(2026, 9, 2, 10, tzinfo=UTC),
        completed_at=datetime(2026, 9, 2, 10, 1, tzinfo=UTC),
        status="completed",
        code_commit="2343a4d",
        configuration_hash="b" * 64,
        artifact_acquisition_ids=("acq-1",),
    )
    assert run.artifact_acquisition_ids == ("acq-1",)
    assert run.code_commit == "2343a4d"


def test_acquisition_run_rejects_reversed_times():
    with pytest.raises(ValueError):
        AcquisitionRun(
            run_id="run-1",
            started_at=datetime(2026, 9, 2, 10, 1, tzinfo=UTC),
            completed_at=datetime(2026, 9, 2, 10, tzinfo=UTC),
            status="failed",
        )
