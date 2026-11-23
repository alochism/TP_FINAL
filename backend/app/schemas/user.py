from pydantic import BaseModel, EmailStr, field_validator



class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError(
                "La contraseña debe tener al menos 8 caracteres"
            )

        if len(value.encode("utf-8")) > 72:
            raise ValueError(
                "La contraseña no puede superar 72 bytes"
            )

        return value



class UserResponse(BaseModel):
    id: int
    email: EmailStr

    model_config = {
        "from_attributes": True
    }


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str