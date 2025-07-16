from celery import Celery

celery_app = Celery(
    main="app", broker="amqp://", backend="rpc://", include=["app.workers.tasks"]
)

if __name__ == "__main__":
    celery_app.start()
