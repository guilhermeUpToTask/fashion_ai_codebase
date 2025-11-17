from datetime import datetime, timezone
import pytest
from sqlalchemy import StaticPool, create_engine
from sqlmodel import SQLModel, Session

from src.infrastructure.repositories.image_analysis.aggregate_repository import SQLModelImageAnalysisRepository
from src.domain.shared.value_objects import (
    EmbeddingData,
    EmbeddingId,
    ImageArtifactID,
    ImageURI,
    ImageMetadata,
    ImageMimeType,
    ImageWidth,
    ImageHeight,
)
from src.domain.shared.entities import Embedding, ImageArtifact
from src.infrastructure.repositories.shared.repos import (
    SQLModelEmbeddingRepository,
    SQLModelImageArtifactRepository,
)


@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # 👈 This is the key
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session


@pytest.fixture
def sqlmodel_embedding_repo(session):
    return SQLModelEmbeddingRepository(session)


@pytest.fixture
def sqlmodel_image_artifact_repo(session):
    return SQLModelImageArtifactRepository(session)


@pytest.fixture
def sqlmodel_image_analysis_repo(session):
    return SQLModelImageAnalysisRepository(session)

@pytest.fixture
def sample_embedding():
    return Embedding(
        id=EmbeddingId.next_id(),
        created_at=datetime.now(timezone.utc),
        embedding=EmbeddingData(model_name="vit", vector=[0.1, 0.2, 0.3, 0.4]),
    )


@pytest.fixture
def sample_image_artifact():

    return ImageArtifact(
        id=ImageArtifactID.next_id(),
        blob_ref=ImageURI("s3://bucket/image.png"),
        metadata=ImageMetadata(
            mime_type=ImageMimeType("image/png"),
            width=ImageWidth(800),
            height=ImageHeight(600),
        ),
    )
