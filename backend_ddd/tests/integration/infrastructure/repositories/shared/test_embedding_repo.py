import pytest
from datetime import datetime, timezone
from src.domain.shared.value_objects import EmbeddingData, EmbeddingId
from src.domain.shared.entities import Embedding
from src.domain.shared.specifications import FieldSpecification, AndSpecification, OrSpecification


# Tests for add method

def test_add_embedding_successfully(sqlmodel_embedding_repo, session, sample_embedding):
    """Test that adding an embedding saves it to the database."""
    sqlmodel_embedding_repo.add(sample_embedding)
    session.commit()
    
    retrieved = sqlmodel_embedding_repo.get_by_id(sample_embedding.id)
    
    assert retrieved is not None
    assert retrieved.id == sample_embedding.id
    assert retrieved.embedding.model_name == sample_embedding.embedding.model_name
    assert retrieved.embedding.vector == sample_embedding.embedding.vector


def test_add_multiple_embeddings(sqlmodel_embedding_repo, session):
    """Test that multiple embeddings can be added."""
    embedding1 = Embedding(
        id=EmbeddingId.next_id(),
        created_at=datetime.now(timezone.utc),
        embedding=EmbeddingData(model_name="model1", vector=[0.1, 0.2]),
    )
    embedding2 = Embedding(
        id=EmbeddingId.next_id(),
        created_at=datetime.now(timezone.utc),
        embedding=EmbeddingData(model_name="model2", vector=[0.3, 0.4]),
    )
    
    sqlmodel_embedding_repo.add(embedding1)
    sqlmodel_embedding_repo.add(embedding2)
    session.commit()
    
    all_embeddings = sqlmodel_embedding_repo.list_all()
    
    assert len(all_embeddings) == 2


def test_add_embedding_without_commit_not_persisted(sqlmodel_embedding_repo, session, sample_embedding):
    """Test that embedding is not persisted without commit."""
    sqlmodel_embedding_repo.add(sample_embedding)
    # No commit
    session.rollback()
    
    retrieved = sqlmodel_embedding_repo.get_by_id(sample_embedding.id)
    
    assert retrieved is None


# Tests for get_by_id method

def test_get_by_id_existing_embedding(sqlmodel_embedding_repo, session, sample_embedding):
    """Test retrieving an existing embedding by ID."""
    sqlmodel_embedding_repo.add(sample_embedding)
    session.commit()
    
    retrieved = sqlmodel_embedding_repo.get_by_id(sample_embedding.id)
    
    assert retrieved is not None
    assert retrieved.id == sample_embedding.id
    assert retrieved.embedding.model_name == sample_embedding.embedding.model_name


def test_get_by_id_nonexistent_embedding(sqlmodel_embedding_repo):
    """Test that getting a nonexistent embedding returns None."""
    nonexistent_id = EmbeddingId.next_id()
    
    retrieved = sqlmodel_embedding_repo.get_by_id(nonexistent_id)
    
    assert retrieved is None


def test_get_by_id_returns_correct_embedding(sqlmodel_embedding_repo, session):
    """Test that get_by_id returns the correct embedding when multiple exist."""
    embedding1 = Embedding(
        id=EmbeddingId.next_id(),
        created_at=datetime.now(timezone.utc),
        embedding=EmbeddingData(model_name="model1", vector=[0.1, 0.2]),
    )
    embedding2 = Embedding(
        id=EmbeddingId.next_id(),
        created_at=datetime.now(timezone.utc),
        embedding=EmbeddingData(model_name="model2", vector=[0.3, 0.4]),
    )
    
    sqlmodel_embedding_repo.add(embedding1)
    sqlmodel_embedding_repo.add(embedding2)
    session.commit()
    
    retrieved = sqlmodel_embedding_repo.get_by_id(embedding1.id)
    
    assert retrieved is not None
    assert retrieved.id == embedding1.id
    assert retrieved.embedding.model_name == "model1"


# Tests for list_all method

def test_list_all_empty_repository(sqlmodel_embedding_repo):
    """Test that list_all returns empty list when no embeddings exist."""
    result = sqlmodel_embedding_repo.list_all()
    
    assert result == []


def test_list_all_single_embedding(sqlmodel_embedding_repo, session, sample_embedding):
    """Test that list_all returns single embedding."""
    sqlmodel_embedding_repo.add(sample_embedding)
    session.commit()
    
    result = sqlmodel_embedding_repo.list_all()
    
    assert len(result) == 1
    assert result[0].id == sample_embedding.id


