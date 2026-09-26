from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship

from app.database import Base


class Aplicativo(Base):
    __tablename__ = "aplicativos"

    aplicativo_id = Column(Integer, primary_key=True, autoincrement=True)
    # Referencia lógica a COMPANIA (vive en identity-db, no hay FK real entre bases)
    compania_id = Column(Integer, nullable=False)
    nom_aplicativo = Column(String(100), nullable=False)
    creado_en = Column(TIMESTAMP, server_default=func.now())

    roles = relationship("Rol", back_populates="aplicativo")


class Cargo(Base):
    __tablename__ = "cargo"

    cargo_id = Column(Integer, primary_key=True, autoincrement=True)
    # Referencia lógica a COMPANIA (identity-db)
    compania_id = Column(Integer, nullable=False)
    nombre_cargo = Column(String(100), nullable=False)
    descripcion = Column(String(255))

    roles_asignados = relationship("CargoRol", back_populates="cargo")


class Rol(Base):
    __tablename__ = "roles"

    rol_id = Column(Integer, primary_key=True, autoincrement=True)
    aplicativo_id = Column(Integer, ForeignKey("aplicativos.aplicativo_id"), nullable=False)
    nombre_rol = Column(String(50), unique=True, nullable=False)
    descripcion = Column(String(255), nullable=False)

    aplicativo = relationship("Aplicativo", back_populates="roles")
    cargos_asignados = relationship("CargoRol", back_populates="rol")
    permisos_otorgados = relationship("RolPermiso", back_populates="rol")


class Permiso(Base):
    __tablename__ = "permisos"

    permiso_id = Column(Integer, primary_key=True, autoincrement=True)
    permiso = Column(String(50), nullable=False)  # Lectura, escritura, borrado, etc.
    detalle = Column(String(255), nullable=False)

    roles_que_lo_otorgan = relationship("RolPermiso", back_populates="permiso")


class CargoRol(Base):
    """Tabla puente: qué roles tiene cada cargo (parte de la matriz)."""

    __tablename__ = "cargo_roles"

    cargo_id = Column(Integer, ForeignKey("cargo.cargo_id"), primary_key=True)
    rol_id = Column(Integer, ForeignKey("roles.rol_id"), primary_key=True)
    asignado_en = Column(TIMESTAMP, server_default=func.now())

    cargo = relationship("Cargo", back_populates="roles_asignados")
    rol = relationship("Rol", back_populates="cargos_asignados")


class RolPermiso(Base):
    """Tabla puente: qué permisos otorga cada rol (parte de la matriz)."""

    __tablename__ = "rol_permisos"

    rol_id = Column(Integer, ForeignKey("roles.rol_id"), primary_key=True)
    permiso_id = Column(Integer, ForeignKey("permisos.permiso_id"), primary_key=True)

    rol = relationship("Rol", back_populates="permisos_otorgados")
    permiso = relationship("Permiso", back_populates="roles_que_lo_otorgan")
