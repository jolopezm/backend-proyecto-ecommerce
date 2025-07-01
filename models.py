from sqlalchemy import Column, Integer, String, LargeBinary, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
import base64

Base = declarative_base()

class Producto(Base):
    __tablename__ = "producto"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    precio = Column(Float)
    cantidad = Column(Integer)
    descripcion = Column(String, default='Sin descripción')
    imagen = Column(LargeBinary, nullable=True)
    imagen_url = Column(String, nullable=True)
    categoria_id = Column(Integer, ForeignKey('categoria.id'))

    categoria = relationship("Categoria", back_populates="productos")
    detalles = relationship('DetalleOrdenCompra', back_populates='producto')

    def as_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "precio": self.precio,
            "cantidad": self.cantidad,
            "descripcion": self.descripcion,
            "imagen": base64.b64encode(self.imagen).decode('utf-8') if self.imagen else None,
            "imagen_url": self.imagen_url,
            "categoria_id": self.categoria_id
        }

class Usuario(Base):
    __tablename__ = "usuario"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    role = Column(String, default="customer")
    ordenes = relationship('OrdenCompra', back_populates='usuario')

    def as_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "email": self.email,
            "hashed_password": self.hashed_password
        }

class Transaccion(Base):
    __tablename__ = 'transaccion'
    token = Column(String, primary_key=True, index=True)

    def as_dict(self):
        return {
            'token': self.token
        }