def test_list_all_multiple_embeddings(sqlmodel_embedding_repo, session):
    """Test that list_all returns all embeddings."""
    embeddings = [
        Embedding(
            id=EmbeddingId.next_id(),
            created_at=datetime.now(timezone.utc),
            embedding=EmbeddingData(model_name=f"model{i}", vector=[float(i)]),
        )
        for i in range(5)
    ]
    
    for embedding in embeddings:
        sqlmodel_embedding_repo.add(embedding)
    session.commit()
    
    result = sqlmodel_embedding_repo.list_all()
    
    assert len(result) == 5
    result_ids = {str(e.id) for e in result}
    expected_ids = {str(e.id) for e in embeddings}
    assert result_ids == expected_ids


# Tests for find_by_specification method

def test_find_by_specification_with_none_spec(sqlmodel_embedding_repo, session):
    """Test that None specification returns all embeddings."""
    embeddings = [
        Embedding(
            id=EmbeddingId.next_id(),
            created_at=datetime.now(timezone.utc),
            embedding=EmbeddingData(model_name=f"model{i}", vector=[float(i)]),
        )
        for i in range(3)
    ]
    
    for embedding in embeddings:
        sqlmodel_embedding_repo.add(embedding)
    session.commit()
    
    result = sqlmodel_embedding_repo.find_by_specification(None)
    
    assert len(result) == 3


def test_find_by_specification_with_eq_operator(sqlmodel_embedding_repo, session):
    """Test finding embeddings with equality specification."""
    embedding1 = Embedding(
        id=EmbeddingId.next_id(),
        created_at=datetime.now(timezone.utc),
        embedding=EmbeddingData(model_name="vit", vector=[0.1, 0.2]),
    )
    embedding2 = Embedding(
        id=EmbeddingId.next_id(),
        created_at=datetime.now(timezone.utc),
        embedding=EmbeddingData(model_name="resnet", vector=[0.3, 0.4]),
    )
    
    sqlmodel_embedding_repo.add(embedding1)
    sqlmodel_embedding_repo.add(embedding2)
    session.commit()
    
    spec = FieldSpecification("model_name", "eq", "vit")
    result = sqlmodel_embedding_repo.find_by_specification(spec)
    
    assert len(result) == 1
    assert result[0].embedding.model_name == "vit"


def test_find_by_specification_with_gt_operator(sqlmodel_embedding_repo, session):
    """Test finding embeddings with greater than specification."""
    base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    future_time = datetime(2024, 6, 1, tzinfo=timezone.utc)
    
    embedding1 = Embedding(
        id=EmbeddingId.next_id(),
        created_at=base_time,
        embedding=EmbeddingData(model_name="model1", vector=[0.1]),
    )
    embedding2 = Embedding(
        id=EmbeddingId.next_id(),
        created_at=future_time,
        embedding=EmbeddingData(model_name="model2", vector=[0.2]),
    )
    
    sqlmodel_embedding_repo.add(embedding1)
    sqlmodel_embedding_repo.add(embedding2)
    session.commit()
    
    spec = FieldSpecification("created_at", "gt", base_time)
    result = sqlmodel_embedding_repo.find_by_specification(spec)
    
    assert len(result) == 1
    # Compare without timezone or use replace to strip timezone
    assert result[0].created_at.replace(tzinfo=timezone.utc) == future_time


def test_find_by_specification_with_lt_operator(sqlmodel_embedding_repo, session):
    """Test finding embeddings with less than specification."""
    base_time = datetime(2024, 6, 1, tzinfo=timezone.utc)
    past_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    
    embedding1 = Embedding(
        id=EmbeddingId.next_id(),
        created_at=past_time,
        embedding=EmbeddingData(model_name="model1", vector=[0.1]),
    )
    embedding2 = Embedding(
        id=EmbeddingId.next_id(),
        created_at=base_time,
        embedding=EmbeddingData(model_name="model2", vector=[0.2]),
    )
    
    sqlmodel_embedding_repo.add(embedding1)
    sqlmodel_embedding_repo.add(embedding2)
    session.commit()
    
    spec = FieldSpecification("created_at", "lt", base_time)
    result = sqlmodel_embedding_repo.find_by_specification(spec)
    
    assert len(result) == 1
    # Compare without timezone or use replace to strip timezone
    assert result[0].created_at.replace(tzinfo=timezone.utc) == past_time


