from pymongo import MongoClient
import toml
from datetime import datetime, timedelta
from bson import ObjectId


def connect_to_mongo(db_name=None):
    config = toml.load(".streamlit/secrets.toml")
    client = MongoClient(config["mongo"]["uri"])
    if db_name:
        return client[db_name]
    else:
        return client
    
def login(username, password):
    db = connect_to_mongo("users")
    data_collection = db.data
    user = data_collection.find_one({"username": username})
    if user and user["password"] == password:
        return True
    else:
        return False

def add_task(task_name, task_description, task_date, task_time, assigned_to):
    db = connect_to_mongo("users")
    tasks_collection = db.tasks
    
    task_datetime = datetime.combine(task_date, task_time)
    
    task_document = {
        "nombre": task_name,
        "descripcion": task_description,
        "fecha_hora": task_datetime,
        "asignado_a": assigned_to,
        "estado": "pendiente",
        "fecha_creacion": datetime.now(),
        "ultima_actualizacion": datetime.now(),
        "comentarios": [],
        "solicitud_extension": None
    }
    
    result = tasks_collection.insert_one(task_document)
    return result.inserted_id

def get_month_tasks(year, month):
    """Obtiene todas las tareas para un mes específico"""
    db = connect_to_mongo("users")
    tasks_collection = db.tasks
    
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    tasks = tasks_collection.find({
        "fecha_hora": {
            "$gte": start_date,
            "$lt": end_date
        }
    })
    return list(tasks)

def get_day_tasks(year, month, day):
    """Obtiene todas las tareas para un día específico"""
    db = connect_to_mongo("users")
    tasks_collection = db.tasks
    
    start_date = datetime(year, month, day)
    end_date = start_date + timedelta(days=1)
    
    tasks = tasks_collection.find({
        "fecha_hora": {
            "$gte": start_date,
            "$lt": end_date
        }
    }).sort("fecha_hora", 1)
    
    return list(tasks)

def add_comment(task_id, comment):
    """Añade un comentario a una tarea"""
    db = connect_to_mongo("users")
    tasks_collection = db.tasks
    
    comment_doc = {
        "texto": comment,
        "fecha": datetime.now()
    }
    
    tasks_collection.update_one(
        {"_id": task_id},
        {
            "$push": {"comentarios": comment_doc},
            "$set": {"ultima_actualizacion": datetime.now()}
        }
    )

def mark_as_completed(task_id):
    """Marca una tarea como completada"""
    db = connect_to_mongo("users")
    tasks_collection = db.tasks
    
    tasks_collection.update_one(
        {"_id": task_id},
        {
            "$set": {
                "estado": "completada",
                "ultima_actualizacion": datetime.now()
            }
        }
    )

def request_extension(task_id, reason):
    """Solicita una extensión para una tarea"""
    db = connect_to_mongo("users")
    tasks_collection = db.tasks
    
    extension_request = {
        "fecha_solicitud": datetime.now(),
        "razon": reason,
        "estado": "pendiente"
    }
    
    tasks_collection.update_one(
        {"_id": task_id},
        {
            "$set": {
                "estado": "extension_solicitada",
                "solicitud_extension": extension_request,
                "ultima_actualizacion": datetime.now()
            }
        }
    )

def mark_as_impossible(task_id, reason):
    """Marca una tarea como imposible"""
    db = connect_to_mongo("users")
    tasks_collection = db.tasks
    
    tasks_collection.update_one(
        {"_id": task_id},
        {
            "$set": {
                "estado": "imposible",
                "razon_imposible": reason,
                "ultima_actualizacion": datetime.now()
            }
        }
    )


def get_pending_admin_tasks():
    """Obtiene todas las tareas que requieren atención del administrador"""
    db = connect_to_mongo("users")
    tasks_collection = db.tasks
    
    # Buscar tareas con extensión solicitada o marcadas como imposible
    tasks = tasks_collection.find({
        "$or": [
            {"estado": "extension_solicitada"},
            {"estado": "imposible"}
        ]
    }).sort("fecha_hora", 1)
    
    return list(tasks)

