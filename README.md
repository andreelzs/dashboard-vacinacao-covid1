# Vacinação contra COVID-19 e internações por município

Trabalho G1 de Linguagens de Programação (Prof. Alexandre Louzada).
Aluno: André Luiz dos Santos Ferreira.

Análise de uma base simulada com 8 municípios do Sudeste (2021 a 2024) para verificar se municípios e anos com maior cobertura vacinal tiveram menos internações por COVID-19. A base vem do repositório [Dados-Simulados](https://github.com/AlexandreLouzada/Dados-Simulados).

## Principais resultados

- Com todos os registros a correlação entre cobertura e internações é fraca (Pearson −0,13).
- Sem os 7 registros com cobertura acima de 100%, ela é moderada (Pearson −0,36 e Spearman −0,45).
- 2022 teve a maior cobertura média e as internações caíram cerca de 30% em relação a 2021.
- Vitória e Serra vão no sentido contrário da hipótese.
- A base é simulada e tem 32 observações, então o resultado não prova causa e efeito.

## Estrutura

- `notebooks/analise_vacinacao_covid.ipynb`: notebook com a análise completa
- `app.py`: dashboard em Streamlit
- `index.html`: página do GitHub Pages
- `data/`: cópia da base, usada se o GitHub do professor estiver fora do ar
- `requirements.txt`: bibliotecas do dashboard

## Tecnologias

Python, Pandas, NumPy, Matplotlib, Seaborn, Plotly, Streamlit e GitHub Pages.

## Rodar o dashboard no computador

```
pip install -r requirements.txt
streamlit run app.py
```