def test_find_by_specification_with_and_specification(sqlmodel_embedding_repo, session):
    """Test finding embeddings with AND specification."""
    base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    
    embedding1 = Embedding(
        id=EmbeddingId.next_id(),
        created_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
        embedding=EmbeddingData(model_name="vit", vector=[0.1]),
    )
    embedding2 = Embedding(
        id=EmbeddingId.next_id(),
        created_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
        embedding=EmbeddingData(model_name="resnet", vector=[0.2]),
    )
    embedding3 = Embedding(
        id=EmbeddingId.next_id(),
        created_at=base_time,
        embedding=EmbeddingData(model_name="vit", vector=[0.3]),
    )
    
    sqlmodel_embedding_repo.add(embedding1)
    sqlmodel_embedding_repo.add(embedding2)
    sqlmodel_embedding_repo.add(embedding3)
    session.commit()
    
    spec1 = FieldSpecification("model_name", "eq", "vit")
    spec2 = FieldSpecification("created_at", "gt", base_time)
    and_spec = AndSpecification(spec1, spec2)
    
    result = sqlmodel_embedding_repo.find_by_specification(and_spec)
    
    assert len(result) == 1
    assert result[0].embedding.model_name == "vit"
    # Compare dates without worrying about timezone
    assert result[0].created_at.replace(tzinfo=None) > base_time.replace(tzinfo=None)


def test_find_by_specification_with_or_specification(sqlmodel_embedding_repo, session):
    """Test finding embeddings with OR specification."""
    embedding1 = Embedding(
        id=EmbeddingId.next_id(),
        created_at=datetime.now(timezone.utc),
        embedding=EmbeddingData(model_name="vit", vector=[0.1]),
    )
    embedding2 = Embedding(
        id=EmbeddingId.next_id(),
        created_at=datetime.now(timezone.utc),
        embedding=EmbeddingData(model_name="resnet", vector=[0.2]),
    )
    embedding3 = Embedding(
        id=EmbeddingId.next_id(),
        created_at=datetime.now(timezone.utc),
        embedding=EmbeddingData(model_name="bert", vector=[0.3]),
    )
    
    sqlmodel_embedding_repo.add(embedding1)
    sqlmodel_embedding_repo.add(embedding2)
    sqlmodel_embedding_repo.add(embedding3)
    session.commit()
    
    spec1 = FieldSpecification("model_name", "eq", "vit")
    spec2 = FieldSpecification("model_name", "eq", "resnet")
    or_spec = OrSpecification(spec1, spec2)
    
    result = sqlmodel_embedding_repo.find_by_specification(or_spec)
    
    assert len(result) == 2
    model_names = {e.embedding.model_name for e in result}
    assert model_names == {"vit", "resnet"}


def test_find_by_specification_no_matches(sqlmodel_embedding_repo, session, sample_embedding):
    """Test that no matches returns empty list."""
    sqlmodel_embedding_repo.add(sample_embedding)
    session.commit()
    
    spec = FieldSpecification("model_name", "eq", "nonexistent_model")
    result = sqlmodel_embedding_repo.find_by_specification(spec)
    
    assert result == []


def test_find_by_specification_complex_query(sqlmodel_embedding_repo, session):
    """Test complex specification with nested AND/OR."""
    base_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    
    embedding1 = Embedding(
        id=EmbeddingId.next_id(),
        created_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
        embedding=EmbeddingData(model_name="vit", vector=[0.1]),
    )
    embedding2 = Embedding(
        id=EmbeddingId.next_id(),
        created_at=datetime(2024, 6, 1, tzinfo=timezone.utc),
        embedding=EmbeddingData(model_name="resnet", vector=[0.2]),
    )
    embedding3 = Embedding(
        id=EmbeddingId.next_id(),
        created_at=base_time,
        embedding=EmbeddingData(model_name="vit", vector=[0.3]),
    )
    
    sqlmodel_embedding_repo.add(embedding1)
    sqlmodel_embedding_repo.add(embedding2)
    sqlmodel_embedding_repo.add(embedding3)
    session.commit()
    
    # (model_name == "vit" OR model_name == "resnet") AND created_at > base_time
    spec1 = FieldSpecification("model_name", "eq", "vit")
    spec2 = FieldSpecification("model_name", "eq", "resnet")
    or_spec = OrSpecification(spec1, spec2)
    
    spec3 = FieldSpecification("created_at", "gt", base_time)
    and_spec = AndSpecification(or_spec, spec3)
    
    result = sqlmodel_embedding_repo.find_by_specification(and_spec)
    
    assert len(result) == 2
    for embedding in result:
        assert embedding.created_at.replace(tzinfo=None) > base_time.replace(tzinfo=None)
        assert embedding.embedding.model_name in ["vit", "resnet"]


