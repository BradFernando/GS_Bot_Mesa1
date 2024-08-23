from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Category(Base):
    __tablename__ = 'Category'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    slug = Column(String, index=True)


class Product(Base):
    __tablename__ = 'Product'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Numeric(10, 2), index=True)
    stock = Column(Integer, index=True)
    image = Column(String)
    categoryId = Column(Integer, ForeignKey('Category.id'))
    orders = relationship("OrderProducts", back_populates="product")


class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    order_products = relationship("OrderProducts", back_populates="order")


class OrderProducts(Base):
    __tablename__ = 'OrderProducts'
    id = Column(Integer, primary_key=True)
    orderId = Column(Integer, ForeignKey('orders.id'))
    productId = Column(Integer, ForeignKey('Product.id'))
    quantity = Column(Integer)
    order = relationship("Order", back_populates="order_products")
    product = relationship("Product", back_populates="orders")
