# import sqlalchemy
# from sqlalchemy import Column, Integer, String
# from sqlalchemy import Table
# from sqlalchemy.ext.declarative import declarative_base

# Base = declarative_base()

# class MyTable(Base):
#     __tablename__ = 'myTable'
#     time_id = Column(String(), primary_key=True)
#     customer_id = Column(String())
#     inventory_id = Column(String())

# def toJSON(self):   
#     json = {
#         "time_id":self.alert_id,
#         "customer_id":self.customer_id,
#         "inventory_id":self.inventory_id,
#     }
#     return json