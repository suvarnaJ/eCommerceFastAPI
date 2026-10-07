from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Boolean,
    UniqueConstraint
)

from sqlalchemy.orm import relationship

from database import Base


# =========================
# USERS
# =========================

class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(150),
        unique=True,
        nullable=False,
        index=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # One User -> Many Orders

    orders = relationship(
        "Order",
        back_populates="user",
        cascade="all, delete-orphan"
    )


# =========================
# PRODUCTS
# =========================

class Product(Base):

    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(
        String(150),
        nullable=False
    )

    description = Column(
        String(500),
        nullable=True
    )

    price = Column(
        Float,
        nullable=False
    )

    inventory = Column(
        Integer,
        nullable=False,
        default=0
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Product -> OrderItems

    order_items = relationship(
        "OrderItem",
        back_populates="product"
    )


# =========================
# ORDERS
# =========================

class Order(Base):

    __tablename__ = "orders"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    total_amount = Column(
        Float,
        nullable=False,
        default=0
    )

    status = Column(
        String(30),
        nullable=False,
        default="PLACED"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Order -> User

    user = relationship(
        "User",
        back_populates="orders"
    )

    # Order -> OrderItems

    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )


# =========================
# ORDER ITEMS
# =========================

class OrderItem(Base):

    __tablename__ = "order_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id"),
        nullable=False
    )

    quantity = Column(
        Integer,
        nullable=False
    )

    unit_price = Column(
        Float,
        nullable=False
    )

    item_total = Column(
        Float,
        nullable=False
    )

    # OrderItem -> Order

    order = relationship(
        "Order",
        back_populates="items"
    )

    # OrderItem -> Product

    product = relationship(
        "Product",
        back_populates="order_items"
    )

    __table_args__ = (
        UniqueConstraint(
            "order_id",
            "product_id",
            name="unique_order_product"
        ),
    )