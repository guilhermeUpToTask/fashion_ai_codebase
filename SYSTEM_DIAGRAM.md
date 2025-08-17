graph TD
    %% User Interfaces
    subgraph UI["User Interfaces"]
        Frontend["Frontend SPA"]
        Admin["Admin Panel"]
    end

    %% API Layer
    subgraph API["API Layer"]
        BackendAPI["Backend API"]
    end

    %% Asynchronous Processing
    subgraph AsyncProc["Asynchronous Processing"]
        Redis["Redis Message Broker"]
        CeleryWorkers["Celery Workers"]
        IndexingPipeline["Indexing Pipeline"]
        SearchPipeline["Search Pipeline"]
    end

    %% AI Services
    subgraph AIServices["AI Services"]
        MLService["ML Inference Service"]
    end

    %% Data & Storage
    subgraph DataStorage["Data & Storage"]
        PostgreSQL["PostgreSQL Database"]
        ChromaDB["ChromaDB Vector Database"]
        MinIO["MinIO Object Storage"]
    end

    %% Product Indexing Workflow
    Frontend -->|"1. Submit product with image"| BackendAPI
    BackendAPI -->|"2. Create initial records"| PostgreSQL
    BackendAPI -->|"3. Queue indexing task"| Redis

    Redis -->|"4. Dequeue indexing task"| CeleryWorkers
    CeleryWorkers -->|"5. Execute indexing pipeline"| IndexingPipeline
    
    IndexingPipeline -->|"Crop and label requests"| MLService
    IndexingPipeline -->|"Store images and crops"| MinIO
    IndexingPipeline -->|"Update product records"| PostgreSQL
    IndexingPipeline -->|"Store product vectors"| ChromaDB

    %% Visual Search Workflow
    Frontend -->|"A. Submit search image"| BackendAPI
    BackendAPI -->|"B. Create search job"| PostgreSQL
    BackendAPI -->|"C. Queue search task"| Redis

    Redis -->|"D. Dequeue search task"| CeleryWorkers
    CeleryWorkers -->|"E. Execute search pipeline"| SearchPipeline

    SearchPipeline -->|"Process query image"| MLService
    SearchPipeline -->|"Store query image"| MinIO
    SearchPipeline -->|"Update search records"| PostgreSQL
    SearchPipeline -->|"Query similar vectors"| ChromaDB
    ChromaDB -->|"Return similar products"| SearchPipeline

    %% Admin Workflow
    Admin -->|"Correction request"| BackendAPI
    BackendAPI -->|"Direct update"| PostgreSQL

    %% Styling
    classDef userInterface fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef apiLayer fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef asyncProc fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef aiServices fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px
    classDef dataStorage fill:#fce4ec,stroke:#880e4f,stroke-width:2px

    class Frontend,Admin userInterface
    class BackendAPI apiLayer
    class Redis,CeleryWorkers,IndexingPipeline,SearchPipeline asyncProc
    class MLService aiServices
    class PostgreSQL,ChromaDB,MinIO dataStorage