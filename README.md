# E-commerce Product Tracking API

A comprehensive FastAPI-based e-commerce application with order tracking functionality. The API allows you to manage products, create orders, and track the shipping journey of orders through predefined routes.

## Features

- **Product Management**: Create, read, update, and delete products
- **Order Management**: Create and manage orders
- **Order Tracking**: Complete tracking system with predefined shipping routes
- **Real-time Updates**: Update order locations as they move through the shipping process
- **Progress Tracking**: Calculate delivery progress and estimated delivery dates
- **PostgreSQL Database**: Robust data storage with proper relationships

## Shipping Routes

The system uses predefined shipping routes:
1. **Manmad** (Starting point)
2. **Yeola**
3. **Kopargaon**
4. **Talegaon Dighe**
5. **Sangamner**
6. **Delivered** (Final destination)

## Database Schema

### Tables

#### `products`
- `id` (UUID, Primary Key)
- `name` (String)
- `description` (Text)
- `rating` (Float)
- `price` (Float)
- `quantity` (Integer)
- `img_url` (String)

#### `orders`
- `id` (UUID, Primary Key)
- `product_id` (UUID, Foreign Key to products)
- `user_id` (UUID)
- `status` (Enum: pending, processing, shipped, delivered, cancelled)
- `created_at` (DateTime)
- `updated_at` (DateTime)

#### `tracking`
- `id` (UUID, Primary Key)
- `tracking_id` (String, Unique)
- `order_id` (UUID, Foreign Key to orders)
- `current_location` (String)
- `status` (Enum: order_placed, in_transit, out_for_delivery, delivered)
- `updated_at` (DateTime)

## API Endpoints

### Product Endpoints
- `GET /products/` - Get all products
- `POST /products/` - Create a new product
- `GET /products/{product_id}` - Get product by ID
- `PUT /products/{product_id}` - Update product
- `DELETE /products/{product_id}` - Delete product

### Order Endpoints
- `POST /orders/` - Create a new order
- `GET /orders/{order_id}` - Get order by ID
- `GET /orders/` - Get all orders (with pagination)
- `PUT /orders/{order_id}/status` - Update order status

### Tracking Endpoints

#### Create Tracking Record
```http
POST /track/create
Content-Type: application/json

{
  "order_id": "uuid-of-order",
  "current_location": "Manmad"
}
```

#### Update Order Location
```http
PUT /track/update/{tracking_id}
Content-Type: application/json

{
  "current_location": "Yeola"
}
```

#### Get Tracking Information
```http
GET /track/{tracking_id}
```

#### Mark Order as Delivered
```http
PUT /track/deliver/{tracking_id}
```

#### Get Shipping Routes
```http
GET /track/routes/list
```

## Installation and Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd shoppify
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   DB_USER=your_username
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=product_db
   ```

4. **Initialize the database**
   ```bash
   python -m app.db.init_db
   ```

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- **Interactive API Documentation**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

## Usage Examples

### 1. Create an Order
```bash
curl -X POST "http://localhost:8000/orders/" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "product-uuid",
    "user_id": "user-uuid"
  }'
```

### 2. Create Tracking for Order
```bash
curl -X POST "http://localhost:8000/track/create" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "order-uuid",
    "current_location": "Manmad"
  }'
```

### 3. Update Order Location
```bash
curl -X PUT "http://localhost:8000/track/update/TRK12345678" \
  -H "Content-Type: application/json" \
  -d '{
    "current_location": "Yeola"
  }'
```

### 4. Get Tracking Information
```bash
curl -X GET "http://localhost:8000/track/TRK12345678"
```

### 5. Mark as Delivered
```bash
curl -X PUT "http://localhost:8000/track/deliver/TRK12345678"
```

## Tracking Status Flow

1. **Order Placed**: When tracking is first created
2. **In Transit**: When order moves between locations
3. **Out for Delivery**: When order reaches Sangamner
4. **Delivered**: When order reaches final destination

## Progress Calculation

The system automatically calculates delivery progress based on the current location in the shipping route:
- Progress percentage = (current_location_index / total_locations) * 100
- Estimated delivery date is calculated based on current location

## Error Handling

The API includes comprehensive error handling for:
- Invalid tracking IDs
- Non-existent orders
- Invalid locations
- Duplicate tracking records
- Database connection issues

## Technologies Used

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **PostgreSQL**: Robust relational database
- **Pydantic**: Data validation using Python type annotations
- **Uvicorn**: ASGI server for running FastAPI applications

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.
