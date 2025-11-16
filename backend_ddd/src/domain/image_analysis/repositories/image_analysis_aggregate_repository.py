from abc import ABC, abstractmethod
from typing import List

from src.domain.image_analysis.aggregates.image_analysis_aggregate import (
    ImageAnalysisAggregate,
)
from src.domain.image_analysis.value_objects.image_analysis_vos import ImageAnalysisID
from src.domain.shared.specifications import Specification


class ImageAnalysisRepository(ABC):
    """
    Repository for ImageAnalysisAggregate.
    
    Responsibilities:
    - Persist and retrieve complete aggregates (including all child entities)
    - Enforce aggregate boundaries (no direct access to child entities)
    - Provide querying capabilities via specifications
    
    Note: The repository must load the COMPLETE aggregate including:
    - All clothing items
    - Processing history with all steps
    - Timestamps
    - Error state
    This ensures aggregate consistency and allows the factory to reconstitute properly.
    """

    @abstractmethod
    def add(self, img_analysis: ImageAnalysisAggregate) -> None:
        """
        Persist a new aggregate to the repository.
        
        Args:
            img_analysis: The aggregate to persist
            
        Raises:
            DuplicateAggregateException: If aggregate with same ID already exists
            RepositoryException: If persistence fails
        """
        ...

    @abstractmethod
    def update(self, img_analysis: ImageAnalysisAggregate) -> None:
        """
        Update an existing aggregate in the repository.
        
        This should update:
        - Aggregate root fields (status, timestamps, error)
        - All clothing items (new items, updated items)
        - Processing history (new steps)
        
        Args:
            img_analysis: The aggregate to update
            
        Raises:
            AggregateNotFoundException: If aggregate doesn't exist
            RepositoryException: If update fails
        """
        ...

    @abstractmethod
    def get_by_id(self, img_analysis_id: ImageAnalysisID) -> ImageAnalysisAggregate | None:
        """
        Retrieve a complete aggregate by its ID.
        
        Returns the fully hydrated aggregate including:
        - All clothing items with their labels, embeddings, and cropped images
        - Complete processing history
        - All timestamps
        - Error information if present
        
        Args:
            img_analysis_id: The ID of the aggregate to retrieve
            
        Returns:
            The complete aggregate if found, None otherwise
            
        Raises:
            RepositoryException: If retrieval fails
        """
        ...

    @abstractmethod
    def find_by_specification(
        self, spec: Specification | None = None
    ) -> List[ImageAnalysisAggregate]:
        """
        Find aggregates matching the given specification.
        
        Examples of specifications:
        - By status (all FAILED aggregates)
        - By date range (created in last 24 hours)
        - By source image ID
        - Combined specifications (FAILED in last hour)
        
        Args:
            spec: The specification to match, or None to return all
            
        Returns:
            List of complete aggregates matching the specification
            
        Raises:
            RepositoryException: If query fails
        """
        ...

    @abstractmethod
    def exists(self, img_analysis_id: ImageAnalysisID) -> bool:
        """
        Check if an aggregate exists without loading it.
        
        Useful for validation before operations.
        
        Args:
            img_analysis_id: The ID to check
            
        Returns:
            True if aggregate exists, False otherwise
        """
        ...

    @abstractmethod
    def delete(self, img_analysis_id: ImageAnalysisID) -> bool:
        """
        Permanently delete an aggregate and all its child entities.
        
        This is a hard delete - use with caution.
        Should cascade to:
        - All clothing items
        - All processing steps
        
        Args:
            img_analysis_id: The ID of the aggregate to delete
            
        Returns:
            True if aggregate was deleted, False if not found
            
        Raises:
            RepositoryException: If deletion fails
        """
        ...

    @abstractmethod
    def soft_delete(self, img_analysis_id: ImageAnalysisID) -> bool:
        """
        Soft delete an aggregate (mark as deleted without removing data).
        
        Implementation should set a deleted_at timestamp or is_deleted flag.
        Soft-deleted aggregates should not appear in normal queries.
        
        Args:
            img_analysis_id: The ID of the aggregate to soft delete
            
        Returns:
            True if aggregate was soft deleted, False if not found
            
        Raises:
            RepositoryException: If soft deletion fails
        """
        ...

    @abstractmethod
    def count(self, spec: Specification | None = None) -> int:
        """
        Count aggregates matching the specification.
        
        Useful for pagination and statistics without loading full aggregates.
        
        Args:
            spec: The specification to match, or None to count all
            
        Returns:
            Number of aggregates matching the specification
        """
        ...


