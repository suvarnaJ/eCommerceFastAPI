from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session
from sqlalchemy import func

from database import engine, Base, get_db

from models import (
    User,
    Product,
    Order,
    OrderItem
)

from schemas import (
    UserCreate,
    UserResponse,
    ProductCreate,
    ProductResponse,
    InventoryUpdate,
    OrderCreate,
    OrderResponse
)


# =====================================
# CREATE DATABASE TABLES
# =====================================

Base.metadata.create_all(bind=engine)


# =====================================
# FASTAPI APPLICATION
# =====================================

app = FastAPI(
    title="Mini E-Commerce API",
    description="FastAPI + Neon PostgreSQL E-Commerce Backend",
    version="1.0.0"
)


# =====================================
# HOME
# =====================================

@app.get("/")
def home():

    return {
        "message": "Welcome to Mini E-Commerce API"
    }


# =====================================
# USER APIs
# =====================================

@app.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):

    existing_user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if existing_user:

        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    user = User(
        name=user_data.name,
        email=user_data.email
    )

    db.add(user)

    db.commit()

    db.refresh(user)

    return user


# =====================================
# GET USERS
# =====================================

@app.get(
    "/users",
    response_model=list[UserResponse]
)
def get_users(
    db: Session = Depends(get_db)
):

    return (
        db.query(User)
        .order_by(User.id)
        .all()
    )


# =====================================
# PRODUCT APIs
# =====================================

@app.post(
    "/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED
)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db)
):

    product = Product(
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        inventory=product_data.inventory
    )

    db.add(product)

    db.commit()

    db.refresh(product)

    return product


# =====================================
# GET PRODUCTS
# =====================================

@app.get(
    "/products",
    response_model=list[ProductResponse]
)
def get_products(
    db: Session = Depends(get_db)
):

    return (
        db.query(Product)
        .filter(Product.inventory >= 0)
        .order_by(Product.name)
        .all()
    )


# =====================================
# GET SINGLE PRODUCT
# =====================================

@app.get(
    "/products/{product_id}",
    response_model=ProductResponse
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):

    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product


# =====================================
# UPDATE INVENTORY
# =====================================

@app.patch(
    "/products/{product_id}/inventory",
    response_model=ProductResponse
)
def update_inventory(
    product_id: int,
    inventory_data: InventoryUpdate,
    db: Session = Depends(get_db)
):

    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:

        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    product.inventory = inventory_data.inventory

    db.commit()

    db.refresh(product)

    return product


# =====================================
# CREATE ORDER
# =====================================

@app.post(
    "/orders",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED
)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db)
):

    # -----------------------------
    # Check user
    # -----------------------------

    user = (
        db.query(User)
        .filter(User.id == order_data.user_id)
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if not order_data.items:

        raise HTTPException(
            status_code=400,
            detail="Order must contain at least one item"
        )

    # -----------------------------
    # Create Order
    # -----------------------------

    order = Order(
        user_id=order_data.user_id,
        total_amount=0,
        status="PLACED"
    )

    db.add(order)

    db.flush()

    total_order_amount = 0

    # -----------------------------
    # Process Items
    # -----------------------------

    for item in order_data.items:

        product = (
            db.query(Product)
            .filter(Product.id == item.product_id)
            .first()
        )

        if not product:

            db.rollback()

            raise HTTPException(
                status_code=404,
                detail=f"Product {item.product_id} not found"
            )

        # -------------------------
        # Check inventory
        # -------------------------

        if product.inventory < item.quantity:

            db.rollback()

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Insufficient inventory for "
                    f"{product.name}. "
                    f"Available: {product.inventory}"
                )
            )

        # -------------------------
        # Quantity × Unit Price
        # -------------------------

        item_total = (
            item.quantity *
            product.price
        )

        # -------------------------
        # Create Order Item
        # -------------------------

        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=item.quantity,
            unit_price=product.price,
            item_total=item_total
        )

        db.add(order_item)

        # -------------------------
        # Reduce Inventory
        # -------------------------

        product.inventory -= item.quantity

        # -------------------------
        # Add to Order Total
        # -------------------------

        total_order_amount += item_total

    # -----------------------------
    # Order Total
    # -----------------------------

    order.total_amount = total_order_amount

    db.commit()

    db.refresh(order)

    return order


