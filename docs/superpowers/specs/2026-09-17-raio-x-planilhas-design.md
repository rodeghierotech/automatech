# Raio-X de planilhas e relatório de transformação

**Data:** 17 de setembro de 2026  
**Status:** aprovado para especificação  
**Escopo:** estabilizar a abertura de “Limpar planilha” e adicionar diagnóstico, comparação antes/depois e relatório HTML ao fluxo de limpeza.

## Objetivo

Transformar a limpeza de planilhas em um fluxo explicável e seguro. Antes de executar, o usuário deve entender os problemas encontrados e o efeito estimado das opções escolhidas. Depois da execução, deve receber a nova planilha e um relatório local que registre o que mudou.

O primeiro uso do Raio-X ficará dentro de “Limpar planilha”, mas a análise será implementada como serviço independente para poder atender futuramente “Unir planilhas” e as Receitas Automatech.

## Limites do primeiro marco

O primeiro marco inclui:

- reprodução e correção da falha que impede a abertura da tela de limpeza;
- diagnóstico de arquivos `.xlsx`;
- resumo geral e métricas por coluna;
- estimativa do resultado conforme as opções de limpeza selecionadas;
- integração do diagnóstico à tela de limpeza;
- relatório HTML gerado após uma limpeza concluída;
- acesso ao relatório pelo histórico;
- testes de serviço e verificação manual do fluxo no Windows.

O primeiro marco não inclui:

- editor visual de receitas;
- monitoramento automático de pastas;
- inteligência artificial ou serviços externos;
- alteração automática de tipos, datas ou valores;
- gráficos estatísticos avançados;
- suporte a `.xls`, CSV ou múltiplas abas.

## Decisões de produto

### Diagnóstico orientado à decisão

O Raio-X deve responder a três perguntas:

1. Qual é o tamanho e a estrutura da planilha?
2. Quais problemas objetivos foram encontrados?
3. O que as opções atuais de limpeza devem alterar?

O diagnóstico não deve marcar diferenças legítimas como erro. Valores distintos e tipos encontrados são informações; vazios, duplicados, espaços externos e cabeçalhos vazios ou repetidos são alertas objetivos.

### Processamento local e privacidade

Nenhum dado será enviado para serviços externos. O relatório não incluirá linhas completas nem amostras de valores. Ele poderá registrar nomes de colunas e métricas agregadas, reduzindo a exposição de conteúdo sensível.

### Relatório como evidência

O relatório será um arquivo HTML autônomo criado ao lado da planilha limpa. Ele terá identidade visual do Automatech, poderá ser aberto no navegador sem servidor e conterá:

- arquivo de origem e arquivo gerado;
- data e horário;
- opções aplicadas;
- quantidade de linhas e colunas antes e depois;
- duplicados removidos;
- linhas e colunas vazias removidas;
- campos de texto ajustados;
- cabeçalhos padronizados;
- tabela de métricas por coluna.

Não será criado PDF neste marco, evitando uma dependência adicional apenas para apresentação.

## Arquitetura

### Serviço de diagnóstico

Será criado `services/spreadsheet_profile_service.py`. O serviço não conhecerá CustomTkinter e oferecerá estruturas de dados explícitas:

- `ColumnProfile`: nome, tipo predominante, vazios, valores distintos e quantidade de textos com espaços externos;
- `SpreadsheetProfile`: caminho, linhas, colunas, duplicados, linhas vazias, colunas vazias e perfis das colunas;
- `CleaningPreview`: perfil original, métricas estimadas do resultado e contadores das transformações;
- `CleaningResult`: métricas finais, caminho da planilha e caminho do relatório.

As estruturas serão `dataclasses` para manter o contrato legível e testável.

### Motor único de transformação

A lógica atual de `clean_spreadsheet()` será dividida em duas camadas:

1. uma função interna que recebe um `DataFrame`, aplica as opções e retorna o novo `DataFrame` com métricas;
2. a função pública que lê o arquivo, usa o motor, grava a saída e retorna o resultado.

O Raio-X usará o mesmo motor sobre uma cópia em memória para calcular a estimativa. Assim, a prévia e a execução não terão regras duplicadas.

A execução continuará relendo o arquivo de origem. Se ele tiver sido alterado depois do diagnóstico, o resultado final continuará correto e o relatório usará as métricas efetivamente produzidas na execução.

### Geração do relatório

Será criado `services/report_service.py`, usando apenas a biblioteca padrão. O HTML será produzido com conteúdo escapado por `html.escape`, codificação UTF-8 e CSS incorporado.

O arquivo seguirá o nome da saída, por exemplo:

```text
clientes_limpo.xlsx
clientes_limpo_relatorio.html
```

O caminho deverá passar por `unique_path()` para não sobrescrever relatório existente. Se a planilha for gerada e a criação do relatório falhar, a operação será registrada como concluída com aviso: a falha do artefato complementar não apagará nem invalidará a planilha.

### Histórico compatível

`record_execution()` receberá um novo argumento opcional `report_path`. Entradas novas poderão ter a chave `report_path`; entradas antigas continuarão válidas porque a leitura atual aceita dicionários sem esquema rígido.

