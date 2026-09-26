from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.database import get_db
from app import models
from app import schemas

app = FastAPI(
    title="RBAC Service",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {
        "service": "rbac-service",
        "status": "healthy",
    }


# =========================================================
# APLICATIVOS
# =========================================================

@app.get("/applications", response_model=list[schemas.AplicativoOut])
def listar_aplicativos(db: Session = Depends(get_db)):
    return db.scalars(select(models.Aplicativo)).all()


@app.post("/applications", response_model=schemas.AplicativoOut, status_code=201)
def crear_aplicativo(payload: schemas.AplicativoIn, db: Session = Depends(get_db)):
    nuevo = models.Aplicativo(**payload.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


# =========================================================
# CARGOS  (la guía las llama "positions")
# =========================================================

@app.get("/positions", response_model=list[schemas.CargoOut])
def listar_cargos(db: Session = Depends(get_db)):
    return db.scalars(select(models.Cargo)).all()


@app.post("/positions", response_model=schemas.CargoOut, status_code=201)
def crear_cargo(payload: schemas.CargoIn, db: Session = Depends(get_db)):
    nuevo = models.Cargo(**payload.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


# =========================================================
# ROLES
# =========================================================

@app.get("/roles", response_model=list[schemas.RolOut])
def listar_roles(db: Session = Depends(get_db)):
    return db.scalars(select(models.Rol)).all()


@app.post("/roles", response_model=schemas.RolOut, status_code=201)
def crear_rol(payload: schemas.RolIn, db: Session = Depends(get_db)):
    aplicativo = db.get(models.Aplicativo, payload.aplicativo_id)
    if not aplicativo:
        raise HTTPException(status_code=404, detail="El aplicativo indicado no existe")

    nuevo = models.Rol(**payload.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


# =========================================================
# PERMISOS
# =========================================================

@app.get("/permissions", response_model=list[schemas.PermisoOut])
def listar_permisos(db: Session = Depends(get_db)):
    return db.scalars(select(models.Permiso)).all()


@app.post("/permissions", response_model=schemas.PermisoOut, status_code=201)
def crear_permiso(payload: schemas.PermisoIn, db: Session = Depends(get_db)):
    nuevo = models.Permiso(**payload.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


# =========================================================
# MATRIZ  (Cargo -> Roles -> Permisos)
# =========================================================

@app.get("/matrix", response_model=list[schemas.CargoConMatriz])
def consultar_matriz(db: Session = Depends(get_db)):
    """
    Devuelve, para cada cargo, sus roles asignados y los permisos
    que otorga cada uno de esos roles.
    """
    cargos = db.scalars(select(models.Cargo)).all()

    resultado = []
    for cargo in cargos:
        roles_out = []
        for cargo_rol in cargo.roles_asignados:
            rol = cargo_rol.rol
            permisos_out = [
                schemas.PermisoResumen(
                    permiso_id=rp.permiso.permiso_id,
                    permiso=rp.permiso.permiso,
                )
                for rp in rol.permisos_otorgados
            ]
            roles_out.append(
                schemas.RolConPermisos(
                    rol_id=rol.rol_id,
                    nombre_rol=rol.nombre_rol,
                    permisos=permisos_out,
                )
            )
        resultado.append(
            schemas.CargoConMatriz(
                cargo_id=cargo.cargo_id,
                nombre_cargo=cargo.nombre_cargo,
                roles=roles_out,
            )
        )
    return resultado


@app.put("/matrix/{cargo_id}", response_model=schemas.CargoConMatriz)
def actualizar_matriz(cargo_id: int, payload: schemas.MatrizUpdate, db: Session = Depends(get_db)):
    """
    Reemplaza los roles asignados a un cargo por la lista de rol_ids recibida.
    """
    cargo = db.get(models.Cargo, cargo_id)
    if not cargo:
        raise HTTPException(status_code=404, detail="El cargo indicado no existe")

    # Valida que todos los roles enviados existan antes de tocar nada
    roles_nuevos = []
    for rol_id in payload.rol_ids:
        rol = db.get(models.Rol, rol_id)
        if not rol:
            raise HTTPException(status_code=404, detail=f"El rol {rol_id} no existe")
        roles_nuevos.append(rol)

    # Borra las asignaciones actuales de este cargo
    for asignacion in list(cargo.roles_asignados):
        db.delete(asignacion)
    db.flush()

    # Crea las nuevas asignaciones
    for rol in roles_nuevos:
        db.add(models.CargoRol(cargo_id=cargo.cargo_id, rol_id=rol.rol_id))

    db.commit()
    return _matriz_de_un_cargo(cargo, db)


def _matriz_de_un_cargo(cargo: models.Cargo, db: Session) -> schemas.CargoConMatriz:
    db.refresh(cargo)
    roles_out = []
    for cargo_rol in cargo.roles_asignados:
        rol = cargo_rol.rol
        permisos_out = [
            schemas.PermisoResumen(permiso_id=rp.permiso.permiso_id, permiso=rp.permiso.permiso)
            for rp in rol.permisos_otorgados
        ]
        roles_out.append(
            schemas.RolConPermisos(rol_id=rol.rol_id, nombre_rol=rol.nombre_rol, permisos=permisos_out)
        )
    return schemas.CargoConMatriz(
        cargo_id=cargo.cargo_id, nombre_cargo=cargo.nombre_cargo, roles=roles_out
    )
