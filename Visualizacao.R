library(tidyverse)

dados <- read.csv("dee-5266.csv", fileEncoding = "latin1", check.names = FALSE)

# Calcular variação percentual 2000→2024
dados_var <- dados %>%
  mutate(
    pop2000 = `...Total 2000 (-)`,
    pop2024 = `...Total 2024 (-)`,
    variacao_pct = (pop2024 - pop2000) / pop2000 * 100,
    categoria = case_when(
      variacao_pct >  30 ~ "Boom (>30%)",
      variacao_pct >   0 ~ "Crescimento",
      variacao_pct >= -10 ~ "Declínio leve",
      TRUE               ~ "Esvaziamento (>-10%)"
    )
  ) %>%
  arrange(variacao_pct) %>%
  slice(c(1:15, (n()-14):n()))  # top e bottom 15

ggplot(dados_var, aes(
  x = variacao_pct,
  y = reorder(Município, variacao_pct),
  fill = categoria
)) +
  geom_col() +
  scale_fill_manual(values = c(
    "Boom (>30%)"        = "#1D9E75",
    "Crescimento"        = "#9FE1CB",
    "Declínio leve"      = "#F0997B",
    "Esvaziamento (>-10%)" = "#D85A30"
  )) +
  labs(
    title = "Municípios que mais cresceram e mais encolheram no RS (2000–2024)",
    x = "Variação populacional (%)",
    y = NULL,
    fill = NULL,
    caption = "Fonte: RIPSA/IBGE. Municípios litorâneos e da Serra lideraram o crescimento;\npequenos municípios rurais enfrentaram forte êxodo."
  ) +
  theme_minimal(base_size = 11) +
  theme(legend.position = "bottom")