A tela de histórico exibirá “Abrir relatório” somente quando o caminho existir. “Abrir pasta” continuará usando `output_path`.

### Interface

A tela “Limpar planilha” será reorganizada em uma área rolável para manter funcionamento na altura mínima atual. Após escolher o arquivo:

1. o botão de execução ficará indisponível;
2. o status mostrará “Analisando planilha…”;
3. o diagnóstico rodará por `run_in_background()`;
4. a tela mostrará resumo geral, alertas e métricas compactas;
5. o botão será liberado quando o diagnóstico terminar.

As opções de limpeza continuarão editáveis. Alterações nelas marcarão a estimativa como desatualizada e solicitarão uma nova análise antes da confirmação. Para evitar várias threads simultâneas, a tela manterá um identificador da solicitação mais recente e ignorará resultados antigos.

O quadro principal mostrará, no máximo:

- linhas, colunas e duplicados;
- total de células vazias;
- total de textos com espaços externos;
- estimativa de linhas e colunas após a limpeza;
- tabela rolável das colunas.

O diálogo de confirmação usará o resumo do Raio-X no lugar da amostra textual atual.

## Fluxo de dados

```text
Usuário seleciona .xlsx
        ↓
Validação de caminho e leitura em segundo plano
        ↓
Perfil original + simulação com opções atuais
        ↓
Resumo exibido na tela
        ↓
Usuário confirma
        ↓
Arquivo é relido e a limpeza é executada
        ↓
Planilha nova é gravada com proteção contra sobrescrita
        ↓
Relatório HTML é gerado
        ↓
Histórico registra resumo, saída e relatório
```

## Diagnóstico da tela que não abre

A implementação começará reproduzindo a navegação para `clean_spreadsheet` na versão de desenvolvimento. A causa deverá ser registrada antes da correção. Serão verificados:

- importação e instanciação de `CleanSpreadsheetModule`;
- criação de `CleanSpreadsheetScreen`;
- carregamento do ícone `brush-cleaning`;
- exceções emitidas pela navegação;
- conteúdo do log em `%LOCALAPPDATA%\Automatech\logs`.

Nenhuma correção será presumida a partir da leitura estática. Se a tela já abrir no código atual, isso será documentado como não reproduzido e o fluxo seguirá com a integração do Raio-X.

## Erros e recuperação

- Arquivo inválido, vazio ou corrompido: mensagem amigável na tela e detalhe técnico no log.
- Arquivo alterado ou removido antes da execução: nova validação na execução.
- Análise antiga concluída depois de uma análise nova: resultado antigo ignorado.
- Falha ao gravar a planilha: remoção de arquivo parcial conforme a proteção existente.
- Falha ao gerar o relatório: planilha preservada, aviso ao usuário e registro sem `report_path`.
- Falha ao salvar histórico: não transforma uma limpeza concluída em erro.
- Tela fechada durante a análise: o mecanismo existente descarta atualizações para widgets destruídos.

## Verificação

### Testes automatizados

Serão adicionados testes para:

- contagem de vazios, duplicados e valores distintos;
- identificação de espaços externos em texto;
- cabeçalhos vazios e repetidos;
- consistência entre estimativa e limpeza executada;
- opções desativadas sem alteração indevida;
- relatório com métricas esperadas;
- escape de nomes de arquivos e colunas no HTML;
- nome único para relatórios existentes;
- leitura de entradas antigas do histórico sem `report_path`;
- persistência e leitura de `report_path` em entradas novas.

### Verificação no aplicativo

No Windows, será verificado:

- abertura da tela “Limpar planilha”;
- seleção de planilha válida e inválida;
- estado de análise sem travamento da janela;
- atualização do Raio-X quando as opções mudam;
- confirmação e execução;
- abertura da pasta e do relatório;
- acesso ao relatório pela tela de histórico;
- comportamento na altura mínima da janela.

### Compatibilidade do executável

Depois dos testes e da verificação em desenvolvimento, será executado o build existente com PyInstaller e verificada a abertura do executável gerado. O novo relatório usa apenas biblioteca padrão e não exige nova dependência de empacotamento.

## Sequência de entrega

1. Reproduzir e documentar a falha de abertura.
2. Adicionar testes do perfil e do motor compartilhado.
3. Extrair o motor de limpeza sem alterar o comportamento atual.
4. Implementar perfil e simulação.
5. Implementar relatório HTML.
6. Ampliar histórico de forma compatível.
7. Integrar o Raio-X à tela de limpeza.
8. Executar testes, verificação manual e build.
9. Atualizar README, versão e imagens de portfólio somente após o fluxo estar validado.

## Critérios de aceite

O marco estará concluído quando:

- a tela de limpeza abrir de forma reproduzível no desenvolvimento e no executável;
- o Raio-X aparecer sem bloquear a interface;
- a estimativa usar as mesmas regras da execução;
- o arquivo original permanecer intocado;
- a planilha limpa e o relatório forem gerados com nomes sem conflito;
- o histórico oferecer acesso ao relatório quando disponível;
- erros técnicos forem registrados sem expor traceback na interface;
- os testes definidos passarem;
- o fluxo completo for verificado no aplicativo Windows.
