import pytest
from src.domain.shared.value_objects import (
    ImageArtifactID,
    ImageURI,
    ImageMetadata,
    ImageMimeType,
    ImageWidth,
    ImageHeight,
)
from src.domain.shared.entities import ImageArtifact
from src.domain.shared.specifications import FieldSpecification, OrSpecification


# Tests for add method

def test_add_image_artifact_successfully(sqlmodel_image_artifact_repo, session, sample_image_artifact):
    """Test that adding an image artifact saves it to the database."""
    sqlmodel_image_artifact_repo.add(sample_image_artifact)
    session.commit()
    
    retrieved = sqlmodel_image_artifact_repo.get_by_id(sample_image_artifact.id)
    
    assert retrieved is not None
    assert retrieved.id == sample_image_artifact.id
    assert retrieved.blob_ref == sample_image_artifact.blob_ref
    assert retrieved.metadata.mime_type == sample_image_artifact.metadata.mime_type
    assert retrieved.metadata.width == sample_image_artifact.metadata.width
    assert retrieved.metadata.height == sample_image_artifact.metadata.height


def test_add_multiple_image_artifacts(sqlmodel_image_artifact_repo, session):
    """Test that multiple image artifacts can be added."""
    artifact1 = ImageArtifact(
        id=ImageArtifactID.next_id(),
        blob_ref=ImageURI("s3://bucket/image1.png"),
        metadata=ImageMetadata(
            mime_type=ImageMimeType("image/png"),
            width=ImageWidth(800),
            height=ImageHeight(600),
        ),
    )
    artifact2 = ImageArtifact(
        id=ImageArtifactID.next_id(),
        blob_ref=ImageURI("s3://bucket/image2.jpg"),
        metadata=ImageMetadata(
            mime_type=ImageMimeType("image/jpeg"),
            width=ImageWidth(1024),
            height=ImageHeight(768),
        ),
    )
    
    sqlmodel_image_artifact_repo.add(artifact1)
    sqlmodel_image_artifact_repo.add(artifact2)
    session.commit()
    
    all_artifacts = sqlmodel_image_artifact_repo.list_all()
    
    assert len(all_artifacts) == 2


def test_add_image_artifact_without_commit_not_persisted(sqlmodel_image_artifact_repo, session, sample_image_artifact):
    """Test that image artifact is not persisted without commit."""
    sqlmodel_image_artifact_repo.add(sample_image_artifact)
    # No commit
    session.rollback()
    
    retrieved = sqlmodel_image_artifact_repo.get_by_id(sample_image_artifact.id)
    
    assert retrieved is None


# Tests for get_by_id method

def test_get_by_id_existing_image_artifact(sqlmodel_image_artifact_repo, session, sample_image_artifact):
    """Test retrieving an existing image artifact by ID."""
    sqlmodel_image_artifact_repo.add(sample_image_artifact)
    session.commit()
    
    retrieved = sqlmodel_image_artifact_repo.get_by_id(sample_image_artifact.id)
    
    assert retrieved is not None
    assert retrieved.id == sample_image_artifact.id
    assert retrieved.blob_ref == sample_image_artifact.blob_ref


def test_get_by_id_nonexistent_image_artifact(sqlmodel_image_artifact_repo):
    """Test that getting a nonexistent image artifact returns None."""
    nonexistent_id = ImageArtifactID.next_id()
    
    retrieved = sqlmodel_image_artifact_repo.get_by_id(nonexistent_id)
    
    assert retrieved is None


def test_get_by_id_returns_correct_image_artifact(sqlmodel_image_artifact_repo, session):
    """Test that get_by_id returns the correct image artifact when multiple exist."""
    artifact1 = ImageArtifact(
        id=ImageArtifactID.next_id(),
        blob_ref=ImageURI("s3://bucket/image1.png"),
        metadata=ImageMetadata(
            mime_type=ImageMimeType("image/png"),
            width=ImageWidth(800),
            height=ImageHeight(600),
        ),
    )
    artifact2 = ImageArtifact(
        id=ImageArtifactID.next_id(),
        blob_ref=ImageURI("s3://bucket/image2.jpg"),
        metadata=ImageMetadata(
            mime_type=ImageMimeType("image/jpeg"),
            width=ImageWidth(1024),
            height=ImageHeight(768),
        ),
    )
    
    sqlmodel_image_artifact_repo.add(artifact1)
    sqlmodel_image_artifact_repo.add(artifact2)
    session.commit()
    
    retrieved = sqlmodel_image_artifact_repo.get_by_id(artifact1.id)
    
    assert retrieved is not None
    assert retrieved.id == artifact1.id
    assert retrieved.blob_ref.value == "s3://bucket/image1.png"


