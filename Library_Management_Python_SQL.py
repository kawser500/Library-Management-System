import datetime
import sqlite3
import uuid
import os

intro = """
Welcome to the Library Management System!

This new digital system will allow efficient and streamlined management of your library!

You can do the following actions using this system:
        - Add a new user to the library database (type "add new user")
        - Add a new book (type "add book")
        - Checkout a book from the library database (type "checkout book")
        - Return a book to the library database (type "return book")
        - View a user's info (type "view user")
        - Check late fines on a user's system (type "late fines")

If you have any issues, please do not hesitate to contact us!

        """

print(intro)

db = sqlite3.connect(r"C:\Users\messi\Documents\Bootcamp - Python\Portfolio\books_db.sqlite", detect_types=sqlite3.PARSE_DECLTYPES)
print("Connection Established!")

cursor = db.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
    isbn TEXT PRIMARY KEY,
    title TEXT NOT NULL UNIQUE,
    author TEXT NOT NULL,
    copies INTEGER NOT NULL,
    genre TEXT
);
               """)

cursor.execute("""
    CREATE TABLE IF NOT EXISTS user (
    id TEXT PRIMARY KEY,
    full_name TEXT,
    books TEXT,
    fines FLOAT           
);
                """)

cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY,
    user_id TEXT,
    book_isbn TEXT,
    checkout_date TEXT,
    return_date TEXT,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (book_isbn) REFERENCES books(isbn)
)
""")

db.commit()

def insert_book():
    # Function to insert a new book into the database
    isbn = input("Please enter the ISBN of the book: ").replace("-", "")  # Remove dashes
    title = input("Please enter the title of the book: ")
    author = input("Please enter the book author name: ")
    genre = input("Please enter the genre of the book: ")

    try:
        copies = int(input("Please enter the number of copies of the book: "))
    except ValueError:
        print("Error: Copies must be an integer.")
        return

    query = """
        INSERT INTO books(isbn, title, author, genre, copies)
        VALUES (?, ?, ?, ?, ?);
    """
    values = (isbn, title, author, genre, copies)

    try:
        cursor.execute(query, values)
        db.commit()
        print(f"The book {title} has been added")

    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            print(f"Error: A book with title '{title}' already exists.")
        else:
            print(f"Error: {e}")

        db.rollback()


def add_user():
    # Function to add a new user to the database

    user_id = str(uuid.uuid4())  # Convert UUID to string
    full_name = input("Please enter the user's full name: ").title()

    cursor.execute("""
                   INSERT INTO user (id, full_name) 
                   VALUES (?,?)""", (user_id, full_name))

    db.commit()
    print(f"The user {full_name} with unique ID {user_id} has been added!")


def checkout_book():
    # Function to checkout a book from the database

    user_id = input("Please enter the user ID: ")
    book_isbn = input("Please enter the book's ISBN: ")
    checkout_date = datetime.date.today()
    checkout_date = checkout_date.strftime("%Y-%m-%d")

    cursor.execute("""
                   INSERT INTO transactions (user_id, book_isbn, checkout_date) 
                   VALUES (?, ?, ?)""", (user_id, book_isbn, checkout_date))

    cursor.execute("""
                   UPDATE books 
                   SET copies = copies - 1 WHERE isbn = ?""", (book_isbn,))

    # Retrieve book title
    cursor.execute("SELECT title FROM books WHERE isbn = ?", (book_isbn,))
    book_title = cursor.fetchone()[0]  # Assuming there is always a result

    cursor.execute("""
                   UPDATE user 
                   SET books = COALESCE(books, '') || ? 
                   WHERE id = ?""", (book_title + ', ', user_id))

    db.commit()

    print(f"The book with ISBN {book_isbn} ({book_title}) has been checked out by user ID {user_id} on {checkout_date}")

def return_book():
    # Function to return a book to the library database
    user_id = input("Please enter user ID: ")
    book_isbn = input("Please enter the book's ISBN: ")
    return_date = datetime.date.today()

    cursor.execute("""
                   UPDATE transactions SET return_date = ? 
                   WHERE user_id = ? 
                   AND book_isbn = ? 
                   AND return_date IS NULL""", (return_date, user_id, book_isbn))

    cursor.execute("""
                   UPDATE books 
                   SET copies = copies + 1 WHERE isbn = ?""", (book_isbn,))

    # Retrieve book title
    cursor.execute("SELECT title FROM books WHERE isbn = ?", (book_isbn,))
    book_title = cursor.fetchone()[0]  # Assuming there is always a result

    cursor.execute("""
                   UPDATE user 
                   SET books = REPLACE(books, ? || ', ', '') 
                   WHERE id = ?""", (book_title, user_id))

    db.commit()

    print(f"The book with ISBN {book_isbn} ({book_title}) has been returned by user ID {user_id} on {return_date}")


def calculate_fine(checkout_date):
    # Function to calculate a fine for a late book return

    current_date = datetime.date.today()
    days_difference = (current_date - checkout_date).days

    if days_difference > 30:
        fine_rate = 1
        fine_amount = fine_rate * (days_difference - 30)
        return fine_amount
    else:
        return 0


def late_fine(user_id, book_isbn):
    cursor.execute("""
                   SELECT checkout_date FROM transactions 
                   WHERE user_id = ? 
                   AND book_isbn = ? 
                   AND return_date IS NOT NULL""", (user_id, book_isbn))

    result = cursor.fetchone()

    if result:
        checkout_date = datetime.datetime.strptime(result[0], "%Y-%m-%d").date()
        fine_amount = calculate_fine(checkout_date)
        print(f"The late return fine is {fine_amount}.")
    else:
        return 0


def view_user_info(user_id):
    # Function to view user's info

    cursor.execute("""
        SELECT u.full_name, b.title, t.checkout_date, t.return_date
        FROM user u
        LEFT JOIN transactions t ON u.id = t.user_id
        LEFT JOIN books b ON t.book_isbn = b.isbn
        WHERE u.id = ?
    """, (user_id,))
    result = cursor.fetchall()

    if result:
        for row in result:
            user_name = row[0]
            book_title = row[1] if len(row) > 1 else "N/A"
            checkout_date = row[2] if len(row) > 2 else "N/A"
            return_date = row[3] if len(row) > 3 else "N/A"
            print(f"User: {user_name}, Book: {book_title}, Checkout Date: {checkout_date}, Return Date: {return_date}")
    else:
        print("User not found or has no transactions.")



while True:

    action = input("Please type an action from the above options or type 'exit': ").lower()

    if action == "exit":
        print("Goodbye!")
        break

    elif action == "add new user":
        add_user()

    elif action == "checkout book":
        checkout_book()

    elif action == "return book":
        return_book()

    elif action == "add book":
        insert_book()

    elif action == "view user":
        user_id = input("Please enter the user's ID: ")
        view_user_info(user_id)
    
    elif action == "late fines":
        user_id = input("Please enter the User ID: ")
        book_isbn = input("Please enter the book ISBN: ")
        late_fine(user_id, book_isbn)

    else:
        raise ValueError("Please choose an option from the list above.")

# Close the connection
db.close()
