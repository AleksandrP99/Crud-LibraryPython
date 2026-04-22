"""
Books API with FastAPI and SQLite
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
from contextlib import asynccontextmanager

DATABASE_NAME = 'books.db'


class Book(BaseModel):
    id: Optional[int] = None
    title: str
    author: str
    year: Optional[int] = None


def get_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            year INTEGER
        )
    ''')
    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_table()
    yield


app = FastAPI(
    title="Books API",
    description="CRUD operations for books with FastAPI and SQLite",
    version="1.0.0",
    lifespan=lifespan
)


@app.post("/books/", response_model=dict, status_code=201)
def create_book(book: Book):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO books (title, author, year) VALUES (?, ?, ?)",
            (book.title, book.author, book.year)
        )
        conn.commit()
        book.id = cursor.lastrowid
        return {"message": "Book added successfully", "book": book.dict()}
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.get("/books/", response_model=List[Book])
def list_books():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books ORDER BY title")
    books = cursor.fetchall()
    conn.close()
    return [Book(id=row["id"], title=row["title"], author=row["author"], year=row["year"]) for row in books]


@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return Book(id=row["id"], title=row["title"], author=row["author"], year=row["year"])
    else:
        raise HTTPException(status_code=404, detail="Book not found")


@app.put("/books/{book_id}", response_model=dict)
def update_book(book_id: int, book: Book):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Book not found")
    try:
        cursor.execute(
            "UPDATE books SET title = ?, author = ?, year = ? WHERE id = ?",
            (book.title, book.author, book.year, book_id)
        )
        conn.commit()
        book.id = book_id
        return {"message": "Book updated successfully", "book": book.dict()}
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.delete("/books/{book_id}", response_model=dict)
def delete_book(book_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Book not found")
    try:
        cursor.execute("DELETE FROM books WHERE id = ?", (book_id,))
        conn.commit()
        return {"message": "Book deleted successfully"}
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("__main__:app", host="127.0.0.1", port=8000, reload=True)