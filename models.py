from database import engine
from sqlalchemy.orm import Mapped,DeclarativeBase
from sqlalchemy.orm import mapped_column,relationship
from sqlalchemy import Integer,String,DateTime,Enum,ForeignKey
from sqlalchemy.sql import func
import enum
from sqlalchemy.ext.mutable import MutableList

# declarative base class
class Base(DeclarativeBase):
    pass

class Status(enum.Enum):
    Inprogress='inprogress'
    Completed='completed'
    Failed='failed'


class Collection(Base):
    __tablename__='collection'

    collection_id:Mapped[int]=mapped_column(Integer,primary_key=True)
    name:Mapped[str]=mapped_column(String,nullable=False)
    create:Mapped[DateTime]=mapped_column(DateTime(timezone=True), server_default=func.now())
    update:Mapped[DateTime]=mapped_column(DateTime(timezone=True), onupdate=func.now())
    status:Mapped[Status]=mapped_column(Enum(Status),default=Status.Inprogress)
    documents:Mapped[int]=mapped_column(Integer)
    documents_ref:Mapped[MutableList['Documents']]=relationship('Documents',back_populates="collection_ref", cascade="all,delete")

    # def __repr__(self):
    #     return f"<instance_id:{self.collection_id} name:{self.name} create:{self.create} update:{self.update} status:{self.status}  documents:{self.documents}>"
    
class Documents(Base):
    __tablename__='documents'

    documents_id:Mapped[int]=mapped_column(Integer,primary_key=True)
    name:Mapped[str]=mapped_column(String,nullable=False)
    create:Mapped[DateTime]=mapped_column(DateTime(timezone=True), server_default=func.now())
    update:Mapped[DateTime]=mapped_column(DateTime(timezone=True), onupdate=func.now())
    status:Mapped[Enum]=mapped_column(Enum(Status),default=Status.Inprogress)
    document_type:Mapped[str]=mapped_column(String)
    collection_id:Mapped[int]=mapped_column(ForeignKey('collection.collection_id'))
    collection_ref:Mapped[MutableList[Collection]]=relationship('Collection',back_populates="documents_ref")

def create_table():
    Base.metadata.create_all(engine)