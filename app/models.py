from tortoise import fields
from tortoise.models import Model

class Categoria(Model):
    codigo_categoria = fields.IntField(pk=True)
    descricao = fields.CharField(max_length=255)

    notas: fields.ReverseRelation["Nota"]

    class Meta:
        table = "categorias"

class Nota(Model):
    id = fields.IntField(pk=True)
    url_image_original = fields.CharField(max_length=255)
    url_image_scan = fields.CharField(max_length=255)
    data = fields.DateField()
    valor = fields.IntField()
    descricao = fields.CharField(max_length=255)
    created_at = fields.DatetimeField(auto_now_add=True)

    codigo_categoria = fields.ForeignKeyField("models.Categoria", related_name="notas", on_delete=fields.CASCADE)
    codigo_usuario = fields.ForeignKeyField("models.Usuario", related_name="notas", on_delete=fields.CASCADE)
    planilha = fields.ForeignKeyField("models.Planilha", related_name="notas", on_delete=fields.CASCADE)

    class Meta:
        table = "notas"

class Usuario(Model):
    codigo_usuario = fields.CharField(pk=True, max_length=20)
    senha = fields.CharField(max_length=255)
    nome = fields.CharField(max_length=255)
    email = fields.CharField(max_length=255, unique=True)
    caixa = fields.IntField()
    is_superuser = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    notas: fields.ReverseRelation["Nota"]

    class Meta:
        table = "usuarios"

class Planilha(Model):
    id = fields.IntField(pk=True)
    codigo_planilha = fields.CharField(max_length=20)

    codigo_usuario = fields.ForeignKeyField("models.Usuario", related_name="planilhas", on_delete=fields.CASCADE)

    class Meta:
        table = "planilhas"

class RefreshToken(Model):
    id = fields.IntField(pk=True)
    refresh_token = fields.TextField()
    expires_at = fields.DatetimeField()
    created_at = fields.DatetimeField(auto_now_add=True)
    is_revoked = fields.BooleanField(default=False)

    usuario = fields.ForeignKeyField("models.Usuario", related_name="refresh_tokens", on_delete=fields.CASCADE)

    class Meta:
        table = "refresh_tokens"