# =====================================
# GET ALL ORDERS
# =====================================

@app.get(
    "/orders",
    response_model=list[OrderResponse]
)
def get_orders(
    db: Session = Depends(get_db)
):

    return (
        db.query(Order)
        .order_by(Order.created_at.desc())
        .all()
    )


# =====================================
# GET USER ORDERS
# =====================================

@app.get(
    "/users/{user_id}/orders",
    response_model=list[OrderResponse]
)
def get_user_orders(
    user_id: int,
    db: Session = Depends(get_db)
):

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return (
        db.query(Order)
        .filter(Order.user_id == user_id)
        .order_by(Order.created_at.desc())
        .all()
    )


# =====================================
# GET SINGLE ORDER
# =====================================

@app.get(
    "/orders/{order_id}",
    response_model=OrderResponse
)
def get_order(
    order_id: int,
    db: Session = Depends(get_db)
):

    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    if not order:

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    return order


# =====================================
# CANCEL ORDER
# =====================================

@app.patch(
    "/orders/{order_id}/cancel"
)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db)
):

    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .first()
    )

    if not order:

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    if order.status == "CANCELLED":

        raise HTTPException(
            status_code=400,
            detail="Order is already cancelled"
        )

    # -----------------------------
    # Restore Inventory
    # -----------------------------

    for item in order.items:

        product = (
            db.query(Product)
            .filter(Product.id == item.product_id)
            .first()
        )

        if product:

            product.inventory += item.quantity

    order.status = "CANCELLED"

    db.commit()

    return {
        "message": "Order cancelled successfully",
        "order_id": order.id,
        "status": order.status
    }


# =====================================
# SQL JOIN API
# =====================================

@app.get("/reports/order-details")
def order_details(
    db: Session = Depends(get_db)
):

    results = (
        db.query(
            Order.id.label("order_id"),
            User.name.label("user_name"),
            Product.name.label("product_name"),
            OrderItem.quantity,
            OrderItem.unit_price,
            OrderItem.item_total
        )
        .join(User, Order.user_id == User.id)
        .join(
            OrderItem,
            Order.id == OrderItem.order_id
        )
        .join(
            Product,
            OrderItem.product_id == Product.id
        )
        .order_by(Order.id.desc())
        .all()
    )

    return [
        {
            "order_id": row.order_id,
            "user_name": row.user_name,
            "product_name": row.product_name,
            "quantity": row.quantity,
            "unit_price": row.unit_price,
            "item_total": row.item_total
        }
        for row in results
    ]


# =====================================
# GROUP BY + AGGREGATE REPORT
# =====================================

@app.get("/reports/product-sales")
def product_sales(
    db: Session = Depends(get_db)
):

    results = (
        db.query(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            func.sum(
                OrderItem.quantity
            ).label("total_quantity"),
            func.sum(
                OrderItem.item_total
            ).label("total_sales")
        )
        .join(
            OrderItem,
            Product.id == OrderItem.product_id
        )
        .join(
            Order,
            OrderItem.order_id == Order.id
        )
        .filter(
            Order.status != "CANCELLED"
        )
        .group_by(
            Product.id,
            Product.name
        )
        .order_by(
            func.sum(
                OrderItem.item_total
            ).desc()
        )
        .all()
    )

    return [
        {
            "product_id": row.product_id,
            "product_name": row.product_name,
            "total_quantity": row.total_quantity,
            "total_sales": row.total_sales
        }
        for row in results
    ]


# =====================================
# TOTAL SALES
# =====================================

@app.get("/reports/total-sales")
def total_sales(
    db: Session = Depends(get_db)
):

    total = (
        db.query(
            func.sum(Order.total_amount)
        )
        .filter(
            Order.status != "CANCELLED"
        )
        .scalar()
    )

    return {
        "total_sales": total or 0
    }