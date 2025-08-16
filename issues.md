# needs to create cascade delete 
black basic solid jacket DELETE http://backend.docker.localhost/products/22f1f30b-ed6a-438b-a787-7a56982ee43d net::ERR_FAILED 500 (Internal Server Error)
fashion_ai_backend     |   File "/root/.local/lib/python3.12/site-packages/sqlalchemy/orm/sync.py", line 88, in clear
fashion_ai_backend     |     raise AssertionError(
fashion_ai_backend     | AssertionError: Dependency rule on column 'products.id' tried to blank-out primary key column 'product_images.product_id' on instance '<ProductImage at 0x75dbd1d10ff0>'
fashion_ai_backend     | 2025-08-15 20:59:49,790 INFO sqlalchemy.engine.Engine BEGIN (implicit)
fashion_ai_backend     | 2025-08-15 20:59:49,790 INFO sqlalchemy.engine.Engine SELECT products.sku, products.name, products.description, products.price, products.id 
fashion_ai_backend     | FROM products 
fashion_ai_backend     |  LIMIT %(param_1)s OFFSET %(param_2)s
fashion_ai_backend     | 2025-08-15 20:59:49,792 INFO sqlalchemy.engine.Engine [cached since 1543s ago] {'param_1': 100, 'param_2': 0}
fashion_ai_backend     | 2025-08-15 20:59:49,794 INFO sqlalchemy.engine.Engine ROLLBACK
fashion_ai_backend     | 2025-08-15 20:59:49,794 INFO sqlalchemy.engine.Engine BEGIN (implicit)
fashion_ai_backend     | 2025-08-15 20:59:49,795 INFO sqlalchemy.engine.Engine SELECT product_images.product_id, product_images.image_id, product_images.is_primary_crop 
fashion_ai_backend     | FROM product_images 
fashion_ai_backend     |  LIMIT %(param_1)s OFFSET %(param_2)s
fashion_ai_backend     | 2025-08-15 20:59:49,795 INFO sqlalchemy.engine.Engine [cached since 1543s ago] {'param_1': 100, 'param_2': 0}


# needs better vocabulary for it or reduce match limit
ValueError("No substantial product match found in image labels, best_match:{'index': 0, 'text': 'grey basic striped shorts', 'score': 0.6239969730377197} target:tactel shorts")
ValueError("No substantial product match found in image labels, best_match:{'index': 0, 'text': 'blue casual solid jeans', 'score': 0.6338144540786743} target:jeans shorts")
ValueError("No substantial product match found in image labels, best_match:{'index': 0, 'text': 'yellow basic solid jacket', 'score': 0.6933481097221375} target:yellow jacket")
ValueError("No substantial product match found in image labels, best_match:{'index': 0, 'text': 'black basic solid jacket', 'score': 0.6546558141708374} target:black leather jacker")

Access to XMLHttpRequest at 'http://backend.docker.localhost/products/22f1f30b-ed6a-438b-a787-7a56982ee43d' from origin 'http://localhost:5173' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.Understand this error
Suggested fix
You need to configure the server at http://backend.docker.localhost to include the Access-Control-Allow-Origin header in its responses. The value of this header should be the origin of your web page (http://localhost:5173) or * to allow requests from any origin (use * with caution in production environments) [2, 3].

The method for adding this header depends on the server technology being used. Here's an example for an Express.js server:

Refused to set unsafe header "content-length"


Edit product not working in the frotnend

the buttons on the lading page on the frontend for indexing and querying not working.

errors not showing in the errorhandling.

footer is not proper settted.

header have home and the logoname for the same thing

same thing for the upload icon and index image

index image buttom on header needs to be changed for products

when add a new product image, it does not show the image, needs to invalidate the key to download the image