# Tests for list_all method

def test_list_all_empty_repository(sqlmodel_image_artifact_repo):
    """Test that list_all returns empty list when no image artifacts exist."""
    result = sqlmodel_image_artifact_repo.list_all()
    
    assert result == []


def test_list_all_single_image_artifact(sqlmodel_image_artifact_repo, session, sample_image_artifact):
    """Test that list_all returns single image artifact."""
    sqlmodel_image_artifact_repo.add(sample_image_artifact)
    session.commit()
    
    result = sqlmodel_image_artifact_repo.list_all()
    
    assert len(result) == 1
    assert result[0].id == sample_image_artifact.id


def test_list_all_multiple_image_artifacts(sqlmodel_image_artifact_repo, session):
    """Test that list_all returns all image artifacts."""
    artifacts = [
        ImageArtifact(
            id=ImageArtifactID.next_id(),
            blob_ref=ImageURI(f"s3://bucket/image{i}.png"),
            metadata=ImageMetadata(
                mime_type=ImageMimeType("image/png"),
                width=ImageWidth(800),
                height=ImageHeight(600),
            ),
        )
        for i in range(5)
    ]
    
    for artifact in artifacts:
        sqlmodel_image_artifact_repo.add(artifact)
    session.commit()
    
    result = sqlmodel_image_artifact_repo.list_all()
    
    assert len(result) == 5
    result_ids = {str(a.id) for a in result}
    expected_ids = {str(a.id) for a in artifacts}
    assert result_ids == expected_ids


# Tests for find_by_specification method

def test_find_by_specification_with_none_spec(sqlmodel_image_artifact_repo, session):
    """Test that None specification returns all image artifacts."""
    artifacts = [
        ImageArtifact(
            id=ImageArtifactID.next_id(),
            blob_ref=ImageURI(f"s3://bucket/image{i}.png"),
            metadata=ImageMetadata(
                mime_type=ImageMimeType("image/png"),
                width=ImageWidth(800),
                height=ImageHeight(600),
            ),
        )
        for i in range(3)
    ]
    
    for artifact in artifacts:
        sqlmodel_image_artifact_repo.add(artifact)
    session.commit()
    
    result = sqlmodel_image_artifact_repo.find_by_specification(None)
    
    assert len(result) == 3


def test_find_by_specification_with_eq_operator(sqlmodel_image_artifact_repo, session):
    """Test finding image artifacts with equality specification."""
    artifact1 = ImageArtifact(
        id=ImageArtifactID.next_id(),
        blob_ref=ImageURI("s3://bucket/image1.png"),
        metadata=ImageMetadata(
            mime_type=ImageMimeType("image/png"),
            width=ImageWidth(800),
            height=ImageHeight(600),
        ),
    )
    artifact2 = ImageArtifact(
        id=ImageArtifactID.next_id(),
        blob_ref=ImageURI("s3://bucket/image2.jpg"),
        metadata=ImageMetadata(
            mime_type=ImageMimeType("image/jpeg"),
            width=ImageWidth(1024),
            height=ImageHeight(768),
        ),
    )
    
    sqlmodel_image_artifact_repo.add(artifact1)
    sqlmodel_image_artifact_repo.add(artifact2)
    session.commit()
    
    spec = FieldSpecification("mime_type", "eq", "image/png")
    result = sqlmodel_image_artifact_repo.find_by_specification(spec)
    
    assert len(result) == 1
    assert result[0].metadata.mime_type.value == "image/png"


