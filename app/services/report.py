from tortoise import Tortoise
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from app.models import Nota, Categoria, Planilha, Usuario

from fastapi import APIRouter, HTTPException, status
from tortoise.exceptions import DoesNotExist

from datetime import datetime

def formatar_codigo(codigo):
    """Remove ou substitui caracteres inválidos no nome do arquivo."""
    return codigo.replace('/', '_')  # Substitui a barra por um underscore

def footer(canvas, doc):
    """Adiciona o número da página no canto inferior direito."""
    canvas.saveState()
    page_number_text = f"Página {doc.page}"
    canvas.drawRightString(200 * mm, 10 * mm, page_number_text)
    canvas.restoreState()

async def criar_pdf_nota_fiscal(codigo_usuario, codigo_planilha):
    # Configuração do PDF com margem adicional
    data_atual = datetime.now().strftime('%d-%m-%Y')
    nome_arquivo = f"Relatorio-{formatar_codigo(codigo_usuario)}-{formatar_codigo(codigo_planilha)}-{data_atual}.pdf"
    doc = SimpleDocTemplate(
        nome_arquivo,
        pagesize=LETTER,
        rightMargin=40,  # Aumentando a margem direita
        leftMargin=40,  # Aumentando a margem esquerda
        topMargin=40,   # Aumentando a margem superior
        bottomMargin=40 # Aumentando a margem inferior
    )
    elementos = []
    estilos = getSampleStyleSheet()

    # Estilo customizado para textos menores e em negrito (ajustando o tamanho da fonte)
    estilo_negrito_menor = ParagraphStyle(
        'NegritoMenor',
        parent=estilos['Normal'],
        fontName='Helvetica-Bold',  # Definindo o estilo como negrito
        fontSize=9,  # Ajustando o tamanho da fonte para 9
        spaceAfter=4  # Adiciona um pequeno espaço depois do texto
    )

    # 1. Cabeçalho
    # logo_path = "logo.png"  # Caminho para o logotipo
    # try:
    #     logo = Image(logo_path, width=1.0 * inch, height=0.7 * inch)  # Logo menor
    #     logo.hAlign = 'LEFT'
    #     elementos.append(logo)
    # except FileNotFoundError:
    #     elementos.append(Paragraph("[Logotipo da Empresa]", estilos['Normal']))
        
    # elementos.append(Spacer(1, 0.1 * inch))  # Espaço após a tabela

    # 2. Cidade e Período
    cidade_text = Paragraph("Cidade: São Paulo", estilo_negrito_menor)
    periodo_text = Paragraph("Período: 01/01/2025 - 10/01/2025", estilo_negrito_menor)
    tabela_cidade_periodo = Table([[cidade_text, periodo_text]], colWidths=[3 * inch, 2.5 * inch])
    tabela_cidade_periodo.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0, colors.white)
    ]))
    elementos.append(tabela_cidade_periodo)
    elementos.append(Spacer(1, 0.1 * inch))  # Espaço após a tabela

    # 3. Quantidade de Notas Cadastradas e Código da Planilha
    qtd_notas = await Nota.filter(codigo_usuario=codigo_usuario).count()
    qtd_notas_text = Paragraph(f"Notas Cadastradas: {qtd_notas}", estilo_negrito_menor)
    ultima_planilha = await Planilha.filter(codigo_usuario=codigo_usuario).order_by('-id').first()
    codigo_planilha_text = Paragraph(f"Código da Planilha: {ultima_planilha}", estilo_negrito_menor)
    tabela_qtd_notas = Table([[qtd_notas_text, codigo_planilha_text]], colWidths=[3 * inch, 2.5 * inch])
    tabela_qtd_notas.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0, colors.white)
    ]))
    elementos.append(tabela_qtd_notas)
    elementos.append(Spacer(1, 0.3 * inch))  # Espaço após a tabela

    # 4. Tabela de Notas Fiscais
    user = await Usuario.filter(codigo_usuario=codigo_usuario).exists()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    try:
        sheet = await Planilha.get(codigo_planilha=codigo_planilha, codigo_usuario=codigo_usuario)
    except DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Planilha não encontrada para este usuário.")

    # Buscando as notas fiscais
    notas = await Nota.filter(codigo_usuario=codigo_usuario, planilha_id=sheet.id).select_related('codigo_categoria').order_by("-created_at")

    # Preparando a lista de notas fiscais
    notas_fiscais = []
    notas_fiscais.append(["ID", "Descrição da Categoria", "Valor", "Data"])

    # Iterando sobre as notas
    for nota in notas:
        categoria = nota.codigo_categoria  # A categoria já está carregada
        valor_formatado = f"R$ {nota.valor / 100:,.2f}".replace('.', ',')
        notas_fiscais.append([nota.id, categoria.descricao, valor_formatado, nota.data.strftime('%d/%m/%Y')])
    
    tabela_nota_fiscal = Table(notas_fiscais, colWidths=[1 * inch, 2.5 * inch, 1 * inch, 1 * inch])
    tabela_nota_fiscal.setStyle(TableStyle([ 
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4CAF50")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.gray)
    ]))
    elementos.append(tabela_nota_fiscal)
    elementos.append(Spacer(1, 0.5 * inch))

    # 5. Resumo Financeiro
    total = sum([nota.valor for nota in notas])  # Calculando o total das notas
    total_formatado = f"R$ {total / 100:,.2f}".replace('.', ',')  # Formatação do total

    # Não tente formatar 'total_formatado' novamente, já que ele é uma string formatada
    resumo_financeiro = [
        ["Subtotal", total_formatado],
        ["Total a Pagar", total_formatado]
    ]
    tabela_resumo = Table(resumo_financeiro, colWidths=[4 * inch, 2 * inch])
    tabela_resumo.setStyle(TableStyle([
        ('BACKGROUND', (-1, -1), (-1, -1), colors.HexColor("#4CAF50")),
        ('TEXTCOLOR', (-1, -1), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ]))
    elementos.append(tabela_resumo)
    elementos.append(Spacer(1, 0.5 * inch))

    # 6. Espaço para Assinatura
    elementos.append(Spacer(1, 0.5 * inch))
    elementos.append(Paragraph("_____________________________________", estilos['Normal']))
    elementos.append(Paragraph("Assinatura do Cliente", estilos['Normal']))
    elementos.append(Spacer(1, 0.5 * inch))

    # Construir PDF com rodapé
    doc.build(elementos, onFirstPage=footer, onLaterPages=footer)
    print(f"PDF gerado com sucesso: {nome_arquivo}")