
**Status Legend:**
*   ✅ **Done:** The core functionality is implemented.
*   ⏳ **In Progress:** Actively being worked on or is the immediate next step.
*   🔵 **To Do:** Planned but not yet started.

---

### Unified Development & MLOps Roadmap

#### Phase 1: Solidify Core Architecture & Technical Debt

*   **Goal:** Stabilize the foundation by refactoring the data model and addressing immediate technical debt.

| Priority | Step | Action | Status |
| :--- | :--- | :--- | :--- |
| **CRITICAL** | 1.1 | **Refactor to Job/Result Model:** Implement `Job`, `IndexingResult`, and `QueryResult` tables to separate process state from data artifacts. |  ✅ Done |
| **HIGH** | 1.2 | **Establish Test Suite:** Write unit tests for core CRUD operations and integration tests for auth and job submission APIs, mocking external services. | 🔵 To Do |
| **HIGH** | 1.3 | **Implement ML Service Lifespan:** Ensure models are loaded cleanly using FastAPI's `lifespan` context manager for robust resource management. | 🔵 To Do |
| **MEDIUM** | 1.4 | **Address Security Vulnerabilities:** Sanitize filenames on upload and configure stricter CORS policies for production. |  ✅ Done|
| **MEDIUM** | 1.5 | **Fix Dependency Management:** Clean up and pin all versions in `requirements.txt` to ensure reproducible builds. | 🔵 To Do |

---

#### Phase 2: Build Product Catalog & Search Intelligence

*   **Goal:** Evolve from searching raw crops to managing a structured product catalog with significantly improved AI accuracy.

| Priority | Step | Action | Status |
| :--- | :--- | :--- | :--- |
| **CRITICAL** | 2.1 | **Implement `Product` Schema:** Create the `Product` table and link `ImageDB` to it. Update the indexing API to accept product metadata. | 🔵 To Do |
| **HIGH** | 2.2 | **Implement Crop Quality Filter ("Filtering Garbage"):** Add a Celery task to discard irrelevant/bad crops *before* labeling using heuristics (size, aspect ratio). | 🔵 To Do |
| **HIGH** | 2.3 | **Implement "Primary Crop Selector" ("Providing Context"):** Create a Celery task to score crops against the product's text description and automatically flag the main item. | 🔵 To Do |
| **HIGH** | 2.4 | **Refine Vector Storage:** Update the pipeline to store only the **primary crop's** vector in ChromaDB, using the `Product.id` as the document ID. | 🔵 To Do |
| **MEDIUM** | 2.5 | **Cache Label Embeddings:** Pre-compute and cache embeddings for all label vocabularies (colors, styles) in the `ml_service` at startup. | 🔵 To Do |

---

#### Phase 3: Develop User Interfaces & Data Flywheel

*   **Goal:** Make the platform usable by end-users and create the mechanism for continuous data quality improvement.

| Priority | Step | Action | Status |
| :--- | :--- | :--- | :--- |
| **HIGH** | 3.1 | **Build Frontend Application (SPA):** Develop a user-facing interface for uploading products, performing visual searches, and viewing results. | 🔵 To Do |
| **HIGH** | 3.2 | **Build Human-in-the-Loop (HITL) Admin UI ("Feedback Loop"):** Create an internal tool for admins to review and correct AI-generated labels and primary crop selections. | 🔵 To Do |
| **MEDIUM** | 3.3 | **Enable Filtered Search:** Enhance the search API to allow filtering vector search results by metadata (e.g., category, color). | 🔵 To Do |
| **LOW** | 3.4 | **Automate Thumbnail Generation:** Add a background task to create standardized thumbnails for all uploaded images to improve frontend performance. | 🔵 To Do |

---

#### Phase 4: Production Readiness & MLOps

*   **Goal:** Prepare the system for deployment, scaling, and long-term operation with automated processes.

| Priority | Step | Action | Status |
| :--- | :--- | :--- | :--- |
add global exception handling middleware in FastAPI
| **HIGH** | 4.1 | **Implement CI/CD Pipeline:** Automate testing, Docker image builds, and pushes to a container registry using GitHub Actions. | 🔵 To Do |
| **HIGH** | 4.2 | **Infrastructure as Code (IaC) & Deployment:** Write Terraform/CloudFormation scripts to deploy the application stack to a cloud orchestrator (AWS ECS/EKS). | 🔵 To Do |
| **MEDIUM** | 4.3 | **Implement Resource Management:** Configure Docker resource limits and apply them in the cloud to ensure stability and prevent DoS attacks. | 🔵 To Do |
| **MEDIUM** | 4.4 | **Establish Observability:** Integrate Prometheus and Grafana for comprehensive monitoring of APIs, job queues, and system health. | 🔵 To Do |
| **LOW** | 4.5 | **Model Fine-Tuning Pipeline:** Use the human-verified dataset from the HITL tool to periodically fine-tune the YOLO and CLIP models. | 🔵 To Do |



Pipeline outline (index & query must use the same code):

Run detector (YOLOv8) → bbox.

Expand bbox by 10–20% (configurable margin) to include context.

Crop from source image.

Pad the crop to square using reflect padding (or mean-color fill), then resize to model size (e.g. 224).

Why reflect? it avoids injecting a new constant color that would bias CLIP. Pinterest emphasizes deterministic preprocess and domain handling — reflect/mean are safe choices. 
arXiv

Normalize using your model’s exact normalization (for FashionCLIP/CLIP use the same processor/mean/std or HF CLIPProcessor).

Compute embedding (image branch + optionally text/label branch), L2-normalize, store with model_version and preprocess_version.

At query-time: same steps → get query embedding → ANN search → top-K → re-rank by category/shape/metadata.


Needs to implement soft delete system for tables and for s3 files strategy