def test_find_by_specification_with_or_specification(sqlmodel_image_artifact_repo, session):
    """Test finding image artifacts with OR specification."""
    artifact1 = ImageArtifact(
        id=ImageArtifactID.next_id(),
        blob_ref=ImageURI("s3://bucket/image1.png"),
        metadata=ImageMetadata(
            mime_type=ImageMimeType("image/png"),
            width=ImageWidth(800),
            height=ImageHeight(600),
        ),
    )
    artifact2 = ImageArtifact(
        id=ImageArtifactID.next_id(),
        blob_ref=ImageURI("s3://bucket/image2.jpg"),
        metadata=ImageMetadata(
            mime_type=ImageMimeType("image/jpeg"),
            width=ImageWidth(1024),
            height=ImageHeight(768),
        ),
    )
    artifact3 = ImageArtifact(
        id=ImageArtifactID.next_id(),
        blob_ref=ImageURI("s3://bucket/image3.webp"),
        metadata=ImageMetadata(
            mime_type=ImageMimeType("image/webp"),
            width=ImageWidth(512),
            height=ImageHeight(512),
        ),
    )
    
    sqlmodel_image_artifact_repo.add(artifact1)
    sqlmodel_image_artifact_repo.add(artifact2)
    sqlmodel_image_artifact_repo.add(artifact3)
    session.commit()
    
    spec1 = FieldSpecification("mime_type", "eq", "image/png")
    spec2 = FieldSpecification("mime_type", "eq", "image/jpeg")
    or_spec = OrSpecification(spec1, spec2)
    
    result = sqlmodel_image_artifact_repo.find_by_specification(or_spec)
    
    assert len(result) == 2
    mime_types = {a.metadata.mime_type.value for a in result}
    assert mime_types == {"image/png", "image/jpeg"}


def test_find_by_specification_no_matches(sqlmodel_image_artifact_repo, session, sample_image_artifact):
    """Test that no matches returns empty list."""
    sqlmodel_image_artifact_repo.add(sample_image_artifact)
    session.commit()
    
    spec = FieldSpecification("mime_type", "eq", "image/gif")
    result = sqlmodel_image_artifact_repo.find_by_specification(spec)
    
    assert result == []


def test_find_by_specification_multiple_mime_types(sqlmodel_image_artifact_repo, session):
    """Test finding multiple artifacts with different mime types."""
    mime_types = ["image/png", "image/jpeg", "image/webp"]
    artifacts = []
    
    for i, mime_type in enumerate(mime_types):
        artifact = ImageArtifact(
            id=ImageArtifactID.next_id(),
            blob_ref=ImageURI(f"s3://bucket/image{i}.{mime_type.split('/')[1]}"),
            metadata=ImageMetadata(
                mime_type=ImageMimeType(mime_type),
                width=ImageWidth(800),
                height=ImageHeight(600),
            ),
        )
        artifacts.append(artifact)
        sqlmodel_image_artifact_repo.add(artifact)
    
    session.commit()
    
    spec = FieldSpecification("mime_type", "eq", "image/png")
    result = sqlmodel_image_artifact_repo.find_by_specification(spec)
    
    assert len(result) == 1
    assert result[0].metadata.mime_type.value == "image/png"


# Tests for update method

def test_update_existing_image_artifact(sqlmodel_image_artifact_repo, session, sample_image_artifact):
    """Test updating an existing image artifact."""
    sqlmodel_image_artifact_repo.add(sample_image_artifact)
    session.commit()
    
    # Modify the artifact
    sample_image_artifact.blob_ref = ImageURI("s3://bucket/updated_image.png")
    sample_image_artifact.metadata = ImageMetadata(
        mime_type=ImageMimeType("image/jpeg"),
        width=ImageWidth(1920),
        height=ImageHeight(1080),
    )
    
    updated = sqlmodel_image_artifact_repo.update(sample_image_artifact)
    session.commit()
    
    assert updated.blob_ref.value == "s3://bucket/updated_image.png"
    assert updated.metadata.mime_type.value == "image/jpeg"
    assert updated.metadata.width.value == 1920
    assert updated.metadata.height.value == 1080
    
    # Verify the update persisted
    retrieved = sqlmodel_image_artifact_repo.get_by_id(sample_image_artifact.id)
    assert retrieved.blob_ref.value == "s3://bucket/updated_image.png"
    assert retrieved.metadata.mime_type.value == "image/jpeg"


