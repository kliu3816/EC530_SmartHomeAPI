from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from fastapi import FastAPI,Depends, HTTPException
from sqlalchemy.exc import IntegrityError

app = FastAPI()

DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind =engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    name = Column(String, index=True)
    email = Column(String, primary_key=True, unique=True, index=True)

    houses = relationship("House", back_populates="user", cascade="all, delete")


class House(Base):
    __tablename__ = "houses"
    address = Column(String, primary_key=True)
    user_email = Column(String, ForeignKey("users.email"), nullable=False)

    user = relationship("User", back_populates="houses")
    rooms = relationship("Room", back_populates = "house")

class Room(Base):
    __tablename__ = "rooms"
    name = Column(String, primary_key=True, index=True)
    house_adrs = Column(String, ForeignKey("houses.address"), nullable=False)

    house = relationship("House", back_populates="rooms")
    devices = relationship("Device", back_populates = "room", cascade="all, delete")


class Device(Base):
    __tablename__ = "devices"
    name = Column(String, primary_key=True, nullable=False)
    room_name = Column(String, ForeignKey("rooms.name"), nullable=False)

    room = relationship("Room", back_populates="devices")



Base.metadata.drop_all(bind=engine)  # Drops existing tables
Base.metadata.create_all(bind=engine)  # Recreates them with the correct schema

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class UserCreate(BaseModel):
    name: str
    email: str

class HouseCreate(BaseModel):
    address: str
    user_email: str


class RoomCreate(BaseModel):
    name: str
    house_adrs: str
  
class DeviceCreate(BaseModel):
    name: str
    room_name: str
 


class UserResponse(BaseModel):
    name:str
    email:str
    class Config:
        orm_model = True

class HouseResponse(HouseCreate):
    class Config:
        orm_model = True

class RoomResponse(BaseModel):
    name: str
    house_adrs: str
    
    class Config:
        orm_mode = True

class HouseResponse(BaseModel):
    address: str
    user_email: str
    
    class Config:
        orm_model = True

#-------------------------------User Endpoints--------------------------#
#Create new user
@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(name=user.name, email=user.email)
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already exists")
    
    db.refresh(new_user)
    return new_user

#Paste all created users
@app.get("/users/", response_model=list[UserResponse])
def read_users(skip: int = 0, Limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(User).offset(skip).limit(Limit).all()
    return users

#Find specfic user based on user_email
@app.get("/users/{user_email}", response_model=UserResponse)
def read_user(user_email: str, db:Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_email).first()

    if user is None:
        raise HTTPException(status_code=404, detail = "user not found")
    return user

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

#Update database
@app.put("/users/{user_email}", response_model=UserResponse)
def update_user(user_email: str, user: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent email update since it's the primary key
    if user.email and user.email != user_email:
        raise HTTPException(status_code=400, detail="Cannot update email address")
    
    if user.name:
        db_user.name = user.name

    db.commit()
    db.refresh(db_user)
    return db_user

#delete a record
@app.delete("/user/{user_email}", response_model=UserResponse)
def delete_user(user_email: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user_email).first()

    if db_user is None:
        raise HTTPException(status_code=404, detail="user not found")
    
    db.delete(db_user)
    db.commit()
    return db_user

#------------------------------House Endpoints---------------------------#
@app.post("/houses/", response_model=HouseResponse)
def create_house(house: HouseCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == house.user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db_house = House(address=house.address, user_email=house.user_email)
    db.add(db_house)
    db.commit()
    db.refresh(db_house)
    return db_house

@app.get("/houses/", response_model=HouseResponse)
def read_houses(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    houses = db.query(House).offset(skip).limit(limit).all()
    return houses

@app.get("/houses/{house_address}", response_model=HouseResponse)
def read_house(house_address: str, db: Session = Depends(get_db)):
    house = db.query(House).filter(House.address == house_address).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")
    return house

#Update address of the house
@app.put("/houses/{house_address}", response_model=HouseResponse)
def update_house(house_address: str, house: HouseCreate, db: Session = Depends(get_db)):
    db_house = db.query(House).filter(House.address == house_address).first()
    if not db_house:
        raise HTTPException(status_code=404, detail="House not found")

    # Check if new address exists
    if house.address != house_address:
        existing = db.query(House).filter(House.address == house.address).first()
        if existing:
            raise HTTPException(status_code=400, detail="Address already exists")

    db_house.address = house.address
    db.commit()
    db.refresh(db_house)
    return db_house

@app.delete("/houses/{house_address}", response_model=HouseCreate)
def delete_house(house_address: str, db: Session = Depends(get_db)):
    house = db.query(House).filter(House.address == house_address).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")

    db.delete(house)
    db.commit()
    return house

#----------------------------Room Endpoints-----------------------------#
@app.post("/rooms/", response_model=RoomResponse)
def create_room(room: RoomCreate, db: Session = Depends(get_db)):
    house = db.query(House).filter(House.address == room.house_adrs).first()
    if not house:
        raise HTTPException(status_code=404, detail="House not found")

    db_room = Room(name=room.name, house_adrs=room.house_adrs)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room

@app.get("/rooms/", response_model=list[RoomResponse])
def read_rooms(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    rooms = db.query(Room).offset(skip).limit(limit).all()
    return rooms

@app.get("/rooms/{room_name}", response_model=RoomResponse)
def read_room(room_name: str, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.name == room_name).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room

#Update which house a room belongs to
@app.put("/rooms/{room_name}", response_model=RoomCreate)
def update_room(room_name: str, room: RoomCreate, db: Session = Depends(get_db)):
    db_room = db.query(Room).filter(Room.name == room_name).first()

    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")

    if room.house_adrs:
        house = db.query(House).filter(House.address == room.house_adrs).first()
        if not house:
            raise HTTPException(status_code=404, detail="House not found")
        db_room.house_adrs = room.house_adrs  # Change house reference

    db.commit()
    db.refresh(db_room)
    return db_room

@app.delete("/rooms/{room_name}", response_model=RoomCreate)
def delete_room(room_name: str, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.name == room_name).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    db.delete(room)
    db.commit()
    return room

#--------------------------------Device Endpoints----------------------#
@app.post("/devices/", response_model=DeviceCreate)
def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.name == device.room_name).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    db_device = Device(name=device.name, room_name=device.room_name)
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device

@app.get("/devices/", response_model=list[DeviceCreate])
def read_devices(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    devices = db.query(Device).offset(skip).limit(limit).all()
    return devices

@app.get("/devices/{device_name}", response_model=DeviceCreate)
def read_device(device_name: str, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.name == device_name).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

#Update a device to a different room
@app.put("/devices/{device_name}", response_model=DeviceCreate)
def update_device(device_name: str, device: DeviceCreate, db: Session = Depends(get_db)):
    db_device = db.query(Device).filter(Device.name == device_name).first()

    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")

    if device.room_name:
        room = db.query(Room).filter(Room.name == device.room_name).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        db_device.room_name = device.room_name  # Change room reference

    db.commit()
    db.refresh(db_device)
    return db_device

@app.delete("/devices/{device_name}", response_model=DeviceCreate)
def delete_device(device_name: str, db: Session = Depends(get_db)):
    device = db.query(Device).filter(Device.name == device_name).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    db.delete(device)
    db.commit()
    return device