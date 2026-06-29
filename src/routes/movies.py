from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy import func

from database import get_db
from database.models import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel,
)
from schemas.movies import (
    MovieListResponseSchema,
    MovieCreateSchema,
    MovieDetailSchema,
    MovieUpdateSchema,
    MessageResponse,
)

router = APIRouter(prefix="/movies", tags=["Movies"])


@router.get("/", response_model=MovieListResponseSchema)
async def get_movies(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
):
    total_items_query = select(func.count(MovieModel.id))
    total_items_result = await db.execute(total_items_query)
    total_items = total_items_result.scalar() or 0

    if total_items == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No movies found."
        )

    total_pages = (total_items + per_page - 1) // per_page

    if page > total_pages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No movies found."
        )

    offset = (page - 1) * per_page
    movies_query = (
        select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page)
    )

    movies_result = await db.execute(movies_query)
    movies = movies_result.scalars().all()

    prev_page = (
        f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    )
    next_page = (
        f"/theater/movies/?page={page + 1}&per_page={per_page}"
        if page < total_pages
        else None
    )

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post("/", response_model=MovieDetailSchema, status_code=status.HTTP_201_CREATED)
async def create_movie(payload: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    duplicate_query = select(MovieModel).where(
        MovieModel.name == payload.name, MovieModel.date == payload.date
    )
    duplicate_result = await db.execute(duplicate_query)
    if duplicate_result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A movie with the name '{payload.name}' and release date '{payload.date}' already exists.",
        )

    country_query = select(CountryModel).where(CountryModel.code == payload.country)
    country_result = await db.execute(country_query)
    country = country_result.scalars().first()
    if not country:
        country = CountryModel(code=payload.country, name=None)
        db.add(country)
        await db.flush()

    genres = []
    for genre_name in payload.genres:
        g_query = select(GenreModel).where(GenreModel.name == genre_name)
        g_res = await db.execute(g_query)
        genre = g_res.scalars().first()
        if not genre:
            genre = GenreModel(name=genre_name)
            db.add(genre)
        genres.append(genre)

    actors = []
    for actor_name in payload.actors:
        a_query = select(ActorModel).where(ActorModel.name == actor_name)
        a_res = await db.execute(a_query)
        actor = a_res.scalars().first()
        if not actor:
            actor = ActorModel(name=actor_name)
            db.add(actor)
        actors.append(actor)

    languages = []
    for lang_name in payload.languages:
        l_query = select(LanguageModel).where(LanguageModel.name == lang_name)
        l_res = await db.execute(l_query)
        lang = l_res.scalars().first()
        if not lang:
            lang = LanguageModel(name=lang_name)
            db.add(lang)
        languages.append(lang)

    await db.flush()

    new_movie = MovieModel(
        name=payload.name,
        date=payload.date,
        score=payload.score,
        overview=payload.overview,
        status=payload.status,
        budget=payload.budget,
        revenue=payload.revenue,
        country_id=country.id,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    db.add(new_movie)
    await db.commit()

    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == new_movie.id)
    )
    final_res = await db.execute(stmt)
    return final_res.scalars().first()


@router.get("/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie_details(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            selectinload(MovieModel.genres),
            selectinload(MovieModel.actors),
            selectinload(MovieModel.languages),
        )
        .where(MovieModel.id == movie_id)
    )
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )
    return movie


@router.delete("/{movie_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    await db.delete(movie)
    await db.commit()


@router.patch("/{movie_id}/", response_model=MessageResponse)
async def update_movie(
    movie_id: int, payload: MovieUpdateSchema, db: AsyncSession = Depends(get_db)
):
    stmt = select(MovieModel).where(MovieModel.id == movie_id)
    result = await db.execute(stmt)
    movie = result.scalars().first()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie with the given ID was not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data and payload.__fields_set__:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input data."
        )

    for key, value in update_data.items():
        setattr(movie, key, value)

    await db.commit()
    return {"detail": "Movie updated successfully."}
