\# Smart E-Commerce Platform



A backend-focused Smart E-Commerce Platform built with \*\*FastAPI\*\*, \*\*PostgreSQL\*\*, \*\*SQLAlchemy\*\*, \*\*Alembic\*\*, and \*\*Django Admin\*\*.



The application provides authentication, role-based access control, product management, product filtering, shopping cart management, order processing, payment management, and an administrative interface.



\---



\## 1. Project Overview



The Smart E-Commerce Platform allows customers to:



\* Register and log in

\* Authenticate using JWT tokens

\* Browse products

\* Filter products by category, price, popularity, and stock availability

\* Add products to a shopping cart

\* Update cart quantities

\* Remove products from the cart

\* Place orders

\* View their orders

\* Make and manage payment records



Administrators can:



\* Create products

\* Update products

\* Delete products

\* View all orders

\* Update order status

\* Manage application data through Django Admin



\---



\## 2. Tech Stack



\### Backend



\* Python 3.13

\* FastAPI

\* Uvicorn

\* Pydantic

\* SQLAlchemy

\* Alembic



\### Database



\* PostgreSQL

\* Psycopg



\### Authentication



\* JWT Authentication

\* Role-Based Access Control (RBAC)

\* Auth0 integration



\### Administration



\* Django 6.1

\* Django Admin



\### Testing / API Tools



\* Swagger UI

\* Postman



\### Version Control



\* Git

\* GitHub



\---



\## 3. Project Structure



```text

fastapi-backend/

│

├── app/

│   ├── core/

│   │   ├── config.py

│   │   └── database.py

│   │

│   ├── dependencies/

│   │   ├── auth.py

│   │   └── rbac.py

│   │

│   ├── models/

│   │   ├── user.py

│   │   ├── product.py

│   │   ├── cart.py

│   │   ├── order.py

│   │   └── payment.py

│   │

│   ├── routers/

│   │   ├── auth.py

│   │   ├── products.py

│   │   ├── cart.py

│   │   ├── orders.py

│   │   └── payment.py

│   │

│   ├── schemas/

│   │   ├── product.py

│   │   ├── cart.py

│   │   ├── order.py

│   │   └── payment.py

│   │

│   └── main.py

│

├── alembic/

│   └── versions/

│

├── admin\_panel/

│   ├── admin.py

│   ├── apps.py

│   └── models.py

│

├── django\_admin/

│   ├── settings.py

│   ├── urls.py

│   ├── asgi.py

│   └── wsgi.py

│

├── postman/

│   └── Smart E-Commerce API.postman\_collection.json

│

├── manage.py

├── alembic.ini

├── requirements.txt

├── .gitignore

└── README.md

```



\---



\## 4. Database



The project uses PostgreSQL.



Create a database named:



```text

smart\_ecommerce\_db

```



Example database URL:



```text

postgresql://postgres:<password>@localhost:5432/smart\_ecommerce\_db

```



Do not commit database credentials to GitHub.



\---



\## 5. Environment Configuration



Create a `.env` file in the project root.



Example:



```env

DATABASE\_URL=postgresql://postgres:<password>@localhost:5432/smart\_ecommerce\_db



SECRET\_KEY=<your-secret-key>

ALGORITHM=HS256



ACCESS\_TOKEN\_EXPIRE\_MINUTES=30

REFRESH\_TOKEN\_EXPIRE\_DAYS=7



AUTH0\_DOMAIN=<your-auth0-domain>

AUTH0\_CLIENT\_ID=<your-auth0-client-id>

AUTH0\_CLIENT\_SECRET=<your-auth0-client-secret>

AUTH0\_CALLBACK\_URL=http://127.0.0.1:8000/auth/auth0/callback

```



The `.env` file is excluded from Git using `.gitignore`.



\---



\## 6. Installation



Clone the repository:



```bash

git clone https://github.com/Logesh-510/smart-ecommerce.git

```



Navigate to the backend:



```bash

cd smart-ecommerce/fastapi-backend

```



Create a virtual environment:



```bash

python -m venv venv

```



Activate the virtual environment on Windows:



```powershell

.\\venv\\Scripts\\Activate.ps1

```



Install dependencies:



```bash

pip install -r requirements.txt

```



\---



\## 7. Database Migration



Run Alembic migrations:



```bash

alembic upgrade head

```



This creates and updates the required FastAPI database tables.



\---



\## 8. Run FastAPI



Start the FastAPI application:



```bash

uvicorn app.main:app --reload

```



The API will be available at:



```text

http://127.0.0.1:8000

```



Swagger API documentation:



```text

http://127.0.0.1:8000/docs

```



ReDoc:



```text

http://127.0.0.1:8000/redoc

```



\---



\## 9. Authentication



The application uses JWT-based authentication.



\### Register



```text

POST /auth/register

```



\### Login



```text

POST /auth/login

```



\### Current User



```text

GET /auth/me

```



\### Refresh Token



```text

POST /auth/refresh

```



Protected endpoints require:



```text

Authorization: Bearer <access\_token>

```



\---



\## 10. Role-Based Access Control



