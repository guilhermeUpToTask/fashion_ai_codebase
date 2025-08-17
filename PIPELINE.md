# Refined Pipeline Architecture

## Core Principle
A single, shared pipeline performs all expensive AI work (crop, label, vectorize). Specialized "finisher" tasks then consume the results of this pipeline to apply context-specific business logic (link to product, query ChromaDB). State management is handled through the Job table, with proper error handling and data lifecycle considerations.

## Data Models

* **Image**: Central repository for all image files and their crop hierarchies (original_id). Stores AI-generated labels and created_at timestamps for lifecycle management. Context-agnostic.
* **Product**: The catalog item.
* **ProductImage**: Link table with unique constraint on (product_id, image_id). Contains is_primary_crop flag. Links products to their selected crop images.
* **Job**: Tracks pipeline execution state, progress, and error conditions for both indexing and querying workflows.
* **Result tables**: For final outcomes and analytics data.

## The Unified AI Pipeline (Shared by Indexing and Querying)

This chain processes one original image and fans out to process its crops, with state tracked in the Job table.

**Input:** original_image_id, job_id

1. **crop_task**
   * **Action:** Takes original_image_id. Creates Image records for all detected crops with created_at timestamps.
   * **State Management:** Updates Job table with crop detection progress and count.
   * **Output:** Triggers parallel group of label_task instances, one for each crop_image_id.
   * **Error Handling:** Proceeds with available crops if some crop detection fails.

2. **label_task (Runs in parallel for each crop)**
   * **Action:** Takes crop_image_id. Calls ml_service for StructuredLabel and storage_vector. Updates Image record.
   * **State Management:** Job table tracks individual crop processing completion.
   * **Output:** Dictionary containing {image_id, label, vector}.
   * **Error Handling:** Failed crops are logged; pipeline continues with successful crops.

**Pipeline Result:** List of {image_id, label, vector} dictionaries for all successfully processed crops.

## Specialized Workflows

### A. The Indexing Workflow

**Input:** job_id, product_id, product_name

1. **Run the Unified AI Pipeline** on the product's original image.

2. **select_and_save_primary_crop_task (The Finisher Task)**
   * **Input:** List of {image_id, label, vector} dictionaries, product_id, product_name.
   * **Selection Logic:** 
     - Finds crop with highest relevance score (label vs product_name comparison)
     - Deterministic tiebreaker for identical scores (e.g., largest crop area)
   * **Transactional Actions:**
     1. **Link Creation:** Creates ProductImage record (product_id, winning_image_id, is_primary_crop=True)
     2. **Vector Storage:** Saves vector to ChromaDB using ProductImage.id as document ID
     3. **Cleanup:** Removes old ChromaDB vectors for previous ProductImage records of this product
   * **Error Handling:** Rollback mechanism for partial failures.

3. **finalize_indexing_job_task:** Creates IndexingResult record and updates Job status.

### B. The Query Workflow  

**Input:** job_id, query_image_id

1. **Run the Unified AI Pipeline** on the query image.

2. **query_all_crops_task (The Finisher Task)**
   * **Input:** List of {image_id, label, vector} dictionaries from pipeline.
   * **Search Logic:**
     - Iterates through each crop's vector
     - Performs similarity search against ChromaDB
     - Aggregates and ranks all results across crops
   * **Output:** Final ranked list of matching products with relevance scores.

3. **finalize_querying_job_task:** Creates QueryResult records and updates Job status.

## Error Handling & Recovery

- **Partial Crop Failures:** Pipeline continues with successfully processed crops
- **ML Service Failures:** Retry logic with exponential backoff
- **Database Failures:** Transaction rollback for finisher tasks
- **Job State Tracking:** Detailed progress and error logging in Job table

## Data Lifecycle Management

### Query Image Retention
- **Analytics Period:** Query images retained for 12 months for analytics and model improvement
- **Cleanup Process:** Automated monthly cleanup job removes images older than retention period
- **Analytics Extraction:** Key metrics extracted immediately after query processing for long-term storage

### ChromaDB Maintenance
- **Re-indexing Cleanup:** Automated removal of orphaned vectors when ProductImage links are updated
- **Consistency Checks:** Periodic validation between ChromaDB entries and ProductImage records

## Resource Management

- **Concurrency Limits:** Configurable limits on parallel crop processing to prevent ML service overload
- **Rate Limiting:** Built-in throttling for external ML service calls
- **Monitoring:** Job table provides visibility into pipeline performance and bottlenecks

## Key Design Benefits

1. **Robust Error Handling:** Graceful degradation with partial crop processing
2. **Data Consistency:** Unique constraints prevent duplicate links; transactional finisher tasks
3. **Analytics-Friendly:** Proper retention policies support model improvement and business intelligence
4. **Scalable:** Resource management prevents system overload
5. **Maintainable:** Clear separation between shared AI processing and business-specific logic
6. **Debuggable:** Comprehensive state tracking through Job table