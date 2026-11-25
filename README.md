# YouTube Downloader

Aplicação full-stack que extrai áudio do YouTube com `yt-dlp` e FFmpeg. Cole um link para baixar um MP3 ou cole de dois a dez links, um por linha, para baixar todos os MP3 em um ZIP. Os arquivos são temporários.

> Use apenas vídeos que você criou ou que tem autorização para baixar. Respeite direitos autorais e os termos da plataforma. O projeto não contorna DRM, autenticação ou restrições de acesso.

## Tecnologias

- Frontend: Next.js (App Router), TypeScript, Tailwind CSS, shadcn/ui, React Hook Form, Zod e Lucide.
- Backend: Python 3.12+, FastAPI, Pydantic, yt-dlp, FFmpeg e Uvicorn.
- Testes: pytest e FastAPI TestClient.

## Pré-requisitos

- Node.js 20+ e npm.
- Python 3.12+.
- FFmpeg e FFprobe disponíveis no `PATH`.

Instale o FFmpeg conforme seu sistema:

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# macOS com Homebrew
brew install ffmpeg

# Windows com winget
winget install Gyan.FFmpeg
```

Confirme a instalação com `ffmpeg -version` e `ffprobe -version`.

## Backend

Dentro da pasta `backend`:

```bash
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

A API fica em <http://localhost:8000>, a documentação Swagger em <http://localhost:8000/docs> e o health check em <http://localhost:8000/health>.

O arquivo `.env` é opcional. As variáveis suportadas são:

| Variável | Padrão | Finalidade |
| --- | --- | --- |
| `FRONTEND_ORIGIN` | `http://localhost:3000` | Origem permitida no CORS |
| `PROCESSING_TIMEOUT_SECONDS` | `300` | Tempo máximo total da requisição |
| `SOCKET_TIMEOUT_SECONDS` | `30` | Timeout de rede do yt-dlp |
| `MAX_FILE_SIZE_MB` | `200` | Limite do arquivo de entrada e saída |

Exemplo de requisição:

```bash
curl -X POST http://localhost:8000/api/download \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://www.youtube.com/watch?v=VIDEO_ID","format":"mp3"}' \
  --output audio.mp3
```

## Frontend

Em outro terminal, dentro da pasta `frontend`:

```bash
cp .env.example .env.local
npm install
npm run dev
```

Abra <http://localhost:3000>. Para apontar o frontend para outra API, altere `NEXT_PUBLIC_API_URL` em `.env.local`.

## Testes e verificações

Os testes usam mocks e não baixam conteúdo real:

```bash
cd backend
source .venv/bin/activate
pytest -q

cd ../frontend
npm run lint
npm run typecheck
npm run build
```

## API e tratamento de erros

`POST /api/download/zip` aceita um objeto com a chave `urls` e uma lista de 2 a 10 URLs. O timeout e o limite de tamanho valem para o lote inteiro. Se algum link falhar, a API informa o item e descarta o ZIP parcial.

`POST /api/download` aceita apenas hosts oficiais `youtube.com`/`youtu.be` e o formato `mp3`. Playlists são desabilitadas. O processamento síncrono ocorre em uma thread separada para não bloquear o event loop.

- `400`: vídeo indisponível.
- `422`: URL ou formato inválido.
- `500`: FFmpeg ausente ou erro inesperado.
- `502`: falha de download/conversão.
- `504`: tempo de processamento excedido.

O nome retornado é sanitizado, o cliente nunca fornece caminhos de arquivo e a limpeza temporária é agendada como tarefa posterior ao envio. Se uma operação exceder o timeout mas a thread ainda estiver encerrando, o resultado tardio também é limpo.

## Limitações conhecidas

- O progresso exibido é indeterminado; não há progresso percentual.
- Não há histórico, autenticação, banco de dados ou armazenamento permanente.
- Downloads dependem da disponibilidade do vídeo, das regras do YouTube e da compatibilidade da versão instalada do yt-dlp.
- O limite de tamanho do yt-dlp é aplicado antes da conversão e novamente verificado no MP3 final.

