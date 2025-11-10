from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category = Column(String)
    image_url = Column(String)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)

    # Relationships
    supplier = relationship("Supplier", back_populates="products")