The application supports role-based access control.



\### Customer



Customers can:



\* Browse products

\* Manage their cart

\* Create orders

\* View their orders

\* Manage payments



\### Admin



Administrators can:



\* Create products

\* Update products

\* Delete products

\* View all orders

\* Update order status



\---



\## 11. Product APIs



\### Get all products



```text

GET /products/

```



\### Get product by ID



```text

GET /products/{product\_id}

```



\### Get products by category



```text

GET /products/category/{category}

```



\### Create product



```text

POST /products/

```



Admin authentication required.



\### Update product



```text

PUT /products/{product\_id}

```



Admin authentication required.



\### Delete product



```text

DELETE /products/{product\_id}

```



Admin authentication required.



\### Product filters



The product listing API supports:



\* Category

\* Minimum price

\* Maximum price

\* Minimum popularity

\* Stock availability



Example:



```text

GET /products/?category=electronics\&min\_price=10000\&max\_price=100000\&in\_stock=true

```



\---



\## 12. Cart APIs



Customers can manage their shopping cart.



\### Add product to cart



```text

POST /cart

```



\### View cart



```text

GET /cart

```



\### Update cart quantity



```text

PUT /cart/{product\_id}

```



\### Remove product from cart



```text

DELETE /cart/{product\_id}

```



Cart operations require customer authentication.



\---



\## 13. Order APIs



\### Create order



```text

POST /orders

```



The order is created from the customer's cart.



The system:



1\. Checks the cart

2\. Validates product availability

3\. Calculates the total amount

4\. Creates order items

5\. Reduces product stock

6\. Clears the cart



\### Get customer's orders



```text

GET /orders

```



\### Get all orders



```text

GET /orders/admin

```



Admin authentication required.



\### Update order status



```text

PUT /orders/{order\_id}/status

```



Supported statuses:



```text

pending

confirmed

shipped

delivered

cancelled

```



\---



\## 14. Payment APIs



Payment records are associated with orders.



Available endpoints include:



```text

POST /payments/

GET /payments/{payment\_id}/status

```



Payment information includes:



\* Order ID

\* Amount

\* Payment method

\* Payment status

\* Transaction ID

\* Created timestamp



\---



\## 15. Django Admin



The project includes Django Admin for administrative management.



Django Admin uses the same PostgreSQL database as the FastAPI backend.



\### Run Django



```powershell

python manage.py migrate

```



Create a Django superuser:



```powershell

python manage.py createsuperuser

```



Start Django:



```powershell

python manage.py runserver 127.0.0.1:8001

```



Open:



```text

http://127.0.0.1:8001/admin/

```



Django Admin can be used to manage application data such as:



\* Users

\* Products

\* Cart items

\* Orders

\* Order items

\* Payments



\---



\## 16. Postman Collection



A Postman collection is included in:



```text

postman/Smart E-Commerce API.postman\_collection.json

```



\### Import into Postman



1\. Open Postman.

2\. Select \*\*Import\*\*.

3\. Select the JSON file from the `postman` folder.

4\. Import the collection.

5\. Start the FastAPI server.

6\. Use the authentication endpoint to obtain an access token.

7\. Add the token to protected requests.

8\. Execute the API requests.



The collection can be used to test:



\* Authentication

\* Products

\* Product filters

\* Cart

\* Orders

\* Payments

\* Admin operations



\---



\## 17. API Testing



FastAPI provides interactive API documentation through Swagger.



Open:



```text

http://127.0.0.1:8000/docs

```



Recommended testing sequence:



1\. Register a customer.

2\. Login as the customer.

3\. Copy the access token.

4\. Authorize Swagger using the token.

5\. Browse products.

6\. Add a product to the cart.

7\. View the cart.

8\. Update the cart quantity.

9\. Create an order.

10\. View customer orders.

11\. Login as an admin.

12\. Create/update products.

13\. View all orders.

14\. Update order status.

15\. Test payment endpoints.



\---



\## 18. GitHub



Repository:



https://github.com/Logesh-510/smart-ecommerce



The repository contains:



\* FastAPI backend

\* PostgreSQL/Alembic configuration

\* Django Admin

\* Postman API collection

\* API models and schemas

\* Authentication and RBAC implementation



\---



\## 19. Security Notes



Never commit sensitive credentials.



The following files should remain local:



```text

.env

venv/

\_\_pycache\_\_/

\*.pyc

```



Use environment variables for:



\* Database credentials

\* JWT secret

\* Auth0 credentials

\* Other sensitive configuration



\---



\## 20. Project Status



The backend implementation is complete with:



\* \[x] FastAPI backend

\* \[x] PostgreSQL database

\* \[x] SQLAlchemy models

\* \[x] Alembic migrations

\* \[x] User authentication

\* \[x] JWT tokens

\* \[x] Role-based access control

\* \[x] Product APIs

\* \[x] Product filtering

\* \[x] Cart management

\* \[x] Order management

\* \[x] Payment management

\* \[x] Django Admin

\* \[x] Postman collection

\* \[x] GitHub repository



A React frontend can be integrated separately if frontend implementation is required by the assignment.



