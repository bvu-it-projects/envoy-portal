from typing import Union
from flask import request, url_for
from sqlalchemy import Integer, String, DateTime, Boolean, Column, ForeignKey, Date, UniqueConstraint, delete, event, DDL
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func

from src.main import db_session, db

import datetime
from .admission_constants import *


class AdmissionType(db.Model):
    __tablename__ = 'AdmissionType'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    name = Column(String(ADMISSION_NAME_LENGTH), nullable=False, unique=True)

    @staticmethod
    def is_admission_type_name_already_exists(self, name: str):
        """
        Check whether the given :name is already in the DB.
        """
        return db_session.query(AdmissionType).filter(AdmissionType.name == name).first() is not None


class Admission(db.Model):
    __tablename__ = 'Admission'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    # slug = Column(String(ADMISSION_SLUG_LENGTH), unique=True, index=True, nullable=False)

    name = Column(String(ADMISSION_NAME_LENGTH), nullable=False, unique=True)
    description = Column(String(length=ADMISSION_DESCRIPTION_LENGTH), nullable=False)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    finished = Column(Boolean, default=False, nullable=False)
    rose = Column(Integer, nullable=False)

    type_id = Column(Integer, ForeignKey("AdmissionType.id"), nullable=False)
    type = relationship("AdmissionType", backref="admissions")

    def __init__(self, name: str, type_id: int, description: str, rose: int, start_date: datetime.date, end_date: datetime.date):
        self.name = name
        # self.slug = slug if slug else self.get_slug_by_name()
        self.description = description
        self.start_date = start_date
        self.end_date = end_date
        self.type_id = type_id
        self.rose = rose

    @staticmethod
    def get_available_items_to_new_registration():
        """
        Getting list of all available Admissions to clients to register.
        """
        return db_session.query(Admission).filter(
        Admission.finished == False, 
        Admission.end_date >= datetime.datetime.now()
        ).all()

    @staticmethod
    def finished_items(self):
        """
        Getting all finished admissions.
        """
        return db_session.query(Admission).filter(Admission.finished == True).all()
    
    @staticmethod
    def running_items(self):
        """
        Getting all closed but not finished admissions (on hold for handling bonus for envoy...).
        """
        return db_session.query(Admission).filter(Admission.finished == False).all()

    def registered_by_user(self, user_id: int) -> bool:
        presenter = db_session.query(AdmissionPresenter).filter(
            AdmissionPresenter.user_id == user_id,
            AdmissionPresenter.admission_id == self.id,
        ).first() != None
        return presenter

    @property
    def students(self):
        applied_students = db_session.query(StudentPresenter)\
        .join(
            AdmissionPresenter, StudentPresenter.presenter_id == AdmissionPresenter.id, isouter=True,
        )\
        .filter(AdmissionPresenter.id != None, AdmissionPresenter.admission_id == self.id)
        return applied_students.all()
    
    


class AdmissionPresenter(db.Model):
    __tablename__ = 'AdmissionPresenter'
    __table_args__ = {'extend_existing': True}

    """
    H???c vi??n kh??ng ???????c ????ng k?? 2 l???n v??o m???t Chi???n d???ch tuy???n sinh.
    ??? m???i chi???n d???ch tuy???n sinh, h???c vi??n ch??? ???????c ????ng k?? v???i m???t ?????i s???.
    """
    id = Column(Integer, primary_key=True)
    # m?? gi???i thi???u ?????i s??? thu???c chi???n d???ch tuy???n sinh --> g???i cho EMS/h???c vi??n nh???p ??? xettuyen
    referral_code = Column(String(ADMISSION_REFERRAL_CODE_LENGTH), unique=True)

    user = relationship("User", backref='joined_admissions')
    user_id = Column(Integer, ForeignKey("User.id"), nullable=False)

    admission = relationship("Admission", backref='joined_users')
    admission_id = Column(Integer, ForeignKey('Admission.id'), nullable=False)

    # extra fields
    user_joined_time = Column(DateTime) # th???i ??i???m ?????i s??? tham gia chi???n d???ch (khi ?????i s??? ????? xu???t tham gia chi???n d???ch, ch??? admin ch???p thu???n xong r???i c???p nh???t)

    __table_args__ = (
        UniqueConstraint(admission_id, user_id),
        {'extend_existing': True, },
    )

    @property
    def referral_shareable_link(self):
        server_name = request.headers.get('host')
        return server_name + url_for('mock.student_apply', referral_code=self.referral_code);


class StudentPresenter(db.Model):
    __tablename__ = 'StudentPresenter'
    __table_args__ = {'extend_existing': True}

    # student = relationship("Student", backref='joined_admissions')
    student_id = Column(String(ADMISSION_STUDENT_ID_LENGTH), primary_key=True)
    student_joined_time = Column(DateTime, nullable=False, default=datetime.datetime.now()) # th???i ??i???m h???c vi??n ????ng k?? ch???n ?????i s??? theo chi???n d???ch (m?? gi???i thi???u)
    student_paid_time = Column(DateTime) # th???i ??i???m h???c vi??n nh???p h???c th??nh c??ng

    presenter = relationship("AdmissionPresenter", backref=db.backref('applied_students', cascade='all,delete'))
    presenter_id = Column(Integer, ForeignKey('AdmissionPresenter.id'), primary_key=True)