def approve_extension(task_id, new_date, new_time):
    """Aprueba una solicitud de extensión y actualiza la fecha"""
    db = connect_to_mongo("users")
    tasks_collection = db.tasks
    
    # Obtener la tarea actual
    task = tasks_collection.find_one({"_id": ObjectId(task_id)})
    if not task:
        return False
        
    # Crear nueva fecha_hora
    new_datetime = datetime.combine(new_date, new_time)
    
    # Actualizar la tarea
    result = tasks_collection.update_one(
        {"_id": ObjectId(task_id)},
        {
            "$set": {
                "fecha_hora": new_datetime,
                "estado": "pendiente",
                "ultima_actualizacion": datetime.now(),
                "solicitud_extension": None
            },
            "$push": {
                "comentarios": {
                    "texto": f"Extensión aprobada. Nueva fecha: {new_datetime.strftime('%Y-%m-%d %H:%M')}",
                    "fecha": datetime.now()
                }
            }
        }
    )
    
    return result.modified_count > 0

def deny_extension(task_id, reason):
    """Deniega una solicitud de extensión"""
    db = connect_to_mongo("users")
    tasks_collection = db.tasks
    
    result = tasks_collection.update_one(
        {"_id": ObjectId(task_id)},
        {
            "$set": {
                "estado": "pendiente",
                "ultima_actualizacion": datetime.now(),
                "solicitud_extension": None
            },
            "$push": {
                "comentarios": {
                    "texto": f"Extensión denegada. Razón: {reason}",
                    "fecha": datetime.now()
                }
            }
        }
    )
    
    return result.modified_count > 0

def handle_impossible_task(task_id, action, reason=None, new_name=None, new_description=None):
    """Maneja una tarea marcada como imposible"""
    db = connect_to_mongo("users")
    tasks_collection = db.tasks
    
    if action == "accept":
        if new_name and new_description:
            # Actualizar la tarea con nuevos detalles
            result = tasks_collection.update_one(
                {"_id": ObjectId(task_id)},
                {
                    "$set": {
                        "nombre": new_name,
                        "descripcion": new_description,
                        "estado": "pendiente",
                        "ultima_actualizacion": datetime.now(),
                        "razon_imposible": None
                    },
                    "$push": {
                        "comentarios": {
                            "texto": "Tarea modificada por el administrador",
                            "fecha": datetime.now()
                        }
                    }
                }
            )
        else:
            # Eliminar la tarea
            result = tasks_collection.delete_one({"_id": ObjectId(task_id)})
        
    elif action == "deny":
        # Denegar y volver a estado pendiente
        result = tasks_collection.update_one(
            {"_id": ObjectId(task_id)},
            {
                "$set": {
                    "estado": "pendiente",
                    "ultima_actualizacion": datetime.now(),
                    "razon_imposible": None
                },
                "$push": {
                    "comentarios": {
                        "texto": f"Solicitud de imposibilidad denegada. Razón: {reason}",
                        "fecha": datetime.now()
                    }
                }
            }
        )
    
    return True

def get_filtered_tasks(estados=None, usuarios=None, fecha_inicio=None, fecha_fin=None):
    """
    Obtiene tareas filtradas según los criterios especificados
    """
    db = connect_to_mongo("users")
    tasks_collection = db.tasks
    
    # Construir query
    query = {}
    
    if estados:
        query["estado"] = {"$in": estados}
        
    if usuarios:
        query["asignado_a"] = {"$in": usuarios}
        
    if fecha_inicio and fecha_fin:
        query["fecha_hora"] = {
            "$gte": datetime.combine(fecha_inicio, datetime.min.time()),
            "$lte": datetime.combine(fecha_fin, datetime.max.time())
        }
    
    # Obtener y ordenar tareas
    tasks = tasks_collection.find(query).sort("fecha_hora", 1)
    return list(tasks)

def update_task(task_id, new_name, new_description, new_date, new_time, new_assigned, new_status):
    """
    Actualiza los detalles de una tarea
    """
    db = connect_to_mongo("users")
    tasks_collection = db.tasks
    
    new_datetime = datetime.combine(new_date, new_time)
    
    result = tasks_collection.update_one(
        {"_id": ObjectId(task_id)},
        {
            "$set": {
                "nombre": new_name,
                "descripcion": new_description,
                "fecha_hora": new_datetime,
                "asignado_a": new_assigned,
                "estado": new_status,
                "ultima_actualizacion": datetime.now()
            },
            "$push": {
                "comentarios": {
                    "texto": "Tarea actualizada por el administrador",
                    "fecha": datetime.now()
                }
            }
        }
    )
    
    return result.modified_count > 0

def delete_task(task_id):
    """
    Elimina una tarea
    """
    db = connect_to_mongo("users")
    tasks_collection = db.tasks
    
    result = tasks_collection.delete_one({"_id": ObjectId(task_id)})
    return result.deleted_count > 0