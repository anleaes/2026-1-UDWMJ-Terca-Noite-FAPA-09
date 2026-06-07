from django import forms

from .models import Manutencao, Peca, PecaManutencao


class ManutencaoFinalizarForm(forms.Form):
    data_saida = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Data de saida'
    )
    custo = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        min_value=0,
        label='Custo final'
    )


class ManutencaoForm(forms.ModelForm):
    class Meta:
        model = Manutencao
        fields = [
            'veiculo',
            'tipo_manutencao',
            'descricao',
            'data_entrada',
            'custo',
        ]
        widgets = {
            'data_entrada': forms.DateInput(attrs={'type': 'date'}),
            'descricao': forms.Textarea(attrs={'rows': 4}),
        }


class PecaForm(forms.ModelForm):
    class Meta:
        model = Peca
        fields = [
            'tipo_peca',
            'fabricante',
            'preco_unitario',
        ]

    def clean_preco_unitario(self):
        preco_unitario = self.cleaned_data['preco_unitario']
        if preco_unitario < 0:
            raise forms.ValidationError('O preco unitario nao pode ser negativo.')
        return preco_unitario


class PecaManutencaoForm(forms.ModelForm):
    class Meta:
        model = PecaManutencao
        fields = [
            'manutencao',
            'peca',
            'quantidade',
            'preco_unitario',
        ]

    def clean_manutencao(self):
        manutencao = self.cleaned_data['manutencao']
        if manutencao.status in ('CONCLUIDA', 'CANCELADA'):
            raise forms.ValidationError(
                'Nao e possivel adicionar pecas em manutencoes concluidas ou canceladas.'
            )
        return manutencao

    def clean_quantidade(self):
        quantidade = self.cleaned_data['quantidade']
        if quantidade <= 0:
            raise forms.ValidationError('A quantidade deve ser maior que zero.')
        return quantidade

    def clean_preco_unitario(self):
        preco_unitario = self.cleaned_data['preco_unitario']
        if preco_unitario < 0:
            raise forms.ValidationError('O preco unitario nao pode ser negativo.')
        return preco_unitario

    def save(self, commit=True):
        peca_manutencao = super().save(commit=False)
        peca_manutencao.sub_total = (
            peca_manutencao.quantidade * peca_manutencao.preco_unitario
        )

        if commit:
            peca_manutencao.save()

        return peca_manutencao