# Tests for update method

def test_update_existing_embedding(sqlmodel_embedding_repo, session, sample_embedding):
    """Test updating an existing embedding."""
    sqlmodel_embedding_repo.add(sample_embedding)
    session.commit()
    
    # Modify the embedding
    sample_embedding.embedding = EmbeddingData(
        model_name="updated_model",
        vector=[1.0, 2.0, 3.0]
    )
    
    updated = sqlmodel_embedding_repo.update(sample_embedding)
    session.commit()
    
    assert updated.embedding.model_name == "updated_model"
    assert updated.embedding.vector == [1.0, 2.0, 3.0]
    
    # Verify the update persisted
    retrieved = sqlmodel_embedding_repo.get_by_id(sample_embedding.id)
    assert retrieved.embedding.model_name == "updated_model"


def test_update_nonexistent_embedding_raises_error(sqlmodel_embedding_repo):
    """Test that updating a nonexistent embedding raises ValueError."""
    nonexistent_embedding = Embedding(
        id=EmbeddingId.next_id(),
        created_at=datetime.now(timezone.utc),
        embedding=EmbeddingData(model_name="model", vector=[0.1]),
    )
    
    with pytest.raises(ValueError, match="Embedding not found"):
        sqlmodel_embedding_repo.update(nonexistent_embedding)


def test_update_preserves_id(sqlmodel_embedding_repo, session, sample_embedding):
    """Test that update preserves the embedding ID."""
    original_id = sample_embedding.id
    sqlmodel_embedding_repo.add(sample_embedding)
    session.commit()
    
    sample_embedding.embedding = EmbeddingData(
        model_name="new_model",
        vector=[5.0]
    )
    
    updated = sqlmodel_embedding_repo.update(sample_embedding)
    session.commit()
    
    assert updated.id == original_id


def test_update_multiple_times(sqlmodel_embedding_repo, session, sample_embedding):
    """Test that an embedding can be updated multiple times."""
    sqlmodel_embedding_repo.add(sample_embedding)
    session.commit()
    
    # First update
    sample_embedding.embedding = EmbeddingData(model_name="model1", vector=[1.0])
    sqlmodel_embedding_repo.update(sample_embedding)
    session.commit()
    
    # Second update
    sample_embedding.embedding = EmbeddingData(model_name="model2", vector=[2.0])
    sqlmodel_embedding_repo.update(sample_embedding)
    session.commit()
    
    retrieved = sqlmodel_embedding_repo.get_by_id(sample_embedding.id)
    assert retrieved.embedding.model_name == "model2"
    assert retrieved.embedding.vector == [2.0]


# Tests for delete method

def test_delete_existing_embedding(sqlmodel_embedding_repo, session, sample_embedding):
    """Test deleting an existing embedding."""
    sqlmodel_embedding_repo.add(sample_embedding)
    session.commit()
    
    sqlmodel_embedding_repo.delete(sample_embedding.id)
    session.commit()
    
    retrieved = sqlmodel_embedding_repo.get_by_id(sample_embedding.id)
    assert retrieved is None


def test_delete_nonexistent_embedding_does_nothing(sqlmodel_embedding_repo, session):
    """Test that deleting a nonexistent embedding doesn't raise an error."""
    nonexistent_id = EmbeddingId.next_id()
    
    # Should not raise an error
    sqlmodel_embedding_repo.delete(nonexistent_id)
    session.commit()


def test_delete_doesnt_affect_other_embeddings(sqlmodel_embedding_repo, session):
    """Test that deleting one embedding doesn't affect others."""
    embedding1 = Embedding(
        id=EmbeddingId.next_id(),
        created_at=datetime.now(timezone.utc),
        embedding=EmbeddingData(model_name="model1", vector=[0.1]),
    )
    embedding2 = Embedding(
        id=EmbeddingId.next_id(),
        created_at=datetime.now(timezone.utc),
        embedding=EmbeddingData(model_name="model2", vector=[0.2]),
    )
    
    sqlmodel_embedding_repo.add(embedding1)
    sqlmodel_embedding_repo.add(embedding2)
    session.commit()
    
    sqlmodel_embedding_repo.delete(embedding1.id)
    session.commit()
    
    retrieved1 = sqlmodel_embedding_repo.get_by_id(embedding1.id)
    retrieved2 = sqlmodel_embedding_repo.get_by_id(embedding2.id)
    
    assert retrieved1 is None
    assert retrieved2 is not None


