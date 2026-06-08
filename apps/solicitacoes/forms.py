from django import forms
from datetime import date
from .models import Solicitacao


class SolicitacaoForm(forms.ModelForm):
    class Meta:
        model = Solicitacao
        fields = [
            'cliente',
            'veiculo',
            'local',
            'funcionario',
            'data_inicio_desejada',
            'data_fim_desejada',
            'motivo',
            'status',
            'observacao',
        ]
        widgets = {
            'data_inicio_desejada': forms.DateInput(attrs={'type': 'date'}),
            'data_fim_desejada': forms.DateInput(attrs={'type': 'date'}),
            'observacao': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        veiculo = cleaned_data.get('veiculo')
        data_inicio = cleaned_data.get('data_inicio_desejada')
        data_fim = cleaned_data.get('data_fim_desejada')
        cliente = cleaned_data.get('cliente')
    
        if cliente and data_inicio:
            if cliente.validade_cnh < date.today():
                raise forms.ValidationError('Cliente possui CNH vencida e não pode realizar locações.')
    
        if veiculo and data_inicio and data_fim:
            conflito = Solicitacao.objects.filter(
                 veiculo=veiculo,
                status__in=['pendente', 'aprovada'],
                data_inicio_desejada__lte=data_fim,
                data_fim_desejada__gte=data_inicio,
            ).exclude(pk=self.instance.pk if self.instance else None)
    
            if conflito.exists():
                raise forms.ValidationError('Este veículo já possui uma solicitação neste período.')
    
        return cleaned_data
