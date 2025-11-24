# dtos.py
from pydantic import BaseModel, validator, field_validator
from typing import List, Any, Optional

# -------------------------------
# DTOs pentru CRUD
# -------------------------------

class ProductDTO(BaseModel):
    id: Optional[int] = None
    nume: str
    brand: str
    model: str
    descriere: Optional[str] = ""
    pret: float
    categorie: str
    garantie: Optional[int] = 0
    status: Optional[str] = "testare"
    imagine: Optional[str] = ""
    data_adaugare: Optional[str] = None

    @validator("pret")
    def pret_must_be_positive(cls, v):
        if v < 0:
            raise ValueError("Pretul trebuie să fie pozitiv")
        return v

class StockDTO(BaseModel):
    produs_id: int
    cantitate: int
    depozit: str

class OrderDTO(BaseModel):
    client_id: int
    data_comanda: str
    status: str
    produse: List[Any] = []

class UserDTO(BaseModel):
    username: str
    nume: str
    email: str
    password: str
    role: Optional[str] = "Client"
    is_active: Optional[bool] = True

# -------------------------------
# DTO generice pentru update & delete
# -------------------------------

class UpdateDTO(BaseModel):
    filter: Any
    update: Any

    @validator("update")
    def update_not_empty(cls, v):
        if not v:
            raise ValueError("Update nu poate fi gol")
        return v

class DeleteDTO(BaseModel):
    filter: Any

    @field_validator("filter", mode="after")
    @classmethod
    def filter_not_empty(cls, v):
        if not isinstance(v, dict):
            raise ValueError("Filter trebuie să fie un obiect (dict)")

        # Verifică dacă există cel puțin un criteriu valid
        has_criteria = False
        for key, value in v.items():
            if isinstance(value, dict):
                if any(k in value and value[k] not in (None, "", []) for k in ("like", "string", "exact", "min", "max")):
                    has_criteria = True
                    break
            elif value not in (None, "", []):
                has_criteria = True
                break

        if not has_criteria:
            raise ValueError("Filter nu poate fi gol – trebuie să conțină cel puțin un criteriu")

        return v

# -------------------------------
# Helper
# -------------------------------

TABLE_DTOS = {
    "products": ProductDTO,
    "stock": StockDTO,
    "orders": OrderDTO,
    "users": UserDTO
}

def get_dto_class(table_name: str):
    return TABLE_DTOS.get(table_name.lower())