def test_delete_and_list_all(sqlmodel_embedding_repo, session):
    """Test that deleted embedding is not in list_all results."""
    embeddings = [
        Embedding(
            id=EmbeddingId.next_id(),
            created_at=datetime.now(timezone.utc),
            embedding=EmbeddingData(model_name=f"model{i}", vector=[float(i)]),
        )
        for i in range(3)
    ]
    
    for embedding in embeddings:
        sqlmodel_embedding_repo.add(embedding)
    session.commit()
    
    sqlmodel_embedding_repo.delete(embeddings[1].id)
    session.commit()
    
    all_embeddings = sqlmodel_embedding_repo.list_all()
    assert len(all_embeddings) == 2
    
    ids = {str(e.id) for e in all_embeddings}
    assert str(embeddings[1].id) not in ids


# Tests for flush method

def test_flush_persists_changes(sqlmodel_embedding_repo, sample_embedding):
    """Test that flush persists changes without commit."""
    sqlmodel_embedding_repo.add(sample_embedding)
    sqlmodel_embedding_repo.flush()
    
    # Changes should be visible in the same session
    retrieved = sqlmodel_embedding_repo.get_by_id(sample_embedding.id)
    assert retrieved is not None


def test_flush_without_commit_rollback(sqlmodel_embedding_repo, session, sample_embedding):
    """Test that flush without commit can be rolled back."""
    sqlmodel_embedding_repo.add(sample_embedding)
    sqlmodel_embedding_repo.flush()
    
    session.rollback()
    
    retrieved = sqlmodel_embedding_repo.get_by_id(sample_embedding.id)
    assert retrieved is None


def test_flush_multiple_operations(sqlmodel_embedding_repo, session):
    """Test flushing multiple operations."""
    embedding1 = Embedding(
        id=EmbeddingId.next_id(),
        created_at=datetime.now(timezone.utc),
        embedding=EmbeddingData(model_name="model1", vector=[0.1]),
    )
    embedding2 = Embedding(
        id=EmbeddingId.next_id(),
        created_at=datetime.now(timezone.utc),
        embedding=EmbeddingData(model_name="model2", vector=[0.2]),
    )
    
    sqlmodel_embedding_repo.add(embedding1)
    sqlmodel_embedding_repo.add(embedding2)
    sqlmodel_embedding_repo.flush()
    
    # Both should be queryable
    all_embeddings = sqlmodel_embedding_repo.list_all()
    assert len(all_embeddings) == 2


# Integration tests

def test_full_crud_cycle(sqlmodel_embedding_repo, session):
    """Test a complete CRUD cycle."""
    # Create
    embedding = Embedding(
        id=EmbeddingId.next_id(),
        created_at=datetime.now(timezone.utc),
        embedding=EmbeddingData(model_name="test_model", vector=[1.0, 2.0]),
    )
    sqlmodel_embedding_repo.add(embedding)
    session.commit()
    
    # Read
    retrieved = sqlmodel_embedding_repo.get_by_id(embedding.id)
    assert retrieved is not None
    assert retrieved.embedding.model_name == "test_model"
    
    # Update
    embedding.embedding = EmbeddingData(model_name="updated_model", vector=[3.0, 4.0])
    sqlmodel_embedding_repo.update(embedding)
    session.commit()
    
    updated = sqlmodel_embedding_repo.get_by_id(embedding.id)
    assert updated.embedding.model_name == "updated_model"
    
    # Delete
    sqlmodel_embedding_repo.delete(embedding.id)
    session.commit()
    
    deleted = sqlmodel_embedding_repo.get_by_id(embedding.id)
    assert deleted is None


def test_repository_isolation(sqlmodel_embedding_repo, session):
    """Test that repository operations are properly isolated."""
    embedding = Embedding(
        id=EmbeddingId.next_id(),
        created_at=datetime.now(timezone.utc),
        embedding=EmbeddingData(model_name="model", vector=[0.1]),
    )
    
    sqlmodel_embedding_repo.add(embedding)
    # Don't commit
    
    # Should be visible in same session
    retrieved = sqlmodel_embedding_repo.get_by_id(embedding.id)
    assert retrieved is not None
    
    # Rollback
    session.rollback()
    
    # Should not be visible after rollback
    retrieved_after = sqlmodel_embedding_repo.get_by_id(embedding.id)
    assert retrieved_after is None