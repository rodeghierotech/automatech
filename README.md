<div align="center">
  <img src="logo-automatech.png" alt="Logo do Automatech" width="220">

  # Automatech

  **Automações de escritório em uma interface simples, local e segura.**

  ![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
  ![Plataforma](https://img.shields.io/badge/plataforma-Windows-2563eb)
  ![Licença](https://img.shields.io/badge/licença-MIT-22c55e)
</div>

## Sobre o projeto

Criei o Automatech para reunir em um único aplicativo tarefas repetitivas que
normalmente exigem fórmulas, scripts ou várias etapas manuais. A proposta é
oferecer automações úteis para planilhas e arquivos sem exigir conhecimento de
programação de quem usa.

O processamento acontece localmente no computador. Os arquivos não são enviados
para serviços externos. As planilhas originais são preservadas e o organizador
apenas move arquivos para subpastas dentro da pasta escolhida.

## Funcionalidades

### Planilhas

- **Unir planilhas:** combina vários arquivos Excel com colunas compatíveis.
- **Separar planilha:** cria um arquivo para cada valor de uma coluna escolhida.
- **Limpar planilha:** remove vazios, duplicados e espaços extras, além de
  padronizar cabeçalhos.
- **Prévia dos dados:** exibe uma amostra antes de iniciar o processamento.

### Arquivos e produtividade

- **Organizador de arquivos:** distribui documentos em pastas por categoria.
- **Rotinas salvas:** restaura arquivos, destinos e opções usados com frequência.
- **Histórico:** registra resultados e oferece acesso rápido à pasta de saída.
- **Execução em segundo plano:** mantém a interface responsiva durante operações.

## Segurança dos dados

- Nenhuma automação sobrescreve arquivos existentes automaticamente.
- A limpeza sempre gera uma nova planilha e preserva o arquivo original.
- Conflitos de nomes recebem sufixos incrementais.
- Erros técnicos ficam nos logs locais; a interface mostra mensagens amigáveis.
- Configurações, rotinas e histórico ficam em `%LOCALAPPDATA%\Automatech`.

## Tecnologias

- Python 3.11+
- CustomTkinter e Pillow
- pandas e openpyxl
- PyInstaller

## Executar em desenvolvimento

```powershell
git clone https://github.com/rodeghierotech/automatech.git
cd automatech
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## Gerar o executável para Windows

Com o ambiente virtual ativado:

```powershell
python build.py
```

O resultado será criado em `dist/Automatech/Automatech.exe`. O script inclui os
recursos visuais e a configuração necessária para as dependências de planilhas.

## Estrutura

```text
Automatech/
├── main.py                    # ponto de entrada
├── build.py                   # empacotamento para Windows
├── config/                    # configurações persistentes
├── core/                      # módulos, tarefas em segundo plano e logs
├── services/                  # planilhas, arquivos, rotinas e histórico
├── modules/
│   ├── spreadsheets/          # unir, separar e limpar
│   └── files/                 # organização de arquivos
├── ui/
│   ├── components/            # componentes reutilizáveis
│   └── screens/               # telas do aplicativo
├── assets/                    # ícones e atribuições
└── tests/                     # testes dos serviços
```

A interface fica separada da lógica de manipulação de dados. Novas automações
podem ser registradas em `core/module_registry.py` sem alterar a tela inicial.

## Roadmap

- [x] Prévia antes da execução
- [x] Rotinas salvas
- [x] Histórico de execuções
- [ ] Comparação entre versões de planilhas
- [ ] Fila de processamentos
- [ ] Rotinas com várias etapas encadeadas

## Como contribuir

Sugestões, correções e novas automações são bem-vindas. Consulte o
[guia de contribuição](CONTRIBUTING.md) antes de abrir uma alteração. Falhas de
segurança devem seguir as orientações de [SECURITY.md](SECURITY.md).

## Autor

Desenvolvido por **Henrique Rodeghiero**.

- GitHub: [@rodeghierotech](https://github.com/rodeghierotech)

## Licença

Distribuído sob a [Licença MIT](LICENSE). Os ícones Lucide mantêm sua licença e
atribuição próprias em [`assets/icons/LICENSE.md`](assets/icons/LICENSE.md).
