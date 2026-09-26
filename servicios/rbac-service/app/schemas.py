from pydantic import BaseModel, ConfigDict


# ---------- Aplicativo ----------
class AplicativoIn(BaseModel):
    compania_id: int
    nom_aplicativo: str


class AplicativoOut(AplicativoIn):
    model_config = ConfigDict(from_attributes=True)
    aplicativo_id: int


# ---------- Cargo ----------
class CargoIn(BaseModel):
    compania_id: int
    nombre_cargo: str
    descripcion: str | None = None


class CargoOut(CargoIn):
    model_config = ConfigDict(from_attributes=True)
    cargo_id: int


# ---------- Rol ----------
class RolIn(BaseModel):
    aplicativo_id: int
    nombre_rol: str
    descripcion: str


class RolOut(RolIn):
    model_config = ConfigDict(from_attributes=True)
    rol_id: int


# ---------- Permiso ----------
class PermisoIn(BaseModel):
    permiso: str
    detalle: str


class PermisoOut(PermisoIn):
    model_config = ConfigDict(from_attributes=True)
    permiso_id: int


# ---------- Matriz (Cargo -> Roles -> Permisos) ----------
class PermisoResumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    permiso_id: int
    permiso: str


class RolConPermisos(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    rol_id: int
    nombre_rol: str
    permisos: list[PermisoResumen] = []


class CargoConMatriz(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    cargo_id: int
    nombre_cargo: str
    roles: list[RolConPermisos] = []


class MatrizUpdate(BaseModel):
    """Reemplaza los roles asignados a un cargo por esta lista."""
    rol_ids: list[int]
