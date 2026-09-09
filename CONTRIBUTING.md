# Como contribuir

Obrigado pelo interesse em melhorar o Automatech.

## Antes de começar

1. Pesquise as issues existentes para evitar trabalho duplicado.
2. Para mudanças maiores, abra uma issue descrevendo o problema e a solução
   proposta.
3. Mantenha cada contribuição pequena e focada em um único objetivo.

## Desenvolvimento

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Coloque regras de negócio em `services/`, componentes visuais reutilizáveis em
`ui/components/` e registre novas automações em `core/module_registry.py`.

## Pull requests

- Explique o problema resolvido e o comportamento resultante.
- Não inclua planilhas pessoais, ambientes virtuais, builds ou configurações
  locais.
- Preserve mensagens amigáveis na interface e detalhes técnicos apenas nos logs.
- Atualize a documentação quando a experiência de uso mudar.
- Informe quais verificações foram realizadas.

Ao contribuir, você concorda que sua alteração será distribuída sob a licença
MIT do projeto.
