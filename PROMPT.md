Quero adicionar um card compartilhável na tela de resultado do quiz. 



REGRAS IMPORTANTES:

\- Não altere nenhuma lógica existente do quiz, perguntas ou pontuação

\- Apenas adicione o card ABAIXO do resultado já existente

\- Analise o componente de resultado atual antes de mexer em qualquer coisa



O QUE IMPLEMENTAR:



1\. Instala a biblioteca: npm install html2canvas



2\. Cria um novo componente src/components/ShareCard.tsx com:

&#x20;  - Card 1080x1080px (formato Instagram) com fundo #f5f0ff

&#x20;  - Topo: "ME JULGA" à esquerda (letra pequena, roxo claro) + badge da categoria à direita (pill roxo claro)

&#x20;  - Seção do usuário: texto "A Dra. Julga analisou" (pequeno, uppercase) + campo com @ do usuário em destaque (grande, roxo escuro #2d1060)

&#x20;  - Divisor horizontal fino (#e2d4ff)

&#x20;  - Texto "e o veredicto é" (pequeno, uppercase) + "Sem defesa possível." em fonte grande bold (#2d1060)

&#x20;  - Citação em itálico com borda esquerda roxa — usar o texto do diagnóstico do resultado

&#x20;  - Rodapé: "E o seu? mejulga.com.br" à esquerda + "@dra.julga" à direita (ambos pequenos, roxo claro)



3\. Antes de mostrar o card, exibe um campo de texto opcional:

&#x20;  - Placeholder: "Seu @ do Instagram (opcional)"

&#x20;  - Campo simples, estilo do site

&#x20;  - Botão "Gerar card para compartilhar"



4\. Ao clicar no botão:

&#x20;  - Usa html2canvas para capturar o card como imagem PNG

&#x20;  - Faz download automático com nome "meu-julgamento-mejulga.png"



5\. O card deve receber como props: categoria, titulo do resultado, texto do diagnostico



6\. Adiciona o ShareCard no componente de resultado existente passando as props corretas



Mantenha o estilo visual roxo do site. Não use emojis no card.

