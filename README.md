# Extrator de Mídia para Windows 10 e 11

Interface simples para extrair áudio MP3 ou vídeo MP4 de links HTTPS do YouTube e TikTok, extrair áudio de arquivos locais e copiar faixas de CDs ou títulos de DVD/Blu-ray de mídia que você pode utilizar. A opção de discos requer uma unidade óptica compatível.

## Baixar o executável

Abra a aba **Actions** deste repositório, escolha a execução **Compilar Windows** e baixe o artefato **ExtratorDeMidia-Windows10-11**. Extraia o ZIP e abra `ExtratorDeMidia.exe`. O fluxo roda automaticamente após cada envio à branch `main`. O executável inclui FFmpeg e yt-dlp; o Windows pode mostrar um aviso por se tratar de um executável sem assinatura digital.

## Usar

1. Escolha **Link**, **Arquivo**, **CD de áudio** ou **DVD / Blu-ray**.
2. Cole o link, selecione o arquivo ou digite a letra da unidade, por exemplo `D`.
3. Escolha uma pasta existente e clique em **Iniciar extração**. O registro mostra o progresso e uma janela informa a conclusão.

Links são limitados a HTTPS de YouTube e TikTok. Alguns vídeos podem exigir autenticação ou impedir a extração. Atualize `yt-dlp` e gere um novo executável se o site mudar. A opção de vídeo tenta MP4, dependendo dos formatos disponibilizados pelo site. Não há remoção de proteções de conteúdo neste aplicativo.

**CD de áudio:** instale `cdda2wav.exe` compatível com Windows e coloque-o no `PATH`. O programa grava WAV e converte as novas faixas para MP3 usando o FFmpeg incluído; preserva os WAV originais.

**DVD / Blu-ray:** instale [MakeMKV](https://www.makemkv.com/) e coloque `makemkvcon.exe` no `PATH`. O resultado são arquivos MKV originais, independentemente do formato selecionado na interface. A disponibilidade e licença da ferramenta são responsabilidade da instalação local. O reconhecimento de unidades ópticas não foi testado em hardware Windows nesta sessão.

## Projetos originais

- [`lucasdksan/extract_audio_from_video`](https://github.com/lucasdksan/extract_audio_from_video), submódulo `upstream/extract_audio_from_video`: servidor Express para extrair áudio MP3 de vídeos enviados pelo usuário. Código original preservado, licença declarada ISC no `package.json`.
- [`automatic-ripping-machine/automatic-ripping-machine`](https://github.com/automatic-ripping-machine/automatic-ripping-machine), submódulo `upstream/automatic-ripping-machine`: automação de discos em Linux/Docker, licença MIT. Código original preservado para consulta e evolução. Seus serviços `udev` e `abcde` não são executáveis nativamente no Windows.

O aplicativo Windows usa integração própria com FFmpeg, yt-dlp, cdda2wav e MakeMKV para os recursos correspondentes. Os dois submódulos **não** são incorporados ao `.exe` nem são apresentados como compatíveis com Windows. Para baixar o código completo, use `git clone --recurse-submodules`.

## Desenvolvimento

`python -m pip install yt-dlp` e `python app.py`. Para arquivo local, adicione FFmpeg ao `PATH`; para discos, instale as ferramentas indicadas acima. O build de Windows é definido em `.github/workflows/windows.yml`.
