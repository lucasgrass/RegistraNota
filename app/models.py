from datetime import datetime, date
from sqlalchemy.orm import (
    registry, Mapped, mapped_column, relationship
)
from sqlalchemy import (
    func, ForeignKey
)


table_registry = registry()

@table_registry.mapped_as_dataclass
class Usuario:
    __tablename__ = 'usuarios'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    codigo: Mapped[str] = mapped_column(unique=True, nullable=False)
    senha: Mapped[str] = mapped_column(nullable=False)
    nome: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    caixa: Mapped[int]
    is_superuser: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )

@table_registry.mapped_as_dataclass
class Categoria:
    __tablename__ = 'categorias'

    numero_categoria: Mapped[int] = mapped_column(primary_key=True)
    descricao: Mapped[str] = mapped_column(nullable=False)

@table_registry.mapped_as_dataclass
class Nota:
    __tablename__ = 'notas'

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    imagem: Mapped[str] = mapped_column(nullable=False)
    data: Mapped[date] = mapped_column(nullable=False) # ano, mês e dia
    valor: Mapped[int] = mapped_column(nullable=False)
    codigo_planilha: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        init=False, server_default=func.now()
    )

    numero_categoria: Mapped[int] = mapped_column(ForeignKey('categorias.numero_categoria'), nullable=False)
    codigo_usuario: Mapped[int] = mapped_column(ForeignKey('usuarios.codigo'), nullable=False)

    categoria: Mapped["Categoria"] = relationship('Categoria')
    usuario: Mapped["Usuario"] = relationship('Usuario')