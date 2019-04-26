import os, csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine('postgres://teykjyfsvqcamv:f982273d2058ffd4fccc4eba198ca702ac67ee7f42ff26f11c8653ba41f5cbcd@ec2-54-197-239-115.compute-1.amazonaws.com:5432/d1rcjij2006gm5')
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv", "r")
    reader = csv.reader(f)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                    {"isbn": isbn, "title": title, "author": author, "year": year})
        print(f"Added book {title} from {author} write in {year}")
    db.commit()

if __name__ == "__main__":
    main()