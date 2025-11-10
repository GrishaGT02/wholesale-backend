from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate


def get_supplier(db: Session, supplier_id: int) -> Optional[Supplier]:
    """Получить поставщика по ID"""
    return db.query(Supplier).filter(Supplier.id == supplier_id).first()


def get_suppliers(db: Session, skip: int = 0, limit: int = 100) -> List[Supplier]:
    """Получить список поставщиков"""
    return db.query(Supplier).offset(skip).limit(limit).all()


def create_supplier(db: Session, supplier: SupplierCreate) -> Supplier:
    """Создать нового поставщика"""
    db_supplier = Supplier(**supplier.dict())
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier


def delete_supplier(db: Session, supplier_id: int) -> bool:
    """Удалить поставщика"""
    db_supplier = get_supplier(db, supplier_id)
    if not db_supplier:
        return False
    
    db.delete(db_supplier)
    db.commit()
    return True

