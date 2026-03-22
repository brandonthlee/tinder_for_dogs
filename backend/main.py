import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select

from database import create_db, get_session
from models import Dog, Like, Match
from pixelate import pixelate

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="Tinder for Dogs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/images", StaticFiles(directory="uploads"), name="images")


@app.on_event("startup")
def on_startup():
    create_db()


def generate_pixel_art(dog_id: int, input_path: str, output_path: str):
    pixelate(input_path, output_path)
    # Update DB once pixel art is ready
    from database import engine
    from sqlmodel import Session
    with Session(engine) as session:
        dog = session.get(Dog, dog_id)
        if dog:
            dog.pixel_photo_path = output_path
            session.add(dog)
            session.commit()


@app.post("/dogs/register", response_model=Dog)
async def register_dog(
    background_tasks: BackgroundTasks,
    name: str = Form(...),
    breed: str = Form(...),
    age: int = Form(...),
    bio: str = Form(...),
    owner_name: str = Form(...),
    photo: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    # Save uploaded photo
    ext = Path(photo.filename).suffix or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    photo_path = str(UPLOAD_DIR / filename)

    with open(photo_path, "wb") as f:
        f.write(await photo.read())

    # Create dog record
    dog = Dog(
        name=name,
        breed=breed,
        age=age,
        bio=bio,
        owner_name=owner_name,
        photo_path=photo_path,
    )
    session.add(dog)
    session.commit()
    session.refresh(dog)

    # Generate pixel art in background
    pixel_filename = f"pixel_{dog.id}_{uuid.uuid4().hex}.png"
    pixel_path = str(UPLOAD_DIR / pixel_filename)
    background_tasks.add_task(generate_pixel_art, dog.id, photo_path, pixel_path)

    return dog


@app.get("/dogs/{dog_id}", response_model=Dog)
def get_dog(dog_id: int, session: Session = Depends(get_session)):
    dog = session.get(Dog, dog_id)
    if not dog:
        raise HTTPException(status_code=404, detail="Dog not found")
    return dog


@app.get("/dogs/feed/{dog_id}")
def get_feed(dog_id: int, limit: int = 10, session: Session = Depends(get_session)):
    # Get IDs this dog has already liked
    liked = session.exec(
        select(Like.liked_dog_id).where(Like.liker_dog_id == dog_id)
    ).all()
    excluded = set(liked) | {dog_id}

    dogs = session.exec(select(Dog)).all()
    feed = [d for d in dogs if d.id not in excluded][:limit]
    return feed


@app.post("/dogs/{dog_id}/like/{target_id}")
def like_dog(dog_id: int, target_id: int, session: Session = Depends(get_session)):
    # Record the like
    like = Like(liker_dog_id=dog_id, liked_dog_id=target_id)
    session.add(like)
    session.commit()

    # Check for mutual like (match)
    mutual = session.exec(
        select(Like).where(Like.liker_dog_id == target_id, Like.liked_dog_id == dog_id)
    ).first()

    if mutual:
        match = Match(dog_a_id=dog_id, dog_b_id=target_id)
        session.add(match)
        session.commit()
        return {"matched": True}

    return {"matched": False}


@app.get("/dogs/{dog_id}/matches")
def get_matches(dog_id: int, session: Session = Depends(get_session)):
    matches = session.exec(
        select(Match).where(
            (Match.dog_a_id == dog_id) | (Match.dog_b_id == dog_id)
        )
    ).all()

    result = []
    for m in matches:
        other_id = m.dog_b_id if m.dog_a_id == dog_id else m.dog_a_id
        other = session.get(Dog, other_id)
        if other:
            result.append(other)
    return result