def test_update_nonexistent_image_artifact_raises_error(sqlmodel_image_artifact_repo):
    """Test that updating a nonexistent image artifact raises ValueError."""
    nonexistent_artifact = ImageArtifact(
        id=ImageArtifactID.next_id(),
        blob_ref=ImageURI("s3://bucket/image.png"),
        metadata=ImageMetadata(
            mime_type=ImageMimeType("image/png"),
            width=ImageWidth(800),
            height=ImageHeight(600),
        ),
    )
    
    with pytest.raises(ValueError, match="ImageArtifact not found"):
        sqlmodel_image_artifact_repo.update(nonexistent_artifact)


def test_update_preserves_id(sqlmodel_image_artifact_repo, session, sample_image_artifact):
    """Test that update preserves the image artifact ID."""
    original_id = sample_image_artifact.id
    sqlmodel_image_artifact_repo.add(sample_image_artifact)
    session.commit()
    
    sample_image_artifact.blob_ref = ImageURI("s3://bucket/new_image.png")
    
    updated = sqlmodel_image_artifact_repo.update(sample_image_artifact)
    session.commit()
    
    assert updated.id == original_id


def test_update_multiple_times(sqlmodel_image_artifact_repo, session, sample_image_artifact):
    """Test that an image artifact can be updated multiple times."""
    sqlmodel_image_artifact_repo.add(sample_image_artifact)
    session.commit()
    
    # First update
    sample_image_artifact.metadata = ImageMetadata(
        mime_type=ImageMimeType("image/jpeg"),
        width=ImageWidth(1024),
        height=ImageHeight(768),
    )
    sqlmodel_image_artifact_repo.update(sample_image_artifact)
    session.commit()
    
    # Second update
    sample_image_artifact.metadata = ImageMetadata(
        mime_type=ImageMimeType("image/webp"),
        width=ImageWidth(2048),
        height=ImageHeight(1536),
    )
    sqlmodel_image_artifact_repo.update(sample_image_artifact)
    session.commit()
    
    retrieved = sqlmodel_image_artifact_repo.get_by_id(sample_image_artifact.id)
    assert retrieved.metadata.mime_type.value == "image/webp"
    assert retrieved.metadata.width.value == 2048
    assert retrieved.metadata.height.value == 1536


def test_update_only_metadata(sqlmodel_image_artifact_repo, session, sample_image_artifact):
    """Test updating only metadata fields."""
    original_blob_ref = sample_image_artifact.blob_ref
    sqlmodel_image_artifact_repo.add(sample_image_artifact)
    session.commit()
    
    sample_image_artifact.metadata = ImageMetadata(
        mime_type=ImageMimeType("image/jpeg"),
        width=ImageWidth(1024),
        height=ImageHeight(768),
    )
    
    updated = sqlmodel_image_artifact_repo.update(sample_image_artifact)
    session.commit()
    
    assert updated.blob_ref == original_blob_ref
    assert updated.metadata.mime_type.value == "image/jpeg"


# Tests for delete method

def test_delete_existing_image_artifact(sqlmodel_image_artifact_repo, session, sample_image_artifact):
    """Test deleting an existing image artifact."""
    sqlmodel_image_artifact_repo.add(sample_image_artifact)
    session.commit()
    
    sqlmodel_image_artifact_repo.delete(sample_image_artifact.id)
    session.commit()
    
    retrieved = sqlmodel_image_artifact_repo.get_by_id(sample_image_artifact.id)
    assert retrieved is None


def test_delete_nonexistent_image_artifact_does_nothing(sqlmodel_image_artifact_repo, session):
    """Test that deleting a nonexistent image artifact doesn't raise an error."""
    nonexistent_id = ImageArtifactID.next_id()
    
    # Should not raise an error
    sqlmodel_image_artifact_repo.delete(nonexistent_id)
    session.commit()


