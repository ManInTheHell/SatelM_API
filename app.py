"""
This is a sample code demonstrating a customer service system using SQLAlchemy and Spyne.
It defines a Customer and Service model, along with operations to add customers, create services,
and retrieve customer information.

Author: Mohammad Hosein
Date: 1402/03/28
"""

from spyne import Application, rpc, ServiceBase, Unicode
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from sqlalchemy import create_engine, ForeignKey, Column, Integer, String, Date, Text
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# Setup SQLite
DB_NAME = 'ShatelMobile.db'
DB_URL = 'sqlite:///{}'.format(DB_NAME)

# setup SQLAlchemy
engine = create_engine(DB_URL, echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()


class Customer(Base):
    """
        Represents a customer in the system.
    """
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    family = Column(String)
    father_name = Column(String)
    national_id = Column(String)
    shenasname_id = Column(String)
    birth_date = Column(Date)
    address = Column(Text)
    services_count = Column(Integer, default=0)
    services = relationship("Service", back_populates="customer")


class Service(Base):
    """
        Represents a service associated with a customer.
    """
    __tablename__ = 'services'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    phone_number = Column(String)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    customer = relationship("Customer", back_populates="services")


# create tables
Base.metadata.create_all(engine)


# define service class
class CustomerService(ServiceBase):
    """
       Service class providing customer-related operations.
   """
    @rpc(Unicode, Unicode, Unicode, Unicode, Unicode, Unicode, Unicode, _returns=Unicode)
    def add_customer(ctx, name, family, father_name, national_id, shenasname_id, birth_date, address):
        """
            Adds a new customer to the system.

            :param name: (str) The customer's name.
            :param family: (str) The customer's family name.
            :param father_name: (str) The customer's father's name.
            :param national_id: (str) The customer's national ID.
            :param shenasname_id: (str) The customer's Shenasname ID.
            :param birth_date: (str) The customer's birth date in the format 'YYYY-MM-DD'.
            :param address : (str) The customer's address.

            :return: (str) A success message if the customer is added successfully, or an error message otherwise.
        """
        session = Session()
        birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
        today = datetime.now().date()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

        if age < 18:
            session.close()
            return "Age must be 18 or older to register as a customer."

        customer = Customer(name=name, family=family, father_name=father_name, national_id=national_id,
                            shenasname_id=shenasname_id, birth_date=birth_date, address=address)
        session.add(customer)
        session.commit()
        session.close()
        return "Customer added successfully."

    @rpc(Unicode, _returns=Unicode)
    def get_customer(ctx, customer_id):
        """
            Retrieves customer information based on the provided customer ID.

            :param customer_id: (str) The ID of the customer to retrieve information for.

            :return: (str) The customer information if found, or a message indicating the customer was not found.
        """
        session = Session()
        customer = session.query(Customer).filter_by(id=customer_id).first()
        result = "\n"
        if customer:
            result += "id: {}\nName: {}\nfamily: {}\nfather_name: {}\nnational_id: {}\nshenasname_id: {}\n" \
                      "birth_date: {}\nAddress: {}\n\n".format(customer.id, customer.name, customer.family,
                                                               customer.father_name, customer.national_id,
                                                               customer.shenasname_id, customer.birth_date,
                                                               customer.address)
            session.close()
            return result
        else:
            return "Customer not found."

    @rpc(Unicode, Unicode, Unicode, _returns=Unicode)
    def create_service(ctx, customer_id, phone_number, service_name):
        """
            Creates a new service for the specified customer.

            :param customer_id: (str) The ID of the customer to create the service for.
            :param phone_number: (str) The phone number associated with the service.
            :param service_name: (str) The name of the service.

            :return: (str) A success message if the service is created successfully, or an error message otherwise.
        """
        session = Session()

        # customer existence checking
        customer = session.query(Customer).filter_by(id=customer_id).first()
        if not customer:
            session.close()
            return "Customer not found."

        # limit checking
        if customer.services_count >= 10:
            session.close()
            return "Maximum number of services reached for this customer."

        # create new service
        service = Service(name=service_name, phone_number=phone_number, customer_id=customer_id)
        session.add(service)

        # customer service count updating
        customer.services_count += 1

        session.commit()
        session.close()
        return "Service created successfully."

    @rpc(Unicode, _returns=Unicode)
    def get_customer_services(ctx, customer_id):
        """
            Retrieves the list of services associated with the specified customer.

            :param customer_id: (str) The ID of the customer to retrieve services for.

            :return: (str) The list of services for the customer if found,
             or a message indicating the customer was not found.
        """
        session = Session()
        customer = session.query(Customer).filter_by(id=customer_id).first()
        result = "\n"
        if customer:
            result += "Customer ID: {}\nName: {}\nFamily: {}\n\nServices:\n".format(customer.id, customer.name,
                                                                                    customer.family)
            for service in customer.services:
                result += "Service ID: {}\nName: {}\nPhone Number: {}\n\n".format(service.id, service.name,
                                                                                  service.phone_number)
            session.close()
            return result
        else:
            return "Customer not found."


# define api app
application = Application([CustomerService],
                          tns='my_namespace',
                          in_protocol=Soap11(validator='lxml'),
                          out_protocol=Soap11())

# setup server and run
if __name__ == '__main__':
    wsgi_application = WsgiApplication(application)
    from wsgiref.simple_server import make_server
    server = make_server('localhost', 8000, wsgi_application)
    server.serve_forever()
