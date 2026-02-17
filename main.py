from fastapi import FastAPI,UploadFile,HTTPException,File,BackgroundTasks,Depends
from utils import create_file,process_file,get_all_documents,get_document_by_id
from fastapi.responses import JSONResponse
from database import *
import datetime
from models import create_table,Collection, Status,Documents
from sqlalchemy.orm import Session
import os
import pathlib
from typing import List


app=FastAPI()
files_dir = "files/"
os.makedirs(files_dir, exist_ok=True)

create_table()

@app.get("/")
def root():
    return {"message":"Fastapi is working"}

def get_db():
    db=Sessionlocal()
    try:
        yield db
    finally:
        db.close()


# create file
@app.post('/uploadfile/')
def upload_data(background_tasks:BackgroundTasks,files: List[UploadFile],collection_name: str = File(...),db:Session=Depends(get_db)):
    try:
        exists_collection = db.query(Collection).filter(Collection.name == collection_name).first()

        if exists_collection:
            raise HTTPException(status_code=400,detail="Collection name already exists")
        
        collection=Collection(name=collection_name, create = datetime.datetime.now(), update = datetime.datetime.now(), status=Status.Inprogress, documents =len(files))
        db.add(collection)
        db.commit() 
        db.refresh(collection)

        for file in files:
            # file_path=file.filename
             # Save uploaded file
            file_path = os.path.join(files_dir, file.filename)
            print(f"DEBUG: Saving file at {file_path}")

            with open(file_path, "wb") as f:
                f.write(file.file.read())

            print("DEBUG: File saved successfully")

            if file_path.endswith(".pdf"):
                print("file_name",files)

                doc=pathlib.Path(file_path).suffix
                print("DOC:", doc)
                background_tasks.add_task(create_file,file_path,collection_name)

                documents=Documents(name=file_path,create=datetime.datetime.now(),update=datetime.datetime.now(),status=Status.Inprogress,document_type=doc,collection_id= collection.collection_id)
                db.add(documents)
                db.commit()
                db.refresh(documents)
        
                #collection.status = Status.Completed
                #documents.status=Status.Completed 
                #db.commit()
            else:
                raise HTTPException(400, detail="Unsupported File Type")

        return JSONResponse(content={"message":f"File Upload Successfully","collections_id": collection.collection_id,"collections_name": collection_name})
    
    except Exception as e:
        # collection.status = Status.Failed
        # documents.status=Status.Failed
        # db.commit() 

        raise HTTPException(status_code=404,detail=str(e))

@app.get("/collections/{collection_name}/documents")
def list_documents(collection_name: str):
    
    documents = get_all_documents(collection_name)

    return {
        "collection_name": collection_name,
        "total_documents": len(documents),
        "documents": documents
    }
     

@app.get("/collections/{collection_name}/documents/{document_id}")
def get_document(collection_name: str, document_id: str):

    document = get_document_by_id(collection_name, document_id)

    return {
        "collection_name": collection_name,
        "document": document
    }


@app.post('/query/')
def query_data(query:str,collection_name: str):
    try:
        query_response=process_file(query,collection_name)
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))    
    return query_response


@app.get('/result')
def get_instance(collection_id:int,db:Session=Depends(get_db)):
    try:
        collection = db.query(Collection).filter( Collection.collection_id == collection_id ).first() 
        if not collection:
            return {"message": "Collection not found"} 
        return { "collection_id": collection.collection_id, "collection_name": collection.name, "status": collection.status.value, "no_of_documents": collection.documents }
    
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))




