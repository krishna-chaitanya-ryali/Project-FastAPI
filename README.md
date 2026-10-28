# Project-FastAPI
# GitHub Token
# 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
# part 14 completed
# To download PostgreSQL on Windows, you can use the Windows Package Manager (winget) to search for and install PostgreSQL. Here are the commands you can use:
# winget search PostgreSQL
# winget install --id PostgreSQL.PostgreSQL.18 --exact


To login to the database using psql, you can use the following command in your terminal or command prompt:

(.venv) PS C:\AI-Journey\Projects\FASTAPI_BLOG> & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -p 5432 -U bloguser -d blog    
Password for user bloguser: 

psql (18.6)
WARNING: Console code page (437) differs from Windows code page (1252)
         8-bit characters might not work correctly. See psql reference
         page "Notes for Windows users" for details.
Type "help" for help.

blog=> 

(.venv) PS C:\AI-Journey\Projects\FASTAPI_BLOG> alembic init -t async alembic 

.\.venv\Scripts\alembic.exe revision --autogenerate -m "initial schema"


