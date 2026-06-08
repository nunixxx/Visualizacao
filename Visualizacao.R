library(tidyverse)

dados <- read.csv(
  "dee-5266.csv",
  fileEncoding = "latin1",
  check.names = FALSE
)

dados_long <- dados %>%
  pivot_longer(
    cols = contains("Total"),
    names_to = "ano",
    values_to = "populacao"
  ) %>%
  mutate(
    ano = str_extract(ano, "\\d{4}") |> as.numeric()
  )

ggplot(
  dados_long,
  aes(
    x = ano,
    y = reorder(Município, populacao, median),
    fill = populacao
  )
) +
  geom_tile() +
  scale_fill_viridis_c() +
  theme_minimal() +
  labs(
    title = "Evolução populacional dos municípios"
  )