from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from app.config import settings

router = APIRouter(tags=["dev"], include_in_schema=False)

TESTING_UI_HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Chess Testing UI</title>
  <style>
    body { font-family: sans-serif; padding: 2rem; }
    #board { display: grid; grid-template-columns: repeat(8, 64px);
             grid-template-rows: repeat(8, 64px); }
    .sq { width: 64px; height: 64px; display: flex;
          align-items: center; justify-content: center; font-size: 40px; }
    .light { background: #f0d9b5; }
    .dark  { background: #b58863; }
    #status { margin-top: 1rem; }
  </style>
</head>
<body>
  <h1>Chess Testing UI</h1>
  <div id="board"></div>
  <div id="status">placeholder — engine not wired yet</div>
  <script>
    const board = document.getElementById('board');
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const sq = document.createElement('div');
        sq.className = 'sq ' + ((r + c) % 2 === 0 ? 'light' : 'dark');
        board.appendChild(sq);
      }
    }
  </script>
</body>
</html>"""


@router.get("/api/dev/testing-ui", response_class=HTMLResponse)
async def testing_ui() -> HTMLResponse:
    if settings.environment == "production":
        raise HTTPException(status_code=404)
    return HTMLResponse(TESTING_UI_HTML)