def test_delete_doesnt_affect_other_artifacts(sqlmodel_image_artifact_repo, session):
    """Test that deleting one artifact doesn't affect others."""
    artifact1 = ImageArtifact(
        id=ImageArtifactID.next_id(),
        blob_ref=ImageURI("s3://bucket/image1.png"),
        metadata=ImageMetadata(
            mime_type=ImageMimeType("image/png"),
            width=ImageWidth(800),
            height=ImageHeight(600),
        ),
    )
    artifact2 = ImageArtifact(
        id=ImageArtifactID.next_id(),
        blob_ref=ImageURI("s3://bucket/image2.jpg"),
        metadata=ImageMetadata(
            mime_type=ImageMimeType("image/jpeg"),
            width=ImageWidth(1024),
            height=ImageHeight(768),
        ),
    )
    
    sqlmodel_image_artifact_repo.add(artifact1)
    sqlmodel_image_artifact_repo.add(artifact2)
    session.commit()
    
    sqlmodel_image_artifact_repo.delete(artifact1.id)
    session.commit()
    
    retrieved1 = sqlmodel_image_artifact_repo.get_by_id(artifact1.id)
    retrieved2 = sqlmodel_image_artifact_repo.get_by_id(artifact2.id)
    
    assert retrieved1 is None
    assert retrieved2 is not None


def test_delete_and_list_all(sqlmodel_image_artifact_repo, session):
    """Test that deleted artifact is not in list_all results."""
    artifacts = [
        ImageArtifact(
            id=ImageArtifactID.next_id(),
            blob_ref=ImageURI(f"s3://bucket/image{i}.png"),
            metadata=ImageMetadata(
                mime_type=ImageMimeType("image/png"),
                width=ImageWidth(800),
                height=ImageHeight(600),
            ),
        )
        for i in range(3)
    ]
    
    for artifact in artifacts:
        sqlmodel_image_artifact_repo.add(artifact)
    session.commit()
    
    sqlmodel_image_artifact_repo.delete(artifacts[1].id)
    session.commit()
    
    all_artifacts = sqlmodel_image_artifact_repo.list_all()
    assert len(all_artifacts) == 2
    
    ids = {str(a.id) for a in all_artifacts}
    assert str(artifacts[1].id) not in ids


# Tests for flush method

def test_flush_persists_changes(sqlmodel_image_artifact_repo, session, sample_image_artifact):
    """Test that flush persists changes without commit."""
    sqlmodel_image_artifact_repo.add(sample_image_artifact)
    sqlmodel_image_artifact_repo.flush()
    
    # Changes should be visible in the same session
    retrieved = sqlmodel_image_artifact_repo.get_by_id(sample_image_artifact.id)
    assert retrieved is not None


def test_flush_without_commit_rollback(sqlmodel_image_artifact_repo, session, sample_image_artifact):
    """Test that flush without commit can be rolled back."""
    sqlmodel_image_artifact_repo.add(sample_image_artifact)
    sqlmodel_image_artifact_repo.flush()
    
    session.rollback()
    
    retrieved = sqlmodel_image_artifact_repo.get_by_id(sample_image_artifact.id)
    assert retrieved is None


def test_flush_multiple_operations(sqlmodel_image_artifact_repo, session):
    """Test flushing multiple operations."""
    artifact1 = ImageArtifact(
        id=ImageArtifactID.next_id(),
        blob_ref=ImageURI("s3://bucket/image1.png"),
        metadata=ImageMetadata(
            mime_type=ImageMimeType("image/png"),
            width=ImageWidth(800),
            height=ImageHeight(600),
        ),
    )
    artifact2 = ImageArtifact(
        id=ImageArtifactID.next_id(),
        blob_ref=ImageURI("s3://bucket/image2.jpg"),
        metadata=ImageMetadata(
            mime_type=ImageMimeType("image/jpeg"),
            width=ImageWidth(1024),
            height=ImageHeight(768),
        ),
    )
    
    sqlmodel_image_artifact_repo.add(artifact1)
    sqlmodel_image_artifact_repo.add(artifact2)
    sqlmodel_image_artifact_repo.flush()
    
    # Both should be queryable
    all_artifacts = sqlmodel_image_artifact_repo.list_all()
    assert len(all_artifacts) == 2


# Integration tests

def test_full_crud_cycle(sqlmodel_image_artifact_repo, session):
    """Test a complete CRUD cycle."""
    # Create
    artifact = ImageArtifact(
        id=ImageArtifactID.next_id(),
        blob_ref=ImageURI("s3://bucket/test_image.png"),
        metadata=ImageMetadata(
            mime_type=ImageMimeType("image/png"),
            width=ImageWidth(800),
            height=ImageHeight(600),
        ),
    )
    sqlmodel_image_artifact_repo.add(artifact)
    session.commit()
    
    # Read
    retrieved = sqlmodel_image_artifact_repo.get_by_id(artifact.id)
    assert retrieved is not None
    assert retrieved.metadata.mime_type.value == "image/png"
    
    # Update
    artifact.metadata = ImageMetadata(
        mime_type=ImageMimeType("image/jpeg"),
        width=ImageWidth(1024),
        height=ImageHeight(768),
    )
    sqlmodel_image_artifact_repo.update(artifact)
    session.commit()
    
    updated = sqlmodel_image_artifact_repo.get_by_id(artifact.id)
    assert updated.metadata.mime_type.value == "image/jpeg"
    
    # Delete
    sqlmodel_image_artifact_repo.delete(artifact.id)
    session.commit()
    
    deleted = sqlmodel_image_artifact_repo.get_by_id(artifact.id)
    assert deleted is None


def test_repository_isolation(sqlmodel_image_artifact_repo, session):
    """Test that repository operations are properly isolated."""
    artifact = ImageArtifact(
        id=ImageArtifactID.next_id(),
        blob_ref=ImageURI("s3://bucket/image.png"),
        metadata=ImageMetadata(
            mime_type=ImageMimeType("image/png"),
            width=ImageWidth(800),
            height=ImageHeight(600),
        ),
    )
    
    sqlmodel_image_artifact_repo.add(artifact)
    # Don't commit
    
    # Should be visible in same session
    retrieved = sqlmodel_image_artifact_repo.get_by_id(artifact.id)
    assert retrieved is not None
    
    # Rollback
    session.rollback()
    
    # Should not be visible after rollback
    retrieved_after = sqlmodel_image_artifact_repo.get_by_id(artifact.id)
    assert retrieved_after is None


def test_different_mime_types_persistence(sqlmodel_image_artifact_repo, session):
    """Test that different mime types are correctly persisted and retrieved."""
    mime_types = ["image/png", "image/jpeg", "image/webp"]
    
    for i, mime_type in enumerate(mime_types):
        artifact = ImageArtifact(
            id=ImageArtifactID.next_id(),
            blob_ref=ImageURI(f"s3://bucket/image{i}.{mime_type.split('/')[1]}"),
            metadata=ImageMetadata(
                mime_type=ImageMimeType(mime_type),
                width=ImageWidth(800),
                height=ImageHeight(600),
            ),
        )
        sqlmodel_image_artifact_repo.add(artifact)
    
    session.commit()
    
    all_artifacts = sqlmodel_image_artifact_repo.list_all()
    retrieved_mime_types = {a.metadata.mime_type.value for a in all_artifacts}
    
    assert len(all_artifacts) == 3
    assert retrieved_mime_types == set(mime_types)


def test_large_dimensions_persistence(sqlmodel_image_artifact_repo, session):
    """Test that large width and height values are correctly persisted."""
    artifact = ImageArtifact(
        id=ImageArtifactID.next_id(),
        blob_ref=ImageURI("s3://bucket/large_image.png"),
        metadata=ImageMetadata(
            mime_type=ImageMimeType("image/png"),
            width=ImageWidth(2500),
            height=ImageHeight(2500),
        ),
    )
    
    sqlmodel_image_artifact_repo.add(artifact)
    session.commit()
    
    retrieved = sqlmodel_image_artifact_repo.get_by_id(artifact.id)
    
    assert retrieved.metadata.width.value == 2500
    assert retrieved.metadata.height.value== 2500