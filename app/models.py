from tortoise import fields
from tortoise.models import Model

class Categoria(Model):
    numero_categoria = fields.IntField(pk=True)
    descricao = fields.CharField(max_length=255)

    notas: fields.ReverseRelation["Nota"]  # Relacionamento reverso com a tabela Nota

    class Meta:
        table = "categorias"

class Nota(Model):
    id = fields.IntField(pk=True)
    imagem = fields.CharField(max_length=255)
    data = fields.DateField()  # ano, mês e dia
    valor = fields.IntField()
    codigo_planilha = fields.IntField()
    created_at = fields.DatetimeField(auto_now_add=True)

    numero_categoria = fields.ForeignKeyField("models.Categoria", related_name="notas", on_delete=fields.CASCADE)
    codigo_usuario = fields.ForeignKeyField("models.Usuario", related_name="notas", on_delete=fields.CASCADE)

    class Meta:
        table = "notas"

class Usuario(Model):
    id = fields.IntField(pk=True)
    codigo = fields.CharField(max_length=100, unique=True)
    senha = fields.CharField(max_length=255)
    nome = fields.CharField(max_length=255)
    email = fields.CharField(max_length=255, unique=True)
    caixa = fields.IntField()
    is_superuser = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    notas: fields.ReverseRelation["Nota"]  # Relacionamento reverso com a tabela Nota

    class Meta:
        table = "usuarios"

class Planilha(Model):
    id = fields.IntField(pk=True)
    codigo = fields.CharField(max_length=100, unique=True)

    class Meta:
        table = "planilhas"
