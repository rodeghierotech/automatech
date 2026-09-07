# Automatiza

Central de Automações desktop para pequenas e médias empresas. Automatize tarefas
repetitivas de escritório (planilhas e arquivos) em poucos cliques, sem precisar
saber programação.

## Tecnologias

- Python 3.11+
- CustomTkinter (interface gráfica)
- pandas + openpyxl (planilhas Excel)
- PyInstaller (geração do executável Windows)

## Estrutura do projeto

```
Automatiza/
├── main.py                  # ponto de entrada
├── build.py                 # gera o .exe com PyInstaller
├── requirements.txt
├── config/
│   └── settings.py          # configurações persistidas em config.json
├── core/
│   ├── module_base.py       # contrato (classe base) de todo módulo
│   ├── module_registry.py   # lista central de módulos disponíveis
│   ├── task_runner.py       # executa tarefas pesadas sem travar a UI
│   └── logger.py            # logs/app.log
├── services/
│   ├── excel_service.py     # lógica pura de planilhas (sem UI)
│   └── file_service.py      # lógica pura de arquivos/pastas (sem UI)
├── utils/
│   ├── errors.py            # exceções com mensagem amigável
│   ├── paths.py             # sanitização de nomes, caminhos únicos
│   └── validators.py
├── ui/
│   ├── app.py                # janela principal
│   ├── sidebar.py
│   ├── theme.py               # cores, fontes, espaçamentos
│   ├── components/            # ModuleCard, StatusBadge
│   └── screens/                # HomeScreen, SettingsScreen
└── modules/
    ├── spreadsheets/
    │   ├── merge.py           # Módulo 1 — Unir planilhas
    │   ├── split.py           # Módulo 2 — Separar planilha
    │   └── clean.py           # Módulo 3 — Limpar planilha
    └── files/
        └── organizer.py       # Módulo 4 — Organizador de arquivos
```

**Princípio da arquitetura:** interface (`ui/`) nunca contém lógica de negócio.
Toda manipulação de dados fica em `services/`. Cada módulo (`modules/`) é
independente e só depende de `services/` e `core/`.

## Instalação (ambiente de desenvolvimento)

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Executar durante o desenvolvimento

```bash
python main.py
```

## Gerar o executável (.exe)

```bash
python build.py
```

O executável final fica em `dist/Automatiza/Automatiza.exe`. Ele não abre
console e não requer Python instalado na máquina do cliente.

> Se o build falhar reconhecendo temas do CustomTkinter, confirme que a
> flag `--collect-all customtkinter` está presente em `build.py` (já
> configurada por padrão).

## Como adicionar um novo módulo

1. Crie a pasta/arquivo em `modules/<categoria>/<nome>.py`.
2. Implemente uma classe que herda de `AutomationModule` (`core/module_base.py`),
   definindo `info = ModuleInfo(key=..., name=..., description=..., category=..., icon=...)`
   e o método `build_ui(self, parent, app)` retornando um `CTkFrame`.
3. Coloque a lógica de negócio pura (sem CustomTkinter) em `services/`.
4. Registre a nova classe em `core/module_registry.py`, na lista `MODULES`.

Nenhum outro arquivo precisa ser alterado — o card aparece automaticamente
na tela inicial.

## Logs

Erros técnicos completos (stack trace) são gravados em `logs/app.log`.
O usuário nunca vê esse conteúdo; a interface sempre mostra uma mensagem
amigável.

## Regras de segurança de dados

- Nenhuma automação apaga arquivos do usuário.
- Nenhuma automação sobrescreve arquivos existentes automaticamente
  (nomes de saída são gerados com sufixo incremental quando há conflito).
- O arquivo original nunca é modificado — sempre é gerado um novo arquivo.
