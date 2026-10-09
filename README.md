# In Vasmer We Trust — указатель

Самообновляемый сайт-указатель к телеграм-каналу
[@ethimologie](https://t.me/ethimologie): словарь разобранных слов, индекс
праиндоевропейских корней и навигация по сюжетным сериям.

**Сайт:** https://aleskunder.github.io/in-vasmer-we-trust/
**Текст закреплённого поста:** [`PINNED.md`](PINNED.md)

## Как это работает

Раз в сутки GitHub Action читает публичный веб-фид канала
(`t.me/s/ethimologie`), дописывает новые посты в архив, прогоняет по ним
эвристику заголовочных слов и пересобирает сайт. Ничего делать руками не нужно:
вышел пост — через сутки он на сайте.

```
scripts/seed_from_export.py   разово: Telegram-экспорт -> data/posts.json
scripts/scrape.py             инкрементально: новые посты из фида канала
scripts/extract.py            эвристика -> data/entries.auto.yml
scripts/build.py              data/* -> site/
```

## Данные

| файл | что это | кто правит |
|---|---|---|
| `data/posts.json` | архив всех постов канала | скрейпер |
| `data/entries.yml` | **курируемый словарь** — слово, глосса, пост, корень | ты |
| `data/entries.auto.yml` | авто-кандидаты из новых постов | скрипт, перезаписывается |
| `data/roots.yml` | праиндоевропейские корни и их глоссы | ты |
| `data/series.yml` | серии постов | ты |
| `data/quizzes.yml` | интерактивы: опрос, разбор, слова, ответ | ты |

Курируемое всегда перекрывает автоматическое. Чтобы «узаконить» авто-статью,
перенеси её строку из `entries.auto.yml` в `entries.yml` — и из авто-файла она
пропадёт при следующем прогоне. Авто-статьи на сайте помечены значком «авто».

Правильные ответы интерактивов лежат в `data/quizzes.yml` в поле `answer`,
но на сайте пока не показываются — если захочешь играбельный архив,
это несколько строк в `build.py`.

## Локально

```bash
export MAMBA_EXE=~/micromamba_folder/micromamba
export MAMBA_ROOT_PREFIX=~/micromamba
$MAMBA_EXE create -n in-vasmer-we-trust -c conda-forge python=3.12 requests pyyaml -y

~/micromamba/envs/in-vasmer-we-trust/bin/python scripts/scrape.py
~/micromamba/envs/in-vasmer-we-trust/bin/python scripts/extract.py
~/micromamba/envs/in-vasmer-we-trust/bin/python scripts/build.py
cd site && python -m http.server 8000
```

`scripts/scrape.py --full` перечитывает весь архив канала с нуля.
