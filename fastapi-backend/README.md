# Smart E-Commerce Platform
A backend-focused Smart E-Commerce Platform built with **FastAPI**, **PostgreSQL**, **SQLAlchemy**, **Alembic**, **Stripe**, and **Django Admin**.
The application provides authentication, role-based access control, product management, product filtering, shopping cart management, order processing, payment management, notifications, analytics, reporting, and an administrative interface.
---
## 1. Project Overview
The Smart E-Commerce Platform allows customers to:
* Register and log in
* Authenticate using JWT tokens
* Browse products
* Filter products by category, price, popularity, and stock availability
* Add products to a shopping cart
* Update cart quantities
* Remove products from the cart
* Place orders
* View their orders
* Manage payment records
* Receive notifications
* Receive real-time notifications through WebSockets
Administrators can:
* Create products
* Update products
* Delete products
* View all orders
* Update order status
* Manage users through Django Admin
* Manage products through Django Admin
* Manage orders and payment information
* View analytics and reports
* Export orders, sales, and user reports
---
## 2. Tech Stack
### Backend
* Python 3.13
* FastAPI
* Uvicorn
* Pydantic
* SQLAlchemy
* Alembic
### Database
* PostgreSQL
* Psycopg
### Authentication
* JWT Authentication
* Role-Based Access Control (RBAC)
* Auth0 integration
### Payments
* Stripe Checkout
* Stripe Webhooks
* Stripe CLI
### Notifications
* Email Notifications
* WebSocket Real-Time Notifications
### Administration
* Django 6.1
* Django Admin
* Chart.js
### Testing / API Tools
* Swagger UI
* ReDoc
* Postman
### Version Control
* Git
* GitHub
---
## 3. Project Structure
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
│   │   ├── payment.py
│   │   └── notifications.py
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
├── admin_panel/
│   ├── admin.py
│   ├── apps.py
│   └── models.py
│
├── django_admin/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── postman/
│   └── Smart E-Commerce API.postman_collection.json
│
├── manage.py
├── alembic.ini
├── requirements.txt
├── .gitignore
└── README.md
```
> The exact project structure may contain additional migration, test, static, template, and configuration files.
---
## 4. Database
The project uses PostgreSQL.
Create a database named:
```text
smart_ecommerce_db
```
Example database URL:
```text
postgresql://postgres:<password>@localhost:5432/smart_ecommerce_db
```
Do not commit database credentials to GitHub.
---
## 5. Environment Configuration
Create a `.env` file in the project root.
Example:
```env
DATABASE_URL=postgresql://postgres:<password>@localhost:5432/smart_ecommerce_db
SECRET_KEY=<your-secret-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
AUTH0_DOMAIN=<your-auth0-domain>
AUTH0_CLIENT_ID=<your-auth0-client-id>
AUTH0_CLIENT_SECRET=<your-auth0-client-secret>
AUTH0_CALLBACK_URL=http://127.0.0.1:8000/auth/auth0/callback
STRIPE_SECRET_KEY=<your-stripe-secret-key>
STRIPE_WEBHOOK_SECRET=<your-stripe-webhook-secret>
```
The `.env` file is excluded from Git using `.gitignore`.
Never commit:
* Database passwords
* JWT secrets
* Auth0 credentials
* Stripe secret keys
* Stripe webhook secrets
---
## 6. Installation
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
.\venv\Scripts\Activate.ps1
```
Install dependencies:
```bash
pip install -r requirements.txt
```
---
## 7. Database Migration
Run Alembic migrations:
```bash
alembic upgrade head
```
This creates and updates the required FastAPI database tables.
---
## 8. Run FastAPI
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
---
## 9. Authentication
The application uses JWT-based authentication.
### Register
```text
POST /auth/register
```
### Login
```text
POST /auth/login
```
### Current User
```text
GET /auth/me
```
### Refresh Token
```text
POST /auth/refresh
```
### Auth0 Login
```text
GET /auth/auth0/login
```
### Auth0 Callback
```text
GET /auth/auth0/callback
```
Protected endpoints require:
```text
Authorization: Bearer <access_token>
```
---
## 10. Role-Based Access Control
The application supports role-based access control.
### Customer
Customers can:
* Browse products
* Manage their cart
* Create orders
* View their orders
* Manage payment records
* View notifications
### Staff
Staff users can access staff-authorized functionality where configured.
### Admin
Administrators can:
* Create products
* Update products
* Delete products
* View all orders
* Update order status
* Manage users
* Manage products
* Manage orders
* View analytics
* Export reports
---
## 11. Product APIs
### Get all products
```text
GET /products/
```
### Get product by ID
```text
GET /products/{product_id}
```
### Get products by category
```text
GET /products/category/{category}
```
### Create product
```text
POST /products/
```
Admin authentication required.
### Update product
```text
PUT /products/{product_id}
```
Admin authentication required.
### Delete product
```text
DELETE /products/{product_id}
```
Admin authentication required.
### Product Filters
The product listing API supports:
* Category
* Minimum price
* Maximum price
* Minimum popularity
* Stock availability
Example:
```text
GET /products/?category=electronics&min_price=10000&max_price=100000&in_stock=true
```
---
## 12. Cart APIs
Customers can manage their shopping cart.
### Add product to cart
```text
POST /cart
```
### View cart
```text
GET /cart
```
### Update cart quantity
```text
PUT /cart/{product_id}
```
### Remove product from cart
```text
DELETE /cart/{product_id}
```
Cart operations require customer authentication.
---
## 13. Order APIs
### Create order
```text
POST /orders
```
The order is created from the customer's cart.
The system:
1. Checks the cart
2. Validates product availability
3. Calculates the total amount
4. Creates order items
5. Reduces product stock
6. Clears the cart
### Get customer's orders
```text
GET /orders
```
### Get order by ID
```text
GET /orders/{order_id}
```
### Get all orders
```text
GET /orders/admin
```
Admin authentication required.
### Update order status
```text
PUT /orders/{order_id}/status
```
Supported statuses:
```text
pending
confirmed
shipped
delivered
cancelled
```
---
## 14. Payment APIs
Payment records are associated with orders.
### Get payments
```text
GET /payments/
```
### Create payment
```text
POST /payments/
```
### Update payment status
```text
PUT /payments/{payment_id}/status
```
### Create Stripe Checkout Session
```text
POST /payments/checkout
```
### Payment Success
```text
GET /payments/success
```
### Payment Cancel
```text
GET /payments/cancel
```
### Stripe Webhook
```text
POST /payments/webhook
```
Payment information includes:
* Order ID
* Amount
* Payment method
* Payment status
* Transaction ID
* Created timestamp
---
## 15. Stripe Payment Integration
The platform integrates Stripe Checkout for online payments.
The payment flow is:
1. Customer creates an order.
2. Customer starts the Stripe Checkout process.
3. FastAPI creates a Stripe Checkout Session.
4. Customer completes or cancels payment on Stripe.
5. Stripe sends a webhook event to the FastAPI application.
6. The webhook verifies the Stripe signature.
7. The order payment status is updated.
8. The payment record is updated.
9. Notifications can be generated based on the payment result.
### Stripe CLI
For local webhook testing, Stripe CLI can forward events to:
```text
http://127.0.0.1:8000/payments/webhook
```
Example:
```bash
stripe listen --forward-to http://127.0.0.1:8000/payments/webhook
```
The webhook secret should be stored in the `.env` file and never committed to GitHub.
---
## 16. Notification System
The application provides notification functionality for important user and order events.
### Notification API
Get notifications:
```text
GET /notifications
```
Mark a notification as read:
```text
PATCH /notifications/{notification_id}/read
```
The notification system supports events such as:
* Order confirmation
* Order status updates
* Payment success
* Payment failure
### Email Notifications
Email notifications are integrated for supported application events.
### Real-Time Notifications
WebSockets are used to provide real-time notification updates.
---
## 17. Analytics Dashboard and Reports
The project includes a Django-based analytics dashboard.
Dashboard URL:
```text
http://127.0.0.1:8001/dashboard/
```
The analytics dashboard includes:
* Total users
* Total products
* Total orders
* Total revenue
* Revenue trends
* Order status distribution
* Payment status distribution
* Top-selling products
* Low-stock product alerts
* Recent orders
Charts are implemented using **Chart.js**.
### Export Reports
The dashboard supports CSV and PDF exports for:
* Orders report
* Sales report
* Users report
Available report endpoints:
```text
/dashboard/reports/orders/csv/
/dashboard/reports/orders/pdf/
/dashboard/reports/sales/csv/
/dashboard/reports/sales/pdf/
/dashboard/reports/users/csv/
/dashboard/reports/users/pdf/
```
Reports can be accessed from the Django analytics dashboard.
---
## 18. Django Admin
The project includes Django Admin for administrative management.
Django Admin uses the same PostgreSQL database as the FastAPI backend.
### Run Django
Apply Django migrations:
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
Open Django Admin:
```text
http://127.0.0.1:8001/admin/
```
Open the analytics dashboard:
```text
http://127.0.0.1:8001/dashboard/
```
### User Management
Django Admin supports:
* View users
* Add users
* Edit users
* Search users
* Filter users by role
* Filter users by active status
* Manage user roles
### Product Management
Django Admin supports:
* Add products
* Edit products
* Delete products
* Update product prices
* Update product stock
* Manage product categories
* Manage product images
* Manage product popularity
### Order Management
Django Admin supports:
* View all orders
* Search orders
* Filter orders by status
* Filter orders by payment status
* Update order status
* Track payment status
---
## 19. Postman Collection
A Postman collection is included in:
```text
postman/Smart E-Commerce API.postman_collection.json
```
### Import into Postman
1. Open Postman.
2. Select **Import**.
3. Select the JSON file from the `postman` folder.
4. Import the collection.
5. Start the FastAPI server.
6. Run the customer login request.
7. Run the admin login request when admin functionality is required.
8. Execute the API requests.
The collection contains requests for:
* Authentication
* RBAC
* Products
* Product filters
* Cart
* Orders
* Payments
* Notifications
* Admin operations
Collection variables include:
```text
base_url
access_token
customer_token
admin_token
```
---
## 20. API Testing
FastAPI provides interactive API documentation through Swagger.
Open:
```text
http://127.0.0.1:8000/docs
```
Recommended testing sequence:
1. Register a customer.
2. Login as the customer.
3. Save the customer access token.
4. Authorize protected requests.
5. Browse products.
6. Test product filters.
7. Add a product to the cart.
8. View the cart.
9. Update the cart quantity.
10. Remove a product from the cart.
11. Create an order.
12. View customer orders.
13. Get an order by ID.
14. Login as an admin.
15. Create a product.
16. Update a product.
17. Delete a product.
18. View all orders.
19. Update order status.
20. Test payment endpoints.
21. Test Stripe Checkout and webhook functionality.
22. Test notification endpoints.
---
## 21. GitHub
Repository:
https://github.com/Logesh-510/smart-ecommerce
The repository contains:
* FastAPI backend
* PostgreSQL configuration
* SQLAlchemy models
* Alembic migrations
* Authentication and JWT implementation
* RBAC implementation
* Product APIs
* Cart APIs
* Order APIs
* Payment APIs
* Stripe integration
* Notification system
* Django Admin
* Analytics dashboard
* Report generation
* Postman API collection
* Project documentation
---
## 22. Security Notes
Never commit sensitive credentials.
The following files and directories should remain local:
```text
.env
venv/
__pycache__/
*.pyc
```
Use environment variables for:
* Database credentials
* JWT secret
* Auth0 credentials
* Stripe secret key
* Stripe webhook secret
* Other sensitive configuration
---
## 23. Project Status
The project implementation includes:
* [x] FastAPI backend
* [x] PostgreSQL database
* [x] SQLAlchemy models
* [x] Alembic migrations
* [x] User authentication
* [x] JWT access tokens
* [x] JWT refresh tokens
* [x] Role-based access control
* [x] Auth0 integration
* [x] Product CRUD
* [x] Product filtering
* [x] Shopping cart management
* [x] Order management
* [x] Payment management
* [x] Stripe Checkout
* [x] Stripe webhook handling
* [x] Payment failure handling
* [x] Notification system
* [x] Email notifications
* [x] Real-time WebSocket notifications
* [x] Notification APIs
* [x] Django Admin
* [x] User management
* [x] Product management
* [x] Order management
* [x] Analytics dashboard
* [x] Chart.js analytics
* [x] Revenue trends
* [x] Top-selling products
* [x] Low-stock alerts
* [x] CSV reports
* [x] PDF reports
* [x] Postman API collection
* [x] GitHub repository
* [x] Project documentation
---
## 24. Future Enhancements
Possible future improvements include:
* React frontend
* Docker deployment
* Cloud deployment
* Advanced product image storage
* Payment reconciliation
* Advanced analytics
* Customer reviews and ratings
* Wishlist functionality
* Shopping recommendations
* Production email service integration
---
## 25. Conclusion
The Smart E-Commerce Platform provides a complete backend solution for an e-commerce application using FastAPI and PostgreSQL.
The project combines:
* Secure authentication
* Role-based authorization
* Product management
* Cart management
* Order processing
* Payment integration
* Notifications
* Real-time updates
* Django administration
* Analytics
* CSV/PDF reporting
* API testing through Swagger and Postman
The architecture is designed so that a React or other frontend application can be integrated separately in the future.

