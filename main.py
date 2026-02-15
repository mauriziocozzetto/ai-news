import requests
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator
from typing import List
import pprint

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- CONFIGURAZIONE ---
NEWS_API_KEY = '04cb13f97f074b37b87434b9a0d79c48'
BASE_URL = 'https://newsapi.org/v2/everything'
DEFAULT_IMAGE = "https://placehold.co/400x200?text=Immagine+Non+Disponibile"

# --- FUNZIONE HELPER ---


def use_default_if_empty(value, default):
    """Ritorna il default se il valore è None, vuoto o solo spazi"""
    if value is None:
        return default
    if isinstance(value, str) and not value.strip():
        return default
    return value.strip() if isinstance(value, str) else value

# --- MODELLO DATI PYDANTIC ---


class Article(BaseModel):
    title: str = Field(default="Titolo non disponibile")
    description: str = Field(default="Nessuna descrizione disponibile")
    author: str = Field(default="Autore sconosciuto")
    url: str = Field(default="#")
    urlToImage: str = Field(default=DEFAULT_IMAGE)
    source_name: str = Field(default="Fonte non specificata")

    @field_validator('*', mode='before')
    @classmethod
    def use_defaults(cls, v, info):
        """Applica automaticamente i default per TUTTI i campi se vuoti"""
        defaults = cls.model_fields[info.field_name].default
        return use_default_if_empty(v, defaults)


# --- LOGICA DI RECUPERO DATI ---


def fetch_news(query: str, page: int = 1) -> List[Article]:
    """Recupera le notizie dalla News API e le valida con Pydantic"""
    params = {
        'q': query,
        'language': 'it',
        'pageSize': 9,
        'page': page,
        'apiKey': NEWS_API_KEY
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=5)
        response.raise_for_status()

        data = response.json()
        pprint.pprint(data)
        raw_articles = data.get('articles', [])

        articles = []
        for a in raw_articles:
            try:
                articles.append(Article(
                    title=a.get('title'),
                    description=a.get('description'),
                    author=a.get('author'),
                    url=a.get('url'),
                    urlToImage=a.get('urlToImage'),
                    source_name=a.get('source', {}).get('name')
                ))
            except Exception:
                continue

        return articles

    except Exception:
        return []


# --- ROTTE ---


@app.get("/", response_class=HTMLResponse)
def index(request: Request, query: str = "tecnologia", page: int = 1):
    """Pagina principale con lista delle notizie"""
    current_page = max(1, page)
    news_list = fetch_news(query, page=current_page)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "articles": news_list,
        "query": query,
        "page": current_page
    })
