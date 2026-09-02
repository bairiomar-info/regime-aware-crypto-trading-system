from datetime import UTC, datetime

import pytest

from trading_system.data.storage import (
    AcquisitionRun,
    ArtifactAcquisition,
    CanonicalDatasetManifest,
    CanonicalDatasetResource,
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


def _resource(path: str, rows: int, start_hour: int, end_hour: int) -> CanonicalDatasetResource:
    return CanonicalDatasetResource(
        path=path,
        sha256="c" * 64,
        byte_size=rows * 100,
        row_count=rows,
        min_timestamp=datetime(2026, 9, 1, start_hour, tzinfo=UTC),
        max_timestamp=datetime(2026, 9, 1, end_hour, tzinfo=UTC),
    )


def test_canonical_resource_records_file_integrity_and_bounds():
    resource = _resource("data/BTCUSDT/1h/part-000.parquet", 24, 0, 23)
    assert resource.row_count == 24
    assert resource.sha256 == "c" * 64


def test_canonical_manifest_preserves_dataset_version_and_processing_versions():
    resource = _resource("data/BTCUSDT/1h/part-000.parquet", 24, 0, 23)
    manifest = CanonicalDatasetManifest(
        dataset_id="spot_ohlcv",
        dataset_version="v1.0.0",
        schema_version="v1",
        normalization_version="v1",
        validation_version="v1",
        input_artifact_ids=("artifact-1",),
        code_commit="0498274b",
        configuration_hash="d" * 64,
        resources=(resource,),
        total_row_count=24,
        min_timestamp=resource.min_timestamp,
        max_timestamp=resource.max_timestamp,
    )
    assert manifest.dataset_id == "spot_ohlcv"
    assert manifest.dataset_version == "v1.0.0"
    assert manifest.input_artifact_ids == ("artifact-1",)


def test_canonical_manifest_requires_semantic_version():
    resource = _resource("data/part.parquet", 1, 0, 0)
    with pytest.raises(ValueError):
        CanonicalDatasetManifest(
            dataset_id="spot_ohlcv",
            dataset_version="latest",
            schema_version="v1",
            normalization_version="v1",
            validation_version="v1",
            resources=(resource,),
            total_row_count=1,
            min_timestamp=resource.min_timestamp,
            max_timestamp=resource.max_timestamp,
        )


def test_canonical_manifest_rejects_incorrect_total_row_count():
    resource = _resource("data/part.parquet", 10, 0, 9)
    with pytest.raises(ValueError):
        CanonicalDatasetManifest(
            dataset_id="spot_ohlcv",
            dataset_version="v1.0.0",
            schema_version="v1",
            normalization_version="v1",
            validation_version="v1",
            resources=(resource,),
            total_row_count=9,
            min_timestamp=resource.min_timestamp,
            max_timestamp=resource.max_timestamp,
        )


def test_canonical_manifest_rejects_incorrect_dataset_bounds():
    resource = _resource("data/part.parquet", 10, 2, 11)
    with pytest.raises(ValueError):
        CanonicalDatasetManifest(
            dataset_id="spot_ohlcv",
            dataset_version="v1.0.0",
            schema_version="v1",
            normalization_version="v1",
            validation_version="v1",
            resources=(resource,),
            total_row_count=10,
            min_timestamp=datetime(2026, 9, 1, 1, tzinfo=UTC),
            max_timestamp=resource.max_timestamp